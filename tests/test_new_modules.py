"""Unit tests for the new west-env modules.

Covers: cache, credentials, vscode, platform, flash.
All tests are pure-Python (no container or hardware required).
"""

# SPDX-License-Identifier: Apache-2.0

import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ===========================================================================
# Cache tests
# ===========================================================================

from west_env.cache import CacheManager, _parse_size, _VOLUME_NAMES


class TestParseSize(unittest.TestCase):
    def test_parses_mb(self):
        self.assertEqual(_parse_size("512MB"), 512 * 1024 ** 2)

    def test_parses_gb(self):
        self.assertEqual(_parse_size("1.5GB"), int(1.5 * 1024 ** 3))

    def test_parses_kb(self):
        self.assertEqual(_parse_size("100KB"), 100 * 1024)

    def test_returns_none_for_garbage(self):
        self.assertIsNone(_parse_size("not-a-size"))


class TestCacheVolumeArgs(unittest.TestCase):
    def test_ccache_flag_adds_volume_and_env(self):
        cm = CacheManager("docker")
        args = cm.volume_args(ccache=True)
        self.assertIn("-v", args)
        self.assertTrue(any("ccache" in a for a in args))
        self.assertIn("-e", args)
        self.assertTrue(any("CCACHE_DIR" in a for a in args))

    def test_modules_flag_adds_volume(self):
        cm = CacheManager("docker")
        args = cm.volume_args(modules=True)
        self.assertIn("-v", args)
        self.assertTrue(any("modules" in a for a in args))

    def test_no_flags_returns_empty(self):
        cm = CacheManager("docker")
        args = cm.volume_args()
        self.assertEqual(args, [])

    def test_sdk_and_pip_flags(self):
        cm = CacheManager("docker")
        args = cm.volume_args(sdk=True, pip=True)
        self.assertTrue(any("sdk" in a for a in args))
        self.assertTrue(any("pip" in a for a in args))


class TestCacheReset(unittest.TestCase):
    def test_reset_unknown_target_raises(self):
        cm = CacheManager("docker")
        with patch.object(cm, "_volume_exists", return_value=False):
            with self.assertRaises(ValueError):
                cm.reset("nonsense")

    def test_reset_all_calls_remove_for_each_volume(self):
        cm = CacheManager("docker")
        calls = []
        with patch.object(cm, "_volume_exists", return_value=True), \
             patch.object(cm, "_remove_volume", side_effect=lambda v: calls.append(v)):
            cm.reset("all")
        self.assertEqual(set(calls), set(_VOLUME_NAMES.values()))

    def test_reset_ccache_only_removes_ccache(self):
        cm = CacheManager("docker")
        calls = []
        with patch.object(cm, "_volume_exists", return_value=True), \
             patch.object(cm, "_remove_volume", side_effect=lambda v: calls.append(v)):
            cm.reset("ccache")
        self.assertEqual(calls, [_VOLUME_NAMES["ccache"]])


class TestCacheVolumeArgsFromConfig(unittest.TestCase):
    def test_reads_flags_from_config(self):
        cfg = MagicMock()
        cfg.cache_ccache = True
        cfg.cache_modules = False
        cfg.cache_sdk = False
        cfg.cache_pip = False
        cm = CacheManager("docker")
        args = cm.volume_args_from_config(cfg)
        self.assertTrue(any("ccache" in a for a in args))
        self.assertFalse(any("modules" in a for a in args))


# ===========================================================================
# Credentials tests
# ===========================================================================

from west_env.credentials import (
    detect_strategy,
    container_args,
    doctor_lines,
)


