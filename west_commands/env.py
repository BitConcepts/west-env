import sys
from pathlib import Path
import inspect
import argparse
import subprocess

# Ensure west-env repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from west.commands import WestCommand
from west.util import west_topdir
from west_env.config import load_config
from west_env.container import run_container, check_container, CONTAINER_WORKDIR
from west_env.util import run_host, check_python, check_west


def validate_workspace_layout():
    workspace_root = Path(west_topdir()).resolve()
    errors = []

    if not (workspace_root / ".west").is_dir():
        errors.append(".west directory not found")

    if not (workspace_root / "modules").is_dir():
        errors.append("modules directory not found")

    # Manifest may live in a subdir — allow that
    if not any(workspace_root.rglob("west.yml")):
        errors.append("west.yml not found anywhere under workspace")

    if errors:
        msg = "\n".join(f"  - {e}" for e in errors)
        raise SystemExit(
            "FATAL: invalid west workspace\n"
            f"Workspace root: {workspace_root}\n"
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

    def _run_container(self, cfg, cmd, interactive=False):
        """
        Wrapper around run_container with stable /work semantics.
        """
        try:
            sig = inspect.signature(run_container)
            kwargs = {}

            if "workdir" in sig.parameters:
                kwargs["workdir"] = CONTAINER_WORKDIR
            if "container_workdir" in sig.parameters:
                kwargs["container_workdir"] = CONTAINER_WORKDIR
            if "mount_target" in sig.parameters:
                kwargs["mount_target"] = CONTAINER_WORKDIR
            if "container_mount" in sig.parameters:
                kwargs["container_mount"] = CONTAINER_WORKDIR
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

    def _doctor_container_workspace(self, cfg):
        """
        Verify the container can see a valid workspace at /work
        """
        workspace = Path(west_topdir()).resolve()

        try:
            subprocess.check_output(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{workspace}:{CONTAINER_WORKDIR}",
                    "-w",
                    CONTAINER_WORKDIR,
                    cfg.image,
                    "sh",
                    "-c",
                    "test -f west.yml && test -d .west && test -d modules",
                ],
                stderr=subprocess.DEVNULL,
            )
            print("[PASS] container workspace visibility")
            return True
        except Exception:
            print("[FAIL] container cannot see a valid workspace at /work")
            print("       expected west.yml, .west/, modules/")
            print("       ensure you run west from the workspace root")
            return False

