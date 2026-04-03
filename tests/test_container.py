"""Unit tests for west_env.container."""

# SPDX-License-Identifier: Apache-2.0

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from west_env.config import EnvConfig
from west_env.container import _container_args, check_container_workspace
from west_env.container import run_container


class ContainerTests(unittest.TestCase):
    def test_container_args_preserve_relative_cwd_and_quote_command(self):
        cfg = EnvConfig(
            {
                "env": {
                    "type": "container",
                    "container": {
                        "engine": "docker",
                        "image": "ghcr.io/example/image:latest",
                    },
                }
            }
        )
        engine = Mock(name="engine")
        engine.name = "docker"

        with tempfile.TemporaryDirectory(prefix="west env ") as tmp:
            workspace = Path(tmp)
            host_cwd = workspace / "app with space"
            host_cwd.mkdir()

            with patch(
                "west_env.container.get_engine",
                return_value=(engine, False),
            ):
                _, _, args = _container_args(
                    cfg,
                    ["west", "build", "../hello world"],
                    workspace=workspace,
                    host_cwd=host_cwd,
                )

        self.assertIn(f"{workspace}:/work", args)
        self.assertEqual(args[args.index("-w") + 1], "/work/app with space")
        self.assertIn(
            "exec west build '../hello world'",
            args[-1],
        )

    def test_container_args_use_workspace_root_when_cwd_is_outside_workspace(self):
        cfg = EnvConfig(
            {
                "env": {
                    "type": "container",
                    "container": {
                        "engine": "docker",
                        "image": "ghcr.io/example/image:latest",
                    },
                }
            }
        )
        engine = Mock(name="engine")
        engine.name = "docker"

        with tempfile.TemporaryDirectory() as workspace_tmp, tempfile.TemporaryDirectory() as outside_tmp:
            workspace = Path(workspace_tmp)
            outside_cwd = Path(outside_tmp)

            with patch(
                "west_env.container.get_engine",
                return_value=(engine, False),
            ):
                _, _, args = _container_args(
                    cfg,
                    ["west", "build"],
                    workspace=workspace,
                    host_cwd=outside_cwd,
                )

        self.assertEqual(args[args.index("-w") + 1], "/work")

    def test_run_container_uses_detected_engine(self):
        cfg = EnvConfig(
            {
                "env": {
                    "type": "container",
                    "container": {
                        "engine": "podman",
                        "image": "ghcr.io/example/image:latest",
                    },
                }
            }
        )
        engine = Mock(name="engine")
        engine.name = "podman"

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            with patch(
                "west_env.container.get_engine",
                return_value=(engine, False),
            ), patch(
                "west_env.container._west_topdir",
                return_value=str(workspace),
            ), patch(
                "west_env.container.Path.cwd",
                return_value=workspace,
            ):
                run_container(cfg, ["west", "build"])

        engine.run.assert_called_once()

    def test_check_container_workspace_uses_selected_engine(self):
        cfg = EnvConfig(
            {
                "env": {
                    "type": "container",
                    "container": {
                        "engine": "podman",
                        "image": "ghcr.io/example/image:latest",
                    },
                }
            }
        )
        engine = Mock(name="engine")
        engine.name = "podman"

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            with patch(
                "west_env.container.get_engine",
                return_value=(engine, False),
            ), patch("subprocess.check_output") as check_output:
                check_container_workspace(cfg, workspace, "workspace/west.yml")

        invoked = check_output.call_args.args[0]
        self.assertEqual(invoked[0], "podman")

    def test_check_container_workspace_uses_docker_when_configured(self):
        cfg = EnvConfig(
            {
                "env": {
                    "type": "container",
                    "container": {
                        "engine": "docker",
                        "image": "ghcr.io/example/image:latest",
                    },
                }
            }
        )
        engine = Mock(name="engine")
        engine.name = "docker"

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            with patch(
                "west_env.container.get_engine",
                return_value=(engine, False),
            ), patch("subprocess.check_output") as check_output:
                check_container_workspace(cfg, workspace, "west.yml")

        invoked = check_output.call_args.args[0]
        self.assertEqual(invoked[0], "docker")


if __name__ == "__main__":
    unittest.main()
