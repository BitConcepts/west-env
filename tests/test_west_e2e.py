"""End-to-end west CLI tests for west-env."""

# SPDX-License-Identifier: Apache-2.0

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

BASE_TEST_IMAGE = os.environ.get(
    "WEST_ENV_WEST_CLI_BASE_IMAGE",
    "python:3.12-alpine",
)
TEST_IMAGE = os.environ.get(
    "WEST_ENV_WEST_CLI_IMAGE",
    "west-env-test-west-cli:latest",
)


def docker_available():
    try:
        subprocess.check_output(
            ["docker", "--version"],
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:  # noqa
        return False


def ensure_west_cli_test_image():
    if os.environ.get("WEST_ENV_WEST_CLI_IMAGE"):
        return

    with tempfile.TemporaryDirectory(prefix="west-env-west-cli-image-") as tmp:
        dockerfile = Path(tmp) / "Dockerfile"
        dockerfile.write_text(
            textwrap.dedent(
                f"""\
                FROM {BASE_TEST_IMAGE}
                RUN apk add --no-cache git
                RUN python -m pip install --no-cache-dir west PyYAML
                ENTRYPOINT []
                CMD ["sh"]
                """
            ),
            encoding="utf-8",
        )
        subprocess.check_call(
            ["docker", "build", "-t", TEST_IMAGE, tmp],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def make_workspace(root, env_yaml):
    root = Path(root)
    shutil.copytree(REPO_ROOT / "west_commands", root / "west_commands")
    shutil.copytree(REPO_ROOT / "west_env", root / "west_env")

    (root / ".west").mkdir()
    (root / ".west" / "config").write_text(
        "[manifest]\npath = .\nfile = west.yml\n",
        encoding="utf-8",
    )

    (root / "west.yml").write_text(
        textwrap.dedent(
            """\
            manifest:
              self:
                path: .
                west-commands: local-west-commands.yml
            """
        ),
        encoding="utf-8",
    )

    (root / "local-west-commands.yml").write_text(
        textwrap.dedent(
            """\
            west-commands:
              - file: west_commands/env.py
                commands:
                  - name: env
                    class: EnvCommand
                    help: Manage reproducible build environments
              - file: fake_build.py
                commands:
                  - name: build
                    class: BuildCommand
                    help: Fake build command for tests
            """
        ),
        encoding="utf-8",
    )

    (root / "fake_build.py").write_text(
        textwrap.dedent(
            """\
            # SPDX-License-Identifier: Apache-2.0
            import json
            import os
            from pathlib import Path
            from west.commands import WestCommand

            class BuildCommand(WestCommand):
                def __init__(self):
                    super().__init__(
                        "build",
                        "Fake build command for tests",
                        "Fake build command for tests",
                        accepts_unknown_args=True,
                    )

                def do_add_parser(self, parser_adder):
                    parser = parser_adder.add_parser(
                        self.name,
                        description=self.description,
                    )
                    parser.add_argument("-b", "--board")
                    parser.add_argument("source_dir", nargs="?")
                    return parser

                def do_run(self, args, unknown):
                    output_path = Path(os.getcwd()) / "west-build-output.json"
                    payload = {
                        "cwd": os.getcwd(),
                        "board": args.board,
                        "source_dir": args.source_dir,
                        "unknown": unknown,
                    }
                    output_path.write_text(json.dumps(payload), encoding="utf-8")
            """
        ),
        encoding="utf-8",
    )

    (root / "west-env.yml").write_text(env_yaml, encoding="utf-8")
    (root / "app").mkdir()


def run_west(args, cwd, extra_env=None):
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["west"] + args,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )


class WestE2ETests(unittest.TestCase):
    def test_west_env_doctor_native_end_to_end(self):
        with tempfile.TemporaryDirectory(prefix="west-env-e2e-") as tmp:
            root = Path(tmp)
            make_workspace(
                root,
                "env:\n  type: native\n",
            )

            result = run_west(["env", "doctor"], cwd=root)

            self.assertIn("Environment looks good", result.stdout)
            self.assertIn("container execution disabled", result.stdout)

    def test_west_env_build_native_end_to_end(self):
        with tempfile.TemporaryDirectory(prefix="west-env-e2e-") as tmp:
            root = Path(tmp)
            output_path = root / "west-build-output.json"
            make_workspace(
                root,
                "env:\n  type: native\n",
            )

            run_west(
                ["env", "build", "-b", "native_sim", "app", "--flag", "value"],
                cwd=root,
            )

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["board"], "native_sim")
            self.assertEqual(payload["source_dir"], "app")
            self.assertEqual(payload["unknown"], ["--flag", "value"])
            self.assertEqual(Path(payload["cwd"]).resolve(), root.resolve())

    @unittest.skipUnless(docker_available(), "Docker is required for container e2e test")
    def test_west_env_build_container_end_to_end(self):
        ensure_west_cli_test_image()

        with tempfile.TemporaryDirectory(prefix="west-env-e2e-") as tmp:
            root = Path(tmp)
            output_path = root / "west-build-output.json"
            make_workspace(
                root,
                textwrap.dedent(
                    f"""\
                    env:
                      type: container
                      container:
                        engine: docker
                        image: {TEST_IMAGE}
                    """
                ),
            )

            run_west(
                ["env", "build", "-b", "container_sim", "app", "--flag", "value"],
                cwd=root,
            )

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["board"], "container_sim")
            self.assertEqual(payload["source_dir"], "app")
            self.assertEqual(payload["unknown"], ["--flag", "value"])
            self.assertEqual(payload["cwd"], "/work")


if __name__ == "__main__":
    unittest.main()
