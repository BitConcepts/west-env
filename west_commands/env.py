# SPDX-License-Identifier: Apache-2.0

import json
import platform as _platform_mod
import sys
import time
from pathlib import Path
import inspect
import argparse
import configparser

# Ensure west-env repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from west.commands import WestCommand
from west_env.config import load_config
from west_env.container import check_container, check_container_workspace
from west_env.container import run_container
from west_env.util import check_python, check_west, host_shell_command
from west_env.util import run_host


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


def validate_workspace_layout(topdir):
    topdir = Path(topdir).resolve()
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
            "Manage reproducible build environments for west workspaces.",
            accepts_unknown_args=True,
        )

    def do_add_parser(self, parser_adder):
        parser = parser_adder.add_parser(
            self.name,
            add_help=True,
            allow_abbrev=False,
            help="Run west commands in native or container/VM environments",
            description=self.description,
        )

        parser.add_argument(
            "action",
            choices=[
                "init",
                "build",
                "shell",
                "doctor",
                "sync",
                "flash",
                "debug",
                "cache",
                "benchmark",
                "generate-tasks",
            ],
            help="Environment action to perform",
        )

        # Legacy flag (kept for backward compat)
        parser.add_argument(
            "--container",
            action="store_true",
            help="Force container execution (legacy; use --backend instead)",
        )
        parser.add_argument(
            "--backend",
            default=None,
            help="Override backend (e.g. docker-native, podman-native, auto)",
        )
        parser.add_argument(
            "--mode",
            default=None,
            dest="workspace_mode",
            choices=["sync", "copy", "tmpfs", "bind"],
            help="Override workspace mode",
        )
        parser.add_argument(
            "--back",
            action="store_true",
            help="(sync only) Sync artifacts from container back to host",
        )
        parser.add_argument(
            "--ccache",
            action="store_true",
            help="(cache reset) Clear ccache only",
        )
        parser.add_argument(
            "--modules",
            action="store_true",
            help="(cache reset) Clear modules cache only",
        )

        parser.add_argument(
            "args",
            nargs=argparse.REMAINDER,
            help="Arguments passed through to the underlying west command",
        )

        return parser

    def do_run(self, args, unknown_args):
        cfg = load_config(self.topdir)
        use_container = args.container or cfg.env_type == "container"
        passthrough = [a for a in args.args if a not in ("--container",)]
        passthrough.extend(a for a in unknown_args if a not in ("--container",))

        action = args.action

        if action == "init":
            print("Initializing environment...")
            if use_container:
                validate_workspace_layout(self.topdir)
                self._run_container(cfg, ["true"])
            else:
                print("Native environment selected")

        elif action == "build":
            cmd = ["west", "build"] + passthrough
            if use_container:
                validate_workspace_layout(self.topdir)
                self._run_container(cfg, cmd)
            else:
                run_host(cmd)

        elif action == "shell":
            if use_container:
                validate_workspace_layout(self.topdir)
                self._run_container(cfg, ["/bin/sh"], interactive=True)
            else:
                run_host(host_shell_command())

        elif action == "doctor":
            self._doctor(cfg, use_container)

        elif action == "sync":
            self._sync(cfg, args.workspace_mode or cfg.workspace_mode, back=getattr(args, "back", False))

        elif action == "flash":
            self._flash(cfg, passthrough)

        elif action == "debug":
            self._debug(cfg, passthrough)

        elif action == "cache":
            sub = passthrough[0] if passthrough else "stats"
            self._cache(cfg, sub, args)

        elif action == "benchmark":
            self._benchmark(cfg, passthrough)

        elif action == "generate-tasks":
            self._generate_tasks(cfg)

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

        # Extended: backend detection
        try:
            from west_env import backend as _backend

            print()
            for line in _backend.doctor_lines():
                print(line)
        except Exception:
            pass

        # Extended: credential strategy
        try:
            from west_env import credentials as _creds

            print()
            for line in _creds.doctor_lines(cfg.git_credential_helper):
                print(line)
        except Exception:
            pass

        # Extended: J-Link
        try:
            from west_env import flash as _flash

            print()
            for line in _flash.doctor_lines(cfg.jlink_mode):
                print(line)
        except Exception:
            pass

        # Legacy container checks (kept for test compatibility)
        if use_container:
            ok &= check_container(cfg)
            ok &= self._doctor_container_workspace(cfg)
        else:
            print("\n[INFO] container execution disabled")

        print()
        if ok:
            print("Environment looks good [OK]")
        else:
            print("One or more checks failed [FAIL]")

    def _doctor_container_workspace(self, cfg):
        topdir = Path(self.topdir).resolve()
        mpath, mfile = _read_west_manifest_location(topdir)
        manifest_rel = f"{mpath.rstrip('/')}/{mfile}".lstrip("./")
        try:
            check_container_workspace(cfg, topdir, manifest_rel)
            print("[PASS] container workspace visibility")
            return True
        except Exception:  # noqa
            print("[FAIL] container cannot see a valid workspace at /work")
            print("       expected .west/ and configured manifest file")
            print(f"       manifest: {manifest_rel}")
            print("       ensure you run west from the workspace root")
            return False

    def _sync(self, cfg, mode, back=False):
        from west_env.sync import WorkspaceSync, _workspace_slug

        topdir = Path(self.topdir).resolve()
        ws = WorkspaceSync(workspace_mode=mode)
        engine_name = self._engine_name(cfg)
        volume = f"west-env-ws-{_workspace_slug(topdir)}"

        if back:
            print(f"Syncing artifacts back from container (mode={mode})...")
            artifacts_dir = topdir / "artifacts"
            ws.sync_from_volume(engine_name, volume, artifacts_dir)
            print(f"[OK] artifacts written to {artifacts_dir}")
        else:
            print(f"Syncing source to container (mode={mode})...")
            ws.warn_if_needed()
            if mode in ("sync", "copy", "tmpfs"):
                ws.sync_to_volume(topdir, engine_name, volume)
                print(f"[OK] source synced to volume {volume}")
            else:
                print("[INFO] bind mode: no sync needed; host path mounted directly")

    def _flash(self, cfg, passthrough):
        from west_env.flash import FlashManager

        if cfg.jlink_mode == "none":
            raise SystemExit("Flash disabled (jlink.mode = none)")
        artifact = passthrough[0] if passthrough else None
        if not artifact:
            raise SystemExit("Usage: west env flash <artifact.hex>")
        fm = FlashManager(jlink_mode=cfg.jlink_mode)
        fm.flash(Path(artifact), extra_args=passthrough[1:] or None)

    def _debug(self, cfg, passthrough):
        from west_env.flash import FlashManager

        fm = FlashManager(jlink_mode=cfg.jlink_mode)
        device = passthrough[0] if passthrough else "auto"
        print(f"Starting J-Link GDB server (device={device}, port={fm.gdb_port})...")
        proc = fm.start_gdb_server(device)
        print(f"[OK] J-Link GDB server started (PID {proc.pid})")
        print("     Connect GDB inside container: target remote host.docker.internal:2331")
        try:
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()

    def _cache(self, cfg, sub_action, args):
        from west_env.cache import CacheManager

        cm = CacheManager(self._engine_name(cfg))
        if sub_action == "stats":
            cm.print_stats()
        elif sub_action == "reset":
            if getattr(args, "ccache", False):
                cm.reset("ccache")
            elif getattr(args, "modules", False):
                cm.reset("modules")
            else:
                cm.reset("all")
        else:
            raise SystemExit(f"Unknown cache sub-action: {sub_action!r}. Use 'stats' or 'reset'.")

    def _benchmark(self, cfg, passthrough):
        topdir = Path(self.topdir).resolve()
        board = "native_sim"
        sample = None
        for i, arg in enumerate(passthrough):
            if arg in ("-b", "--board") and i + 1 < len(passthrough):
                board = passthrough[i + 1]
            elif not arg.startswith("-"):
                sample = arg

        print(f"Benchmarking: board={board}, mode={cfg.workspace_mode}")
        start = time.monotonic()
        cmd = ["west", "build", "-b", board] + ([sample] if sample else [])
        try:
            if cfg.env_type == "container":
                self._run_container(cfg, cmd)
            else:
                run_host(cmd)
        except Exception as exc:
            print(f"[FAIL] build failed: {exc}")
            return
        elapsed = time.monotonic() - start

        result = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "machine": _platform_mod.node(),
            "os": _platform_mod.platform(),
            "python": _platform_mod.python_version(),
            "board": board,
            "sample": sample,
            "backend": cfg.backend,
            "workspace_mode": cfg.workspace_mode,
            "elapsed_seconds": round(elapsed, 2),
        }
        bench_dir = topdir / "docs" / "benchmarks"
        bench_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
        out = bench_dir / f"benchmark-{stamp}.json"
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\n[OK] {elapsed:.1f}s — results: {out}")

    def _generate_tasks(self, cfg):
        topdir = Path(self.topdir).resolve()
        from west_env.platform import generate_wrappers
        from west_env.vscode import write_tasks

        scripts_dir = topdir / "scripts"
        created = generate_wrappers(scripts_dir)
        for p in created:
            print(f"[OK] wrapper: {p.relative_to(topdir)}")
        tasks_path = write_tasks(topdir)
        print(f"[OK] VSCode tasks: {tasks_path.relative_to(topdir)}")
        print(f"     Platform: {'PowerShell (.ps1)' if sys.platform == 'win32' else 'shell (.sh)'}")
        print("     No Remote WSL extension required.")

    def _engine_name(self, cfg) -> str:
        """Return underlying binary name (docker or podman) for the config."""
        backend = getattr(cfg, "backend", "auto") or "auto"
        if "podman" in backend:
            return "podman"
        if "docker" in backend:
            return "docker"
        engine = getattr(cfg, "engine", "docker") or "docker"
        return "docker" if engine == "auto" else engine
