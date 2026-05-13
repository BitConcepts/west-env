"""Unit tests for west_env.buildcheck — stale build directory detection."""

# SPDX-License-Identifier: Apache-2.0

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from west_env.buildcheck import (
    CONTAINER_WORK_PREFIX,
    _read_cmake_source_dir,
    clean_build_dir,
    detect_stale_build,
)


def _write_cmake_cache(build_dir: Path, source_dir: str) -> None:
    """Write a minimal CMakeCache.txt with the given source directory."""
    cache = build_dir / "CMakeCache.txt"
    cache.write_text(
        f"# CMake generated cache\nCMAKE_SOURCE_DIR:STATIC={source_dir}\nCMAKE_BUILD_TYPE:STRING=\n",
        encoding="utf-8",
    )


class TestReadCmakeSourceDir(unittest.TestCase):
    def test_returns_none_when_no_build_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp) / "build"
            self.assertIsNone(_read_cmake_source_dir(build))

    def test_returns_none_when_no_cmake_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp) / "build"
            build.mkdir()
            self.assertIsNone(_read_cmake_source_dir(build))

    def test_reads_cmake_source_dir_from_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp) / "build"
            build.mkdir()
            _write_cmake_cache(build, "/home/user/workspace")
            result = _read_cmake_source_dir(build)
            self.assertEqual(result, "/home/user/workspace")

    def test_reads_container_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp) / "build"
            build.mkdir()
            _write_cmake_cache(build, "/work")
            result = _read_cmake_source_dir(build)
            self.assertEqual(result, "/work")

    def test_reads_subdirectory_container_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp) / "build"
            build.mkdir()
            _write_cmake_cache(build, "/work/modules/my-app")
            result = _read_cmake_source_dir(build)
            self.assertEqual(result, "/work/modules/my-app")

    def test_returns_none_for_empty_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp) / "build"
            build.mkdir()
            (build / "CMakeCache.txt").write_text("# empty cache\n", encoding="utf-8")
            self.assertIsNone(_read_cmake_source_dir(build))


class TestDetectStaleBuild(unittest.TestCase):
    """Tests for the main stale-build detection logic."""

    def test_no_warning_when_build_dir_does_not_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp) / "build"
            # Native mode, no build dir yet
            self.assertIsNone(detect_stale_build(build, use_container=False))
            # Container mode, no build dir yet
            self.assertIsNone(detect_stale_build(build, use_container=True))

    def test_no_warning_when_build_has_no_cmake_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp) / "build"
            build.mkdir()
            self.assertIsNone(detect_stale_build(build, use_container=False))
            self.assertIsNone(detect_stale_build(build, use_container=True))

    def test_no_warning_native_build_used_natively(self):
        """Same mode: native build used natively — no stale."""
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp) / "build"
            build.mkdir()
            _write_cmake_cache(build, "/home/user/workspace")
            self.assertIsNone(detect_stale_build(build, use_container=False))

    def test_no_warning_container_build_used_in_container(self):
        """Same mode: container build used in container — no stale."""
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp) / "build"
            build.mkdir()
            _write_cmake_cache(build, "/work")
            self.assertIsNone(detect_stale_build(build, use_container=True))

    def test_warning_native_to_container(self):
        """Stale: build was native, now switching to container."""
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp) / "build"
            build.mkdir()
            _write_cmake_cache(build, "/home/user/workspace")
            msg = detect_stale_build(build, use_container=True)
            self.assertIsNotNone(msg)
            self.assertIn("native mode", msg)
            self.assertIn("container mode", msg)
            self.assertIn("--clean", msg)
            self.assertIn("/home/user/workspace", msg)

    def test_warning_container_to_native(self):
        """Stale: build was container, now switching to native."""
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp) / "build"
            build.mkdir()
            _write_cmake_cache(build, "/work")
            msg = detect_stale_build(build, use_container=False)
            self.assertIsNotNone(msg)
            self.assertIn("container mode", msg)
            self.assertIn("native mode", msg)
            self.assertIn("--clean", msg)
            self.assertIn("/work", msg)

    def test_warning_contains_warn_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp) / "build"
            build.mkdir()
            _write_cmake_cache(build, "/work/app")
            msg = detect_stale_build(build, use_container=False)
            self.assertTrue(msg.startswith("[WARN]"))

    def test_container_subdir_path_detected_as_container_build(self):
        """A source path of /work/some/subdir should count as container build."""
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp) / "build"
            build.mkdir()
            _write_cmake_cache(build, "/work/modules/zephyr/samples/hello_world")
            # Used natively — should warn
            msg = detect_stale_build(build, use_container=False)
            self.assertIsNotNone(msg)
            # Used in container — should not warn
            self.assertIsNone(detect_stale_build(build, use_container=True))

    def test_windows_host_path_detected_as_native(self):
        """A Windows-style host path should count as native build."""
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp) / "build"
            build.mkdir()
            _write_cmake_cache(build, "C:/Users/dev/workspace")
            # Used in container — should warn
            msg = detect_stale_build(build, use_container=True)
            self.assertIsNotNone(msg)
            # Used natively — should not warn
            self.assertIsNone(detect_stale_build(build, use_container=False))


class TestCleanBuildDir(unittest.TestCase):
    def test_removes_build_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp) / "build"
            build.mkdir()
            (build / "CMakeCache.txt").write_text("cache", encoding="utf-8")
            self.assertTrue(build.exists())
            clean_build_dir(build)
            self.assertFalse(build.exists())

    def test_no_error_when_build_dir_does_not_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp) / "nonexistent"
            # Should not raise
            clean_build_dir(build)

    def test_removes_nested_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp) / "build"
            nested = build / "zephyr" / "CMakeFiles"
            nested.mkdir(parents=True)
            (nested / "somefile.o").write_text("obj", encoding="utf-8")
            clean_build_dir(build)
            self.assertFalse(build.exists())


class TestContainerWorkPrefix(unittest.TestCase):
    def test_prefix_is_slash_work(self):
        self.assertEqual(CONTAINER_WORK_PREFIX, "/work")


if __name__ == "__main__":
    unittest.main()
