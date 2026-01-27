import sys
from pathlib import Path
import inspect
import argparse

# Ensure west-env repo root is on sys.path
# (west loads extension modules under a synthetic namespace)
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from west.commands import WestCommand
from west_env.config import load_config
from west_env.container import run_container, check_container
from west_env.util import run_host, check_python, check_west


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

        # Everything after the action is passed through verbatim
        parser.add_argument(
            "args",
            nargs=argparse.REMAINDER,
            help="Arguments passed through to the underlying west command",
        )

        return parser

    def do_run(self, args, unknown_args):
        cfg = load_config()
        use_container = args.container or cfg.env_type == "container"

        passthrough = list(args.args)

        if args.action == "init":
            print("Initializing environment...")
            if use_container:
                # Lightweight container sanity check (pulls image on first use)
                self._run_container(cfg, ["true"])
            else:
                print("Native environment selected")

        elif args.action == "build":
            cmd = ["west", "build"] + passthrough
            if use_container:
                self._run_container(cfg, cmd)
            else:
                run_host(cmd)

        elif args.action == "shell":
            if use_container:
                self._run_container(cfg, ["/bin/bash"], interactive=True)
            else:
                # Native shell (minimal; platform-specific polish can come later)
                run_host(["bash"])

        elif args.action == "doctor":
            self._doctor(cfg, use_container)

    def _run_container(self, cfg, cmd, interactive=False):
        """
        Wrapper around west_env.container.run_container.

        On Windows hosts running Linux containers, Docker requires Linux container
        paths for -w and the container-side mount. We standardize on /work.
        """
        container_workdir = "/work"

        try:
            sig = inspect.signature(run_container)
            kwargs = {}

            # Optional parameters that container.py may support
            if "workdir" in sig.parameters:
                kwargs["workdir"] = container_workdir
            if "container_workdir" in sig.parameters:
                kwargs["container_workdir"] = container_workdir
            if "mount_target" in sig.parameters:
                kwargs["mount_target"] = container_workdir
            if "container_mount" in sig.parameters:
                kwargs["container_mount"] = container_workdir

            if "interactive" in sig.parameters:
                kwargs["interactive"] = interactive
                return run_container(cfg, cmd, **kwargs)

            # Positional fallback
            if len(sig.parameters) >= 3:
                return run_container(cfg, cmd, interactive, **kwargs)

            # Minimal signature fallback
            return run_container(cfg, cmd, **kwargs)

        except TypeError:
            # Legacy fallback; container.py should eventually be updated
            if interactive:
                return run_container(cfg, cmd, interactive=True)
            return run_container(cfg, cmd)

    def _doctor(self, cfg, use_container):
        print("west-env doctor\n")

        ok = True
        ok &= check_python()
        ok &= check_west()

        if use_container:
            ok &= check_container(cfg)
        else:
            print("[INFO] container execution disabled")

        print()
        if ok:
            print("Environment looks good ✔")
        else:
            print("One or more checks failed ✖")
