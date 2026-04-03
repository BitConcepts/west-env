"""End-to-end test for switching between native and container execution."""

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


@unittest.skipUnless(docker_available(), "Docker is required for mode-switch test")
class ModeSwitchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_west_cli_test_image()

    def test_native_then_container_build_in_same_workspace(self):
        """Build natively, then switch config to container and build again.

        Verifies that the workspace works correctly in both modes and that
        switching does not cause cross-contamination.
        """
        with tempfile.TemporaryDirectory(prefix="west-env-switch-") as tmp:
            root = Path(tmp)
            output_path = root / "west-build-output.json"

            # --- Phase 1: native build ---
            make_workspace(root, "env:\n  type: native\n")

            run_west(
                ["env", "build", "-b", "native_sim", "app"],
                cwd=root,
            )

            native_payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(native_payload["board"], "native_sim")
            self.assertEqual(
                Path(native_payload["cwd"]).resolve(),
                root.resolve(),
            )

            # Remove the output so the container build proves it ran fresh
            output_path.unlink()

            # --- Phase 2: switch to container ---
            (root / "west-env.yml").write_text(
                textwrap.dedent(
                    f"""\
                    env:
                      type: container
                      container:
                        engine: docker
                        image: {TEST_IMAGE}
                    """
                ),
                encoding="utf-8",
            )

            run_west(
                ["env", "build", "-b", "container_sim", "app"],
                cwd=root,
            )

            container_payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(container_payload["board"], "container_sim")
            self.assertEqual(container_payload["cwd"], "/work")

    def test_doctor_reports_correctly_after_mode_switch(self):
        """Doctor output changes appropriately when switching modes."""
        with tempfile.TemporaryDirectory(prefix="west-env-switch-") as tmp:
            root = Path(tmp)

            # --- Native mode ---
            make_workspace(root, "env:\n  type: native\n")
            native_result = run_west(["env", "doctor"], cwd=root)
            self.assertIn("container execution disabled", native_result.stdout)
            self.assertIn("Environment looks good", native_result.stdout)

            # --- Switch to container ---
            (root / "west-env.yml").write_text(
                textwrap.dedent(
                    f"""\
                    env:
                      type: container
                      container:
                        engine: docker
                        image: {TEST_IMAGE}
                    """
                ),
                encoding="utf-8",
            )
            container_result = run_west(["env", "doctor"], cwd=root)
            self.assertNotIn("container execution disabled", container_result.stdout)
            self.assertIn("container engine: docker", container_result.stdout)
            self.assertIn("Environment looks good", container_result.stdout)


if __name__ == "__main__":
    unittest.main()
