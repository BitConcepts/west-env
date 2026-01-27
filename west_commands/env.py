import sys
from pathlib import Path

# Ensure west-env repo root is on sys.path
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
            "init | build | shell | doctor"
        )

    def do_add_parser(self, parser_adder):
        parser = parser_adder.add_parser(self.name)
        parser.add_argument(
            "action",
            choices=["init", "build", "shell", "doctor"]
        )
        parser.add_argument(
            "--container",
            action="store_true",
            help="Force container execution"
        )
        return parser

    def do_run(self, args, unknown_args):
        cfg = load_config()
        use_container = args.container or cfg.env_type == "container"

        if args.action == "init":
            print("Initializing environment...")
            if use_container:
                run_container(cfg, ["true"])
            else:
                print("Native environment selected")

        elif args.action == "build":
            cmd = ["west", "build"] + unknown_args
            if use_container:
                run_container(cfg, cmd)
            else:
                run_host(cmd)

        elif args.action == "shell":
            if use_container:
                run_container(cfg, ["/bin/bash"], interactive=True)
            else:
                run_host(["bash"])

        elif args.action == "doctor":
            self._doctor(cfg, use_container)

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
