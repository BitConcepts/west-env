"""Docker-backed integration tests for west_env.container."""

# SPDX-License-Identifier: Apache-2.0

import contextlib
import os
import shutil
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
    "WEST_ENV_DOCKER_TEST_BASE_IMAGE",
    "alpine/git:latest",
)
TEST_IMAGE = os.environ.get(
    "WEST_ENV_DOCKER_TEST_IMAGE",
    "west-env-test-git-shell:latest",
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


def ensure_test_image():
    if os.environ.get("WEST_ENV_DOCKER_TEST_IMAGE"):
        return

    with tempfile.TemporaryDirectory(prefix="west-env-image-") as tmp:
        dockerfile = Path(tmp) / "Dockerfile"
        dockerfile.write_text(
            f"FROM {BASE_TEST_IMAGE}\nENTRYPOINT []\nCMD [\"sh\"]\n",
            encoding="utf-8",
        )
        subprocess.check_call(
            ["docker", "build", "-t", TEST_IMAGE, tmp],
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


def make_cfg(engine):
    return EnvConfig(
        {
            "env": {
                "type": "container",
                "container": {
                    "engine": engine,
                    "image": TEST_IMAGE,
                },
            }
        }
    )


@contextlib.contextmanager
def podman_proxy_path():
    docker_exe = shutil.which("docker")
    if not docker_exe:
        raise RuntimeError("docker executable not found")

    with tempfile.TemporaryDirectory(prefix="west-env-podman-proxy-") as tmp:
        proxy_dir = Path(tmp)
        if os.name == "nt":
            shutil.copyfile(docker_exe, proxy_dir / "podman.exe")
        else:
            os.symlink(docker_exe, proxy_dir / "podman")
        yield f"{proxy_dir}{os.pathsep}{os.environ.get('PATH', '')}"


@unittest.skipUnless(docker_available(), "Docker is required for integration tests")
class DockerIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_test_image()

    def test_check_container_workspace_succeeds_with_real_docker(self):
        with tempfile.TemporaryDirectory(prefix="west-env-docker-") as tmp:
            topdir = Path(tmp)
            make_workspace(topdir, manifest_path="workspace")
            check_container_workspace(
                make_cfg("docker"),
                topdir,
                "workspace/west.yml",
            )

    def test_check_container_workspace_fails_for_missing_manifest(self):
        with tempfile.TemporaryDirectory(prefix="west-env-docker-") as tmp:
            topdir = Path(tmp)
            (topdir / ".west").mkdir()
            (topdir / ".west" / "config").write_text(
                "[manifest]\npath = workspace\nfile = west.yml\n",
                encoding="utf-8",
            )
            (topdir / "workspace").mkdir()

            with self.assertRaises(subprocess.CalledProcessError):
                check_container_workspace(
                    make_cfg("docker"),
                    topdir,
                    "workspace/west.yml",
                )

    def test_run_container_executes_in_relative_subdirectory_with_real_docker(self):
        with tempfile.TemporaryDirectory(prefix="west-env-docker-") as tmp:
            topdir = Path(tmp)
            make_workspace(topdir)
            app_dir = topdir / "app"
            app_dir.mkdir()

            with pushd(app_dir), patch(
                "west_env.container._west_topdir",
                return_value=str(topdir),
            ):
                run_container(
                    make_cfg("docker"),
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

    def test_run_container_executes_selected_podman_path_via_docker_proxy(self):
        with tempfile.TemporaryDirectory(prefix="west-env-docker-") as tmp:
            topdir = Path(tmp)
            make_workspace(topdir)
            app_dir = topdir / "app"
            app_dir.mkdir()

            with podman_proxy_path() as path_value:
                with pushd(app_dir), patch(
                    "west_env.container._west_topdir",
                    return_value=str(topdir),
                ), patch.dict(
                    os.environ,
                    {"PATH": path_value},
                ):
                    run_container(
                        make_cfg("podman"),
                        [
                            "sh",
                            "-c",
                            "pwd > podman-runtime-pwd.txt && test -d ../.west && test -f ../west.yml",
                        ],
                    )

            self.assertEqual(
                (app_dir / "podman-runtime-pwd.txt").read_text(encoding="utf-8").strip(),
                "/work/app",
            )


if __name__ == "__main__":
    unittest.main()
