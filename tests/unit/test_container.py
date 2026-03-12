# SPDX-License-Identifier: Apache-2.0
"""Tests for west_env.container.

Regression coverage
-------------------
* safe.directory must use the ``'*'`` wildcard — NOT a hardcoded path such as
  ``/work/zephyr``.  A hardcoded path breaks any workspace that stores the
  Zephyr checkout at a different location (e.g. ``deps/zephyr``) because a
  ``zephyr/`` directory at the repo root may already be taken by a Zephyr
  module integration directory containing ``zephyr/module.yml``.

Additional coverage
-------------------
* The west workspace is mounted at ``CONTAINER_WORKDIR`` (``/work``).
* The container working directory (``-w``) matches the host cwd relative to
  the workspace, falling back to ``/work`` when cwd is outside the workspace.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from west_env.container import CONTAINER_WORKDIR


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cfg(image: str = "test/image:latest", engine: str = "docker") -> MagicMock:
    cfg = MagicMock()
    cfg.image = image
    cfg.engine = engine
    return cfg


def _call_run_container(workspace: Path, cwd: Path, cfg: MagicMock | None = None):
    """Invoke run_container with filesystem calls fully mocked.

    Returns the list of arguments passed to ``engine.run()``.
    """
    if cfg is None:
        cfg = _make_cfg()

    mock_engine = MagicMock()

    with (
        patch("west_env.container.west_topdir", return_value=str(workspace)),
        patch("west_env.container.Path.cwd", return_value=cwd),
        patch("west_env.container.get_engine", return_value=(mock_engine, False)),
    ):
        from west_env.container import run_container

        run_container(cfg, ["west", "build", "-b", "native_sim", "."])

    assert mock_engine.run.called, "engine.run() was never invoked"
    # engine.run() is called as engine.run(args_list)
    return mock_engine.run.call_args[0][0]


# ---------------------------------------------------------------------------
# Regression: safe.directory wildcard
# ---------------------------------------------------------------------------


class TestSafeDirectoryWildcard:
    def test_wildcard_present(self, tmp_path):
        """The shell -c command must contain safe.directory '*'."""
        ws = tmp_path / "workspace"
        ws.mkdir()
        args = _call_run_container(ws, cwd=ws)
        shell_cmd = args[-1]  # "sh -c <cmd>" is the last positional arg
        assert "safe.directory '*'" in shell_cmd, (
            f"Expected wildcard safe.directory, got shell cmd:\n  {shell_cmd}"
        )

    def test_no_hardcoded_zephyr_path(self, tmp_path):
        """Regression: /work/zephyr must not appear in the safe.directory command."""
        ws = tmp_path / "workspace"
        ws.mkdir()
        args = _call_run_container(ws, cwd=ws)
        shell_cmd = args[-1]
        assert "/work/zephyr" not in shell_cmd, (
            "Regression: hardcoded /work/zephyr found — use '*' instead"
        )

    def test_shell_also_executes_original_command(self, tmp_path):
        """The git config preamble must be followed by the actual build command."""
        ws = tmp_path / "workspace"
        ws.mkdir()
        args = _call_run_container(ws, cwd=ws)
        shell_cmd = args[-1]
        assert "west build" in shell_cmd


# ---------------------------------------------------------------------------
# Workspace bind-mount
# ---------------------------------------------------------------------------


class TestWorkspaceMount:
    def test_workspace_mounted_at_container_workdir(self, tmp_path):
        ws = tmp_path / "workspace"
        ws.mkdir()
        args = _call_run_container(ws, cwd=ws)
        vol_idx = args.index("-v") + 1
        mount = args[vol_idx]
        host_part, container_part = mount.split(":", 1)
        assert container_part == CONTAINER_WORKDIR, (
            f"Expected mount target {CONTAINER_WORKDIR}, got {container_part}"
        )
        assert Path(host_part).resolve() == ws.resolve()

    def test_container_workdir_constant_is_work(self):
        assert CONTAINER_WORKDIR == "/work"


# ---------------------------------------------------------------------------
# Container working directory (-w flag)
# ---------------------------------------------------------------------------


class TestContainerWorkingDirectory:
    def test_cwd_at_workspace_root(self, tmp_path):
        ws = tmp_path / "workspace"
        ws.mkdir()
        args = _call_run_container(ws, cwd=ws)
        wd_idx = args.index("-w") + 1
        assert args[wd_idx] == CONTAINER_WORKDIR

    def test_cwd_inside_workspace_subdir(self, tmp_path):
        ws = tmp_path / "workspace"
        subdir = ws / "app" / "src"
        subdir.mkdir(parents=True)
        args = _call_run_container(ws, cwd=subdir)
        wd_idx = args.index("-w") + 1
        assert args[wd_idx] == f"{CONTAINER_WORKDIR}/app/src"

    def test_cwd_outside_workspace_falls_back_to_workdir(self, tmp_path):
        ws = tmp_path / "workspace"
        ws.mkdir()
        outside = tmp_path / "other"
        outside.mkdir()
        args = _call_run_container(ws, cwd=outside)
        wd_idx = args.index("-w") + 1
        assert args[wd_idx] == CONTAINER_WORKDIR


# ---------------------------------------------------------------------------
# PYTHONPATH injection
# ---------------------------------------------------------------------------


class TestPythonPathInjection:
    def test_pythonpath_set(self, tmp_path):
        ws = tmp_path / "workspace"
        ws.mkdir()
        args = _call_run_container(ws, cwd=ws)
        env_idx = args.index("-e") + 1
        assert "PYTHONPATH" in args[env_idx]
        assert "/work/modules/west-env" in args[env_idx]