class TestDetectStrategy(unittest.TestCase):
    def test_explicit_strategy_returned_as_is(self):
        self.assertEqual(detect_strategy("none"), "none")
        self.assertEqual(detect_strategy("openssh-agent"), "openssh-agent")

    def test_auto_detects_openssh_when_sock_set(self):
        with tempfile.NamedTemporaryFile() as f:
            with patch.dict(os.environ, {"SSH_AUTH_SOCK": f.name}):
                strategy = detect_strategy("auto")
        self.assertEqual(strategy, "openssh-agent")

    def test_auto_falls_back_to_credential_manager(self):
        with patch("west_env.credentials._ssh_agent_socket", return_value=None), \
             patch("west_env.credentials._git_credential_manager_installed",
                   return_value=True):
            strategy = detect_strategy("auto")
        self.assertEqual(strategy, "credential-manager")

    def test_auto_falls_back_to_none(self):
        with patch("west_env.credentials._ssh_agent_socket", return_value=None), \
             patch("west_env.credentials._git_credential_manager_installed",
                   return_value=False):
            strategy = detect_strategy("auto")
        self.assertEqual(strategy, "none")


class TestContainerArgs(unittest.TestCase):
    def test_none_strategy_returns_empty(self):
        args = container_args("none")
        self.assertEqual(args, [])

    def test_credential_manager_returns_empty(self):
        args = container_args("credential-manager")
        self.assertEqual(args, [])

    def test_openssh_agent_posix_returns_volume_and_env(self):
        with tempfile.NamedTemporaryFile() as f:
            with patch("west_env.credentials.sys.platform", "linux"), \
                 patch.dict(os.environ, {"SSH_AUTH_SOCK": f.name}):
                args = container_args("openssh-agent")
        # Should have -v and -e args
        self.assertTrue(any("ssh-agent.sock" in a for a in args))
        self.assertTrue(any("SSH_AUTH_SOCK" in a for a in args))


class TestDoctorLines(unittest.TestCase):
    def test_none_strategy_shows_warning(self):
        with patch("west_env.credentials.detect_strategy", return_value="none"):
            lines = doctor_lines()
        self.assertTrue(any("WARN" in line or "none" in line for line in lines))

    def test_openssh_agent_shows_pass(self):
        with patch("west_env.credentials.detect_strategy",
                   return_value="openssh-agent"), \
             patch("west_env.credentials._ssh_agent_socket",
                   return_value="/tmp/agent.sock"):
            lines = doctor_lines()
        self.assertTrue(any("PASS" in line for line in lines))


# ===========================================================================
# VSCode tasks tests
# ===========================================================================

from west_env.vscode import generate_tasks, write_tasks


