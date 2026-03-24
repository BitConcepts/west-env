# SPDX-License-Identifier: Apache-2.0

import sys
from pathlib import Path
import argparse
import subprocess
import configparser

# Ensure west-env repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from west.commands import WestCommand
from west.util import west_topdir
from west_env.config import load_config
from west_env.container import (
    run_container,
    run_container_volume,
    extract_artifacts,
    check_container,
    CONTAINER_WORKDIR,
)
from west_env.engine import get_engine
from west_env.util import run_host, check_python, check_west


def _read_west_manifest_location(topdir: Path) -> tuple[str, str]:
    cfg_path = topdir / ".west" / "config"
    cp = configparser.ConfigParser()
    cp.read(cfg_path)
    mpath = cp.get("manifest", "path", fallback=".")
    mfile = cp.get("manifest", "file", fallback="west.yml")
    return mpath, mfile


def validate_workspace_layout():
    topdir = Path(west_topdir()).resolve()
    errors = []

    if not (topdir / ".west").is_dir():
        errors.append(".west directory not found")

    try:
        mpath, mfile = _read_west_manifest_location(topdir)
        manifest = (topdir / mpath / mfile).resolve()
        if not manifest.is_file():
            errors.append(f"manifest not found at {manifest}")
    except Exception as e:
        errors.append(f"failed to read .west/config: {e}")

    if errors:
        msg = "\n".join(f"  - {e}" for e in errors)
        raise SystemExit(
            "FATAL: invalid west workspace\n"
            f"West topdir: {topdir}\n"
            "Problems:\n"
            f"{msg}\n\n"
            "Hint: ensure west init was run and the workspace is intact.\n"
        )


class EnvCommand(WestCommand):
    def __init__(self):
        super().__init__(
            "env",
            "Manage reproducible build environments",
            "init | build | shell | doctor",
        )

    def do_add_parser(self, parser_adder):
        parser = parser_adder.add_parser(
            self.name,
            add_help=True,
            allow_abbrev=False,
            help="Run west commands in native or container environments",
        )

        parser.add_argument(
            "action",
            choices=["init", "build", "shell", "doctor"],
            help="Environment action to perform",
        )

        parser.add_argument(
            "--container",
            action="store_true",
            help="Force container execution",
        )

        parser.add_argument(
            "args",
            nargs=argparse.REMAINDER,
            help="Arguments passed through to the underlying west command",
        )

        return parser

    def do_run(self, args, unknown_args):
        cfg = load_config()
        use_container = args.container or cfg.env_type == "container"
        passthrough = [a for a in args.args if a != "--container"]
        use_volume = use_container and cfg.sync_mode == "volume"

        if args.action == "init":
            print("Initializing environment...")
            if use_container:
                validate_workspace_layout()
                run_container(cfg, ["true"])
            else:
                print("Native environment selected")

        elif args.action == "build":
            build_dir = self._extract_build_dir(passthrough)
            passthrough = self._inject_build_dir(
                cfg, passthrough, use_container
            )
            cmd = ["west", "build"] + passthrough
            if use_volume:
                validate_workspace_layout()
                run_container_volume(cfg, cmd, build_dir=build_dir)
                if build_dir:
                    extract_artifacts(cfg, build_dir)
            elif use_container:
                validate_workspace_layout()
                run_container(cfg, cmd)
            else:
                run_host(cmd)

        elif args.action == "shell":
            if use_volume:
                validate_workspace_layout()
                print("NOTE: volume mode -- host edits require re-sync (exit and re-enter).")
                run_container_volume(cfg, ["/bin/bash"], interactive=True)
            elif use_container:
                validate_workspace_layout()
                run_container(cfg, ["/bin/bash"], interactive=True)
            else:
                run_host(["bash"])

        elif args.action == "doctor":
            self._doctor(cfg, use_container)

    @staticmethod
    def _extract_build_dir(passthrough):
        for i, arg in enumerate(passthrough):
            if arg in ("--build-dir", "-d") and i + 1 < len(passthrough):
                return passthrough[i + 1]
        return None

    @staticmethod
    def _inject_build_dir(cfg, passthrough, use_container):
        if not cfg.build_dir:
            return passthrough
        for arg in passthrough:
            if arg in ("--build-dir", "-d"):
                return passthrough
        if use_container:
            bd = f"{CONTAINER_WORKDIR}/{cfg.build_dir}"
        else:
            bd = str(Path(west_topdir()).resolve() / cfg.build_dir)
        return ["--build-dir", bd] + passthrough

    # ---------------------------------------------------------------
    # doctor
    # ---------------------------------------------------------------
    def _doctor(self, cfg, use_container):
        print("west-env doctor\n")

        ok = True
        ok &= check_python()
        ok &= check_west()

        if use_container:
            engine_ok = check_container(cfg)
            ok &= engine_ok

            if engine_ok:
                ok &= self._doctor_container_workspace(cfg)

                if cfg.sync_mode == "volume":
                    ok &= self._doctor_volume(cfg)

        else:
            print("[INFO] container execution disabled")

        print()
        if ok:
            print("Environment looks good \u2714")
        else:
            print("One or more checks failed \u2716")

    @staticmethod
    def _doctor_volume(cfg):
        try:
            engine, _ = get_engine(cfg.engine)
            subprocess.check_output(
                [engine.name, "volume", "ls"],
                stderr=subprocess.DEVNULL,
            )
            print("[PASS] volume management")
            return True
        except Exception:
            print("[WARN] container engine cannot list volumes")
            print("       ensure the Docker/Podman daemon is running")
            return True  # non-fatal

    @staticmethod
    def _doctor_container_workspace(cfg):
        topdir = Path(west_topdir()).resolve()
        mpath, mfile = _read_west_manifest_location(topdir)
        manifest_rel = f"{mpath.rstrip('/')}/{mfile}".lstrip("./")

        engine, _ = get_engine(cfg.engine)

        # Skip when image not yet pulled
        try:
            subprocess.check_output(
                [engine.name, "image", "inspect", cfg.image],
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            print("[SKIP] container workspace visibility")
            print("       image not present locally; will be checked on first use")
            return True

        try:
            subprocess.check_output(
                [
                    engine.name,
                    "run",
                    "--rm",
                    "-v",
                    f"{topdir}:{CONTAINER_WORKDIR}",
                    "-w",
                    CONTAINER_WORKDIR,
                    cfg.image,
                    "sh",
                    "-c",
                    f"test -d .west && test -f '{manifest_rel}'",
                ],
                stderr=subprocess.DEVNULL,
            )
            print("[PASS] container workspace visibility")
            return True
        except Exception:
            print("[FAIL] container cannot see a valid workspace at /work")
            print("       expected .west/ and configured manifest file")
            print(f"       manifest: {manifest_rel}")
            print("       ensure you run west from the workspace root")
            return False
