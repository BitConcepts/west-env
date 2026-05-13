"""Unit tests for west_env.sync."""

# SPDX-License-Identifier: Apache-2.0

import sys
import tempfile
import unittest
import warnings
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from west_env.sync import (
    DEFAULT_EXCLUDES,
    WorkspaceSync,
    SyncWarning,
    _is_excluded,
    _workspace_slug,
    _copy_tree,
)


class TestIsExcluded(unittest.TestCase):
    def test_excludes_build_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build = root / "build"
            build.mkdir()
            self.assertTrue(_is_excluded(build, root, DEFAULT_EXCLUDES))

    def test_excludes_dotcache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = root / ".cache"
            cache.mkdir()
            self.assertTrue(_is_excluded(cache, root, DEFAULT_EXCLUDES))

    def test_excludes_egg_info(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            egg = root / "mypackage.egg-info"
            egg.mkdir()
            self.assertTrue(_is_excluded(egg, root, DEFAULT_EXCLUDES))

    def test_excludes_nested_pycache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / "src" / "__pycache__"
            nested.mkdir(parents=True)
            self.assertTrue(_is_excluded(nested, root, DEFAULT_EXCLUDES))

    def test_does_not_exclude_regular_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "src"
            src.mkdir()
            self.assertFalse(_is_excluded(src, root, DEFAULT_EXCLUDES))

    def test_custom_pattern_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outdir = root / "my_output"
            outdir.mkdir()
            self.assertTrue(_is_excluded(outdir, root, ["my_output"]))
            self.assertFalse(_is_excluded(outdir, root, ["other_output"]))


class TestCopyTree(unittest.TestCase):
    def test_copies_files_respecting_excludes(self):
        with tempfile.TemporaryDirectory() as src_tmp, tempfile.TemporaryDirectory() as dst_tmp:
            src = Path(src_tmp)
            dst = Path(dst_tmp)

            (src / "app.c").write_text("int main(){}", encoding="utf-8")
            (src / "README.md").write_text("# Readme", encoding="utf-8")
            (src / "build").mkdir()
            (src / "build" / "output.elf").write_text("ELF", encoding="utf-8")

            _copy_tree(src, dst, DEFAULT_EXCLUDES)

            self.assertTrue((dst / "app.c").exists())
            self.assertTrue((dst / "README.md").exists())
            self.assertFalse((dst / "build").exists())

    def test_copies_nested_directory(self):
        with tempfile.TemporaryDirectory() as src_tmp, tempfile.TemporaryDirectory() as dst_tmp:
            src = Path(src_tmp)
            dst = Path(dst_tmp)

            nested = src / "src" / "module"
            nested.mkdir(parents=True)
            (nested / "module.c").write_text("code", encoding="utf-8")

            _copy_tree(src, dst, DEFAULT_EXCLUDES)

            self.assertTrue((dst / "src" / "module" / "module.c").exists())


class TestWorkspaceSlug(unittest.TestCase):
    def test_slug_from_path(self):
        slug = _workspace_slug(Path("/home/user/my-workspace"))
        self.assertEqual(slug, "my-workspace")

    def test_slug_truncated_at_40(self):
        long_name = "a" * 50
        slug = _workspace_slug(Path(f"/home/user/{long_name}"))
        self.assertLessEqual(len(slug), 40)


class TestWorkspaceSyncInit(unittest.TestCase):
    def test_default_mode_is_bind(self):
        ws = WorkspaceSync()
        self.assertEqual(ws.mode, "bind")

    def test_custom_mode(self):
        ws = WorkspaceSync("sync")
        self.assertEqual(ws.mode, "sync")

    def test_custom_excludes(self):
        ws = WorkspaceSync(excludes=["mydir"])
        self.assertIn("mydir", ws.excludes)


class TestVolumeArgs(unittest.TestCase):
    def test_bind_returns_v_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = WorkspaceSync("bind")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SyncWarning)
                args = ws.volume_args(Path(tmp), "docker")
            self.assertIn("-v", args)
            self.assertTrue(any("/work" in a for a in args))
            self.assertNotIn("tmpfs", str(args))

    def test_sync_returns_named_volume(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = WorkspaceSync("sync")
            args = ws.volume_args(Path(tmp), "docker")
            self.assertIn("-v", args)
            # Named volume (not a host path)
            vol_arg = [a for a in args if ":/work" in a][0]
            self.assertFalse(vol_arg.startswith("/"))

    def test_tmpfs_returns_both_volume_and_mount(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = WorkspaceSync("tmpfs")
            args = ws.volume_args(Path(tmp), "docker")
            self.assertIn("--mount", args)
            self.assertTrue(any("tmpfs" in a for a in args))

    def test_unknown_mode_raises(self):
        ws = WorkspaceSync.__new__(WorkspaceSync)
        ws.mode = "invalid"
        ws.excludes = []
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                ws.volume_args(Path(tmp), "docker")


class TestBindWarningOnWindows(unittest.TestCase):
    def test_emits_warning_on_windows(self):
        ws = WorkspaceSync("bind")
        with patch("west_env.sync.sys.platform", "win32"), warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            ws.warn_if_needed()
        sync_warns = [w for w in caught if issubclass(w.category, SyncWarning)]
        self.assertTrue(len(sync_warns) > 0)
        self.assertIn("NTFS", str(sync_warns[0].message))

    def test_no_warning_on_linux(self):
        ws = WorkspaceSync("bind")
        with patch("west_env.sync.sys.platform", "linux"), warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            ws.warn_if_needed()
        sync_warns = [w for w in caught if issubclass(w.category, SyncWarning)]
        self.assertEqual(len(sync_warns), 0)

    def test_no_warning_for_sync_mode_on_windows(self):
        ws = WorkspaceSync("sync")
        with patch("west_env.sync.sys.platform", "win32"), warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            ws.warn_if_needed()
        sync_warns = [w for w in caught if issubclass(w.category, SyncWarning)]
        self.assertEqual(len(sync_warns), 0)


class TestSyncStatus(unittest.TestCase):
    def test_status_returns_correct_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = WorkspaceSync("sync")
            status = ws.status(Path(tmp))
            self.assertEqual(status["mode"], "sync")
            self.assertIn("volume_name", status)
            self.assertIn("excludes", status)

    def test_status_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = WorkspaceSync("bind")
            s1 = ws.status(Path(tmp))
            s2 = ws.status(Path(tmp))
            self.assertEqual(s1, s2)


if __name__ == "__main__":
    unittest.main()
