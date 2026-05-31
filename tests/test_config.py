"""Unit tests for west_env.config."""

# SPDX-License-Identifier: Apache-2.0

import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from west_env.config import find_config_path, load_config


class ConfigTests(unittest.TestCase):
    def test_find_config_path_uses_manifest_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            topdir = Path(tmp)
            manifest_dir = topdir / "workspace"
            manifest_dir.mkdir()
            (topdir / ".west").mkdir()
            (topdir / ".west" / "config").write_text(
                "[manifest]\npath = workspace\nfile = west.yml\n",
                encoding="utf-8",
            )
            (manifest_dir / "west.yml").write_text(
                "manifest:\n  self:\n    path: .\n",
                encoding="utf-8",
            )

            result = find_config_path(topdir)
            expected = manifest_dir / "west-env.yml"
            self.assertEqual(result.resolve(), expected.resolve())

    def test_load_config_reads_manifest_local_file_not_cwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            topdir = Path(tmp)
            manifest_dir = topdir / "workspace"
            nested_dir = topdir / "workspace" / "app"
            nested_dir.mkdir(parents=True)
            (topdir / ".west").mkdir()
            (topdir / ".west" / "config").write_text(
                "[manifest]\npath = workspace\nfile = west.yml\n",
                encoding="utf-8",
            )
            (manifest_dir / "west.yml").write_text(
                "manifest:\n  self:\n    path: .\n",
                encoding="utf-8",
            )
            (manifest_dir / "west-env.yml").write_text(
                textwrap.dedent(
                    """\
                    env:
                      type: container
                      container:
                        engine: podman
                        image: ghcr.io/example/image:latest
                    """
                ),
                encoding="utf-8",
            )
            (nested_dir / "west-env.yml").write_text(
                "env:\n  type: native\n",
                encoding="utf-8",
            )

            prev_cwd = Path.cwd()
            try:
                os.chdir(nested_dir)
                cfg = load_config(topdir)
            finally:
                os.chdir(prev_cwd)

            self.assertEqual(cfg.env_type, "container")
            self.assertEqual(cfg.engine, "podman")
            self.assertEqual(cfg.image, "ghcr.io/example/image:latest")

    def test_load_config_handles_empty_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            topdir = Path(tmp)
            (topdir / ".west").mkdir()
            (topdir / ".west" / "config").write_text(
                "[manifest]\npath = .\nfile = west.yml\n",
                encoding="utf-8",
            )
            (topdir / "west.yml").write_text(
                "manifest:\n  self:\n    path: .\n",
                encoding="utf-8",
            )
            (topdir / "west-env.yml").write_text("", encoding="utf-8")

            cfg = load_config(topdir)

            self.assertEqual(cfg.env_type, "native")
            self.assertEqual(cfg.engine, "docker")
            self.assertIsNone(cfg.image)

    def test_wants_container_legacy_container(self):
        """Legacy env.type=container should set wants_container=True."""
        from west_env.config import EnvConfig

        cfg = EnvConfig({"env": {"type": "container", "container": {"engine": "docker"}}})
        self.assertTrue(cfg.wants_container)

    def test_wants_container_legacy_native(self):
        """Legacy env.type=native with no backend should set wants_container=False."""
        from west_env.config import EnvConfig

        cfg = EnvConfig({"env": {"type": "native"}})
        self.assertFalse(cfg.wants_container)

    def test_wants_container_new_format_explicit_backend(self):
        """New format with explicit backend should set wants_container=True."""
        from west_env.config import EnvConfig

        cfg = EnvConfig({"env": {"backend": "docker-desktop"}})
        self.assertTrue(cfg.wants_container)

    def test_wants_container_new_format_sync_mode(self):
        """New format with workspace_mode=sync implies container execution."""
        from west_env.config import EnvConfig

        cfg = EnvConfig({"env": {"backend": "auto", "workspace_mode": "sync"}})
        self.assertTrue(cfg.wants_container)

    def test_wants_container_new_format_bind_mode_auto(self):
        """New format with workspace_mode=bind and auto backend is native."""
        from west_env.config import EnvConfig

        cfg = EnvConfig({"env": {"backend": "auto", "workspace_mode": "bind"}})
        self.assertFalse(cfg.wants_container)

    def test_wants_container_empty_config(self):
        """Empty config should not want container."""
        from west_env.config import EnvConfig

        cfg = EnvConfig({})
        self.assertFalse(cfg.wants_container)


if __name__ == "__main__":
    unittest.main()
