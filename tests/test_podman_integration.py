"""Podman rootless integration tests for west_env.container.

Mirrors test_docker_integration.py using the Podman engine.
Validates:
  - check_container_workspace with Podman
  - run_container with workspace mounted at /work
  - git safe.directory injection (Zephyr west extensions require it)
  - Container working directory maps correctly to host CWD relative to workspace

All tests are skipped when Podman is not available on the host.
"""

# SPDX-License-Identifier: Apache-2.0

import contextlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from west_env.config import EnvConfig
from west_env.container import check_container_workspace, run_container

BASE_TEST_IMAGE = os.environ.get(
    "WEST_ENV_PODMAN_TEST_BASE_IMAGE",
    "alpine/git:latest",
)
TEST_IMAGE = os.environ.get(
    "WEST_ENV_PODMAN_TEST_IMAGE",
    "west-env-test-git-shell-podman:latest",
)


def podman_available() -> bool:
    try:
        subprocess.check_output(
            ["podman", "--version"],
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:  # noqa
        return False


def ensure_test_image() -> None:
    if os.environ.get("WEST_ENV_PODMAN_TEST_IMAGE"):
        return

    with tempfile.TemporaryDirectory(prefix="west-env-podman-image-") as tmp:
        dockerfile = Path(tmp) / "Dockerfile"
        dockerfile.write_text(
            f'FROM {BASE_TEST_IMAGE}\nENTRYPOINT []\nCMD ["sh"]\n',
            encoding="utf-8",
        )
        subprocess.check_call(
            ["podman", "build", "-t", TEST_IMAGE, tmp],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


@contextlib.contextmanager
def pushd(path):
    prev = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)


def make_workspace(topdir, manifest_path="."):
    topdir = Path(topdir)
    manifest_dir = (topdir / manifest_path).resolve()
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (topdir / ".west").mkdir()
    (topdir / ".west" / "config").write_text(
        f"[manifest]\npath = {manifest_path}\nfile = west.yml\n",
        encoding="utf-8",
    )
    (manifest_dir / "west.yml").write_text(
        "manifest:\n  self:\n    path: .\n",
        encoding="utf-8",
    )
    return manifest_dir


def make_podman_cfg() -> EnvConfig:
    return EnvConfig(
        {
            "env": {
                "type": "container",
                "container": {
                    "engine": "podman",
                    "image": TEST_IMAGE,
                },
            }
        }
    )


@unittest.skipUnless(podman_available(), "Podman is required for Podman integration tests")
class PodmanIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_test_image()

    def test_check_container_workspace_succeeds_with_podman(self):
        """Podman can see the west workspace mounted at /work."""
        with tempfile.TemporaryDirectory(prefix="west-env-podman-", ignore_cleanup_errors=True) as tmp:
            topdir = Path(tmp)
            make_workspace(topdir, manifest_path="workspace")
            check_container_workspace(
                make_podman_cfg(),
                topdir,
                "workspace/west.yml",
            )

    def test_check_container_workspace_fails_for_missing_manifest(self):
        """Podman reports failure when manifest is absent in workspace."""
        with tempfile.TemporaryDirectory(prefix="west-env-podman-", ignore_cleanup_errors=True) as tmp:
            topdir = Path(tmp)
            (topdir / ".west").mkdir()
            (topdir / ".west" / "config").write_text(
                "[manifest]\npath = workspace\nfile = west.yml\n",
                encoding="utf-8",
            )
            (topdir / "workspace").mkdir()
            # west.yml is absent — should fail
            with self.assertRaises(subprocess.CalledProcessError):
                check_container_workspace(
                    make_podman_cfg(),
                    topdir,
                    "workspace/west.yml",
                )

    def test_run_container_executes_in_relative_subdirectory(self):
        """Container working directory tracks host CWD relative to workspace."""
        with tempfile.TemporaryDirectory(prefix="west-env-podman-", ignore_cleanup_errors=True) as tmp:
            topdir = Path(tmp)
            make_workspace(topdir)
            app_dir = topdir / "app"
            app_dir.mkdir()

            with (
                pushd(app_dir),
                patch(
                    "west_env.container._west_topdir",
                    return_value=str(topdir),
                ),
            ):
                run_container(
                    make_podman_cfg(),
                    [
                        "sh",
                        "-c",
                        "pwd > runtime-pwd.txt && test -d ../.west && test -f ../west.yml",
                    ],
                )

            self.assertEqual(
                (app_dir / "runtime-pwd.txt").read_text(encoding="utf-8").strip(),
                "/work/app",
            )

    def test_git_safe_directory_injected(self):
        """git safe.directory '*' is set so git works in the mounted workspace."""
        with tempfile.TemporaryDirectory(prefix="west-env-podman-", ignore_cleanup_errors=True) as tmp:
            topdir = Path(tmp)
            make_workspace(topdir)

            with patch(
                "west_env.container._west_topdir",
                return_value=str(topdir),
            ):
                # Verifies git can run (which requires safe.directory to be set)
                run_container(
                    make_podman_cfg(),
                    ["sh", "-c", "git config --global --get safe.directory > safe-dir.txt"],
                )

            safe_dir_file = topdir / "safe-dir.txt"
            self.assertTrue(safe_dir_file.exists())
            content = safe_dir_file.read_text(encoding="utf-8").strip()
            self.assertIn("*", content)

    def test_pythondontwritebytecode_env_var_is_set(self):
        """PYTHONDONTWRITEBYTECODE=1 is present in the container environment."""
        with tempfile.TemporaryDirectory(prefix="west-env-podman-", ignore_cleanup_errors=True) as tmp:
            topdir = Path(tmp)
            make_workspace(topdir)

            with patch(
                "west_env.container._west_topdir",
                return_value=str(topdir),
            ):
                # Write the env var value to a file inside the workspace
                run_container(
                    make_podman_cfg(),
                    ["sh", "-c", "echo $PYTHONDONTWRITEBYTECODE > env-check.txt"],
                )

            content = (topdir / "env-check.txt").read_text(encoding="utf-8").strip()
            self.assertEqual(
                content,
                "1",
                "PYTHONDONTWRITEBYTECODE was not set to 1 inside the container",
            )


if __name__ == "__main__":
    unittest.main()
