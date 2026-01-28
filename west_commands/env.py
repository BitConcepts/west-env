# SPDX-License-Identifier: Apache-2.0

import sys
from pathlib import Path
import inspect
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
from west_env.container import run_container, check_container, CONTAINER_WORKDIR
from west_env.util import run_host, check_python, check_west


def _read_west_manifest_location(topdir: Path) -> tuple[str, str]:
    """
    Return (manifest_path, manifest_file) from .west/config.

    manifest_path is the directory which contains the manifest file,
    relative to the west topdir (e.g. "workspace").
    manifest_file is typically "west.yml".
    """
    cfg_path = topdir / ".west" / "config"
    cp = configparser.ConfigParser()
    cp.read(cfg_path)

    # West stores this in [manifest] path=..., file=...
    mpath = cp.get("manifest", "path", fallback=".")
    mfile = cp.get("manifest", "file", fallback="west.yml")
    return mpath, mfile


def validate_workspace_layout():
    # NOTE: west_topdir() is the directory containing .west/
    topdir = Path(west_topdir()).resolve()
    errors = []

    if not (topdir / ".west").is_dir():
        errors.append(".west directory not found")

    # Validate the configured manifest file exists (supports manifest in subdir)
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
            "init | build [west build args...] | shell | doctor",
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

        if args.action == "init":
            print("Initializing environment...")
            if use_container:
                validate_workspace_layout()
                self._run_container(cfg, ["true"])
            else:
                print("Native environment selected")

        elif args.action == "build":
            cmd = ["west", "build"] + passthrough
            if use_container:
                validate_workspace_layout()
                self._run_container(cfg, cmd)
            else:
                run_host(cmd)

        elif args.action == "shell":
            if use_container:
                validate_workspace_layout()
                self._run_container(cfg, ["/bin/bash"], interactive=True)
            else:
                run_host(["bash"])

        elif args.action == "doctor":
            self._doctor(cfg, use_container)

    @staticmethod
    def _run_container(cfg, cmd, interactive=False):
        try:
            sig = inspect.signature(run_container)
            kwargs = {}
            if "interactive" in sig.parameters:
                kwargs["interactive"] = interactive
            return run_container(cfg, cmd, **kwargs)
        except TypeError:
            return run_container(cfg, cmd, interactive=interactive)

    def _doctor(self, cfg, use_container):
        print("west-env doctor\n")

        ok = True
        ok &= check_python()
        ok &= check_west()

        if use_container:
            ok &= check_container(cfg)
            ok &= self._doctor_container_workspace(cfg)
        else:
            print("[INFO] container execution disabled")

        print()
        if ok:
            print("Environment looks good ✔")
        else:
            print("One or more checks failed ✖")

    @staticmethod
    def _doctor_container_workspace(cfg):
        """
        Verify the container can see:
          - .west/ at /work (west topdir)
          - the configured manifest file (often workspace/west.yml)
        """
        topdir = Path(west_topdir()).resolve()

        # Compute manifest location from host .west/config, then check in-container
        mpath, mfile = _read_west_manifest_location(topdir)
        manifest_rel = f"{mpath.rstrip('/')}/{mfile}".lstrip("./")

        try:
            subprocess.check_output(
                [
                    "docker",
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
        except Exception:  # noqa
            print("[FAIL] container cannot see a valid workspace at /work")
            print("       expected .west/ and configured manifest file")
            print(f"       manifest: {manifest_rel}")
            print("       ensure you run west from the workspace root")
            return False