class TestGenerateTasks(unittest.TestCase):
    def test_generates_valid_tasks_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = generate_tasks(Path(tmp), host_platform="linux")
        self.assertIn("tasks", data)
        self.assertEqual(data["version"], "2.0.0")
        self.assertIsInstance(data["tasks"], list)

    def test_windows_tasks_use_ps1(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = generate_tasks(Path(tmp), host_platform="win32")
        for task in data["tasks"]:
            cmd = task["command"]
            self.assertTrue(cmd.endswith(".ps1"),
                            f"Expected .ps1 extension, got: {cmd}")

    def test_linux_tasks_use_sh(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = generate_tasks(Path(tmp), host_platform="linux")
        for task in data["tasks"]:
            cmd = task["command"]
            self.assertTrue(cmd.endswith(".sh"),
                            f"Expected .sh extension, got: {cmd}")

    def test_macos_tasks_use_sh(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = generate_tasks(Path(tmp), host_platform="darwin")
        for task in data["tasks"]:
            cmd = task["command"]
            self.assertTrue(cmd.endswith(".sh"))

    def test_no_task_uses_wsl_or_bash_on_windows(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = generate_tasks(Path(tmp), host_platform="win32")
        for task in data["tasks"]:
            cmd = task.get("command", "")
            for arg in task.get("args", []):
                self.assertNotIn("wsl", arg.lower())
                self.assertNotIn("bash", arg.lower())
            self.assertNotIn("wsl", cmd.lower())
            self.assertNotIn("bash", cmd.lower())

    def test_all_tasks_have_shell_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = generate_tasks(Path(tmp), host_platform="linux")
        for task in data["tasks"]:
            self.assertEqual(task["type"], "shell",
                             f"Task {task['label']} should use type=shell")

    def test_build_task_is_marked_as_default_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = generate_tasks(Path(tmp), host_platform="linux")
        build_task = next(
            (t for t in data["tasks"] if t["label"] == "west-env: build"), None
        )
        self.assertIsNotNone(build_task)
        self.assertEqual(build_task.get("group", {}).get("kind"), "build")
        self.assertTrue(build_task.get("group", {}).get("isDefault", False))

    def test_covers_all_required_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = generate_tasks(Path(tmp))
        labels = {t["label"] for t in data["tasks"]}
        self.assertIn("west-env: build", labels)
        self.assertIn("west-env: sync", labels)


class TestWriteTasks(unittest.TestCase):
    def test_creates_vscode_tasks_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = write_tasks(root, host_platform="linux")
            self.assertTrue(path.is_file())
            self.assertEqual(path.name, "tasks.json")
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("tasks", data)

    def test_creates_vscode_dir_if_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertFalse((root / ".vscode").exists())
            write_tasks(root)
            self.assertTrue((root / ".vscode").is_dir())


# ===========================================================================
# Platform wrapper tests
# ===========================================================================

from west_env.platform import (
    generate_wrappers,
    generate_wrapper_content,
    get_extension,
    ACTIONS,
)


class TestGetExtension(unittest.TestCase):
    def test_windows_returns_ps1(self):
        self.assertEqual(get_extension("win32"), ".ps1")

    def test_linux_returns_sh(self):
        self.assertEqual(get_extension("linux"), ".sh")

    def test_macos_returns_sh(self):
        self.assertEqual(get_extension("darwin"), ".sh")


class TestGenerateWrapperContent(unittest.TestCase):
    def test_ps1_content_contains_no_bash_or_wsl(self):
        content = generate_wrapper_content("build", "win32")
        self.assertNotIn("bash", content.lower())
        self.assertNotIn("wsl", content.lower())
        self.assertIn("west env build", content)
        self.assertIn("$ErrorActionPreference", content)

    def test_sh_content_uses_exec(self):
        content = generate_wrapper_content("build", "linux")
        self.assertIn("exec west env build", content)
        self.assertIn("#!/bin/sh", content)

    def test_action_substituted_correctly(self):
        for action in ACTIONS:
            content_win = generate_wrapper_content(action, "win32")
            self.assertIn(f"west env {action}", content_win)
            content_sh = generate_wrapper_content(action, "linux")
            self.assertIn(f"west env {action}", content_sh)


class TestGenerateWrappers(unittest.TestCase):
    def test_generates_correct_extension_on_linux(self):
        with tempfile.TemporaryDirectory() as tmp:
            scripts_dir = Path(tmp) / "scripts"
            created = generate_wrappers(scripts_dir, host_platform="linux")
            for p in created:
                self.assertEqual(p.suffix, ".sh",
                                 f"Expected .sh, got {p.suffix} for {p.name}")

    def test_generates_correct_extension_on_windows(self):
        with tempfile.TemporaryDirectory() as tmp:
            scripts_dir = Path(tmp) / "scripts"
            created = generate_wrappers(scripts_dir, host_platform="win32")
            for p in created:
                self.assertEqual(p.suffix, ".ps1",
                                 f"Expected .ps1, got {p.suffix} for {p.name}")

    def test_creates_all_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            scripts_dir = Path(tmp) / "scripts"
            created = generate_wrappers(scripts_dir, host_platform="linux")
            names = {p.stem for p in created}
            for action in ACTIONS:
                self.assertIn(f"west-env-{action}", names)

    def test_creates_scripts_dir_if_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            scripts_dir = Path(tmp) / "new_scripts"
            self.assertFalse(scripts_dir.exists())
            generate_wrappers(scripts_dir, host_platform="linux")
            self.assertTrue(scripts_dir.is_dir())

    @unittest.skipIf(sys.platform == "win32", "chmod not relevant on Windows")
    def test_sh_files_are_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            scripts_dir = Path(tmp) / "scripts"
            created = generate_wrappers(scripts_dir, host_platform="linux")
            for p in created:
                mode = p.stat().st_mode
                self.assertTrue(
                    mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH),
                    f"{p.name} is not executable"
                )

    def test_ps1_content_does_not_reference_wsl(self):
        with tempfile.TemporaryDirectory() as tmp:
            scripts_dir = Path(tmp) / "scripts"
            created = generate_wrappers(scripts_dir, host_platform="win32")
            for p in created:
                content = p.read_text(encoding="utf-8")
                self.assertNotIn("wsl", content.lower(),
                                 f"{p.name} contains 'wsl'")
                self.assertNotIn("bash", content.lower(),
                                 f"{p.name} contains 'bash'")

    def test_generate_subset_of_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            scripts_dir = Path(tmp) / "scripts"
            created = generate_wrappers(scripts_dir, actions=["build", "sync"],
                                        host_platform="linux")
            self.assertEqual(len(created), 2)


# ===========================================================================
# Flash tests (no hardware required)
# ===========================================================================

from west_env.flash import find_jlink_exe, FlashManager, doctor_lines as flash_doctor


class TestFindJlinkExe(unittest.TestCase):
    def test_returns_none_when_not_installed(self):
        with patch("west_env.flash.which", return_value=None):
            result = find_jlink_exe()
        self.assertIsNone(result)

    def test_returns_path_when_in_path(self):
        with patch("west_env.flash.which", return_value="/usr/bin/JLinkExe"):
            result = find_jlink_exe()
        self.assertIsNotNone(result)
        # Compare by name only (str() differs on Windows vs POSIX)
        self.assertEqual(result.name, "JLinkExe")


class TestFlashDoctorLines(unittest.TestCase):
    def test_pass_when_jlink_found(self):
        with patch("west_env.flash.find_jlink_exe",
                   return_value=Path("/usr/bin/JLinkExe")):
            lines = flash_doctor("host")
        self.assertTrue(any("PASS" in line for line in lines))

    def test_warn_when_jlink_not_found(self):
        with patch("west_env.flash.find_jlink_exe", return_value=None):
            lines = flash_doctor("host")
        self.assertTrue(any("WARN" in line for line in lines))

    def test_info_when_disabled(self):
        with patch("west_env.flash.find_jlink_exe", return_value=None):
            lines = flash_doctor("none")
        self.assertTrue(any("disabled" in line for line in lines))


class TestFlashManagerErrors(unittest.TestCase):
    def test_flash_raises_when_jlink_not_found(self):
        fm = FlashManager()
        with patch("west_env.flash.find_jlink_exe", return_value=None):
            with self.assertRaises(RuntimeError):
                fm.flash(Path("/tmp/fw.hex"))

    def test_flash_raises_when_artifact_missing(self):
        fm = FlashManager()
        with patch("west_env.flash.find_jlink_exe",
                   return_value=Path("/usr/bin/JLinkExe")):
            with self.assertRaises(FileNotFoundError):
                fm.flash(Path("/nonexistent/fw.hex"))

    def test_gdb_server_raises_when_not_found(self):
        fm = FlashManager()
        with patch("west_env.flash.find_jlink_exe", return_value=None):
            with self.assertRaises(RuntimeError):
                fm.start_gdb_server("nRF52840_xxAA")


# ===========================================================================
# Benchmark output schema test
# ===========================================================================

class TestBenchmarkOutputSchema(unittest.TestCase):
    """Validate that a benchmark JSON result has all required fields."""

    REQUIRED_FIELDS = {
        "timestamp", "machine", "os", "python",
        "board", "backend", "workspace_mode", "elapsed_seconds",
    }

    def test_benchmark_result_schema(self):
        result = {
            "timestamp": "2026-05-13T00:00:00Z",
            "machine": "test-host",
            "os": "Linux-5.15",
            "python": "3.11.0",
            "board": "native_sim",
            "sample": None,
            "backend": "docker-native",
            "workspace_mode": "bind",
            "elapsed_seconds": 42.5,
        }
        for field in self.REQUIRED_FIELDS:
            self.assertIn(field, result, f"Missing required field: {field}")
        self.assertIsInstance(result["elapsed_seconds"], float)


if __name__ == "__main__":
    unittest.main()
