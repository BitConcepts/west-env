"""Unit tests for west_env.backend."""

# SPDX-License-Identifier: Apache-2.0

import sys
import unittest
from unittest.mock import patch
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from west_env.backend import (
    BackendProbe,
    detect_all,
    select,
    doctor_lines,
    ContainerBackend,
    _probe_podman_native,
    _probe_docker_native,
    _probe_podman_machine_hyperv,
    _probe_docker_desktop,
    _probe_podman_machine,
    _probe_docker_machine,
    _binary_version,
)


class TestBinaryVersion(unittest.TestCase):
    def test_returns_none_when_binary_not_in_path(self):
        with patch("west_env.backend.which", return_value=None):
            self.assertIsNone(_binary_version("notaprogram"))

    def test_returns_first_line_of_output(self):
        with patch("west_env.backend.which", return_value="/usr/bin/docker"), \
             patch("west_env.backend.subprocess.check_output",
                   return_value="Docker version 24.0.0\nsome other line\n"):
            result = _binary_version("docker")
            self.assertEqual(result, "Docker version 24.0.0")


class TestLinuxProbes(unittest.TestCase):
    def test_podman_native_available(self):
        with patch("west_env.backend._binary_version", return_value="podman version 4.9.0"):
            probe = _probe_podman_native()
        self.assertTrue(probe.available)
        self.assertEqual(probe.name, "podman-native")
        self.assertEqual(probe.version, "podman version 4.9.0")

    def test_podman_native_not_available(self):
        with patch("west_env.backend._binary_version", return_value=None):
            probe = _probe_podman_native()
        self.assertFalse(probe.available)
        self.assertIn("not found", probe.notes[0])

    def test_docker_native_available(self):
        with patch("west_env.backend._binary_version", return_value="Docker version 24.0.0"):
            probe = _probe_docker_native()
        self.assertTrue(probe.available)
        self.assertEqual(probe.name, "docker-native")

    def test_docker_native_not_available(self):
        with patch("west_env.backend._binary_version", return_value=None):
            probe = _probe_docker_native()
        self.assertFalse(probe.available)


class TestWindowsProbes(unittest.TestCase):
    def test_podman_machine_hyperv_not_available_no_podman(self):
        with patch("west_env.backend._binary_version", return_value=None):
            probe = _probe_podman_machine_hyperv()
        self.assertFalse(probe.available)
        self.assertIn("podman not found", probe.notes[0])

    def test_podman_machine_hyperv_not_available_no_hyperv(self):
        with patch("west_env.backend._binary_version", return_value="podman 4.x"), \
             patch("west_env.backend._hyperv_enabled", return_value=False):
            probe = _probe_podman_machine_hyperv()
        self.assertFalse(probe.available)
        self.assertTrue(any("Hyper-V" in n for n in probe.notes))

    def test_podman_machine_hyperv_not_available_no_machine(self):
        with patch("west_env.backend._binary_version", return_value="podman 4.x"), \
             patch("west_env.backend._hyperv_enabled", return_value=True), \
             patch("west_env.backend._podman_machine_running", return_value=False):
            probe = _probe_podman_machine_hyperv()
        self.assertFalse(probe.available)
        self.assertTrue(any("podman machine" in n for n in probe.notes))

    def test_podman_machine_hyperv_available(self):
        with patch("west_env.backend._binary_version", return_value="podman 4.x"), \
             patch("west_env.backend._hyperv_enabled", return_value=True), \
             patch("west_env.backend._podman_machine_running", return_value=True):
            probe = _probe_podman_machine_hyperv()
        self.assertTrue(probe.available)
        self.assertEqual(probe.name, "podman-machine-hyperv")

    def test_docker_desktop_no_docker(self):
        with patch("west_env.backend._binary_version", return_value=None):
            probe = _probe_docker_desktop()
        self.assertFalse(probe.available)

    def test_docker_desktop_not_wsl2(self):
        with patch("west_env.backend._binary_version", return_value="Docker 24"), \
             patch("west_env.backend._docker_uses_wsl2", return_value=False):
            probe = _probe_docker_desktop()
        self.assertFalse(probe.available)

    def test_docker_desktop_available_issues_warning(self):
        with patch("west_env.backend._binary_version", return_value="Docker 24"), \
             patch("west_env.backend._docker_uses_wsl2", return_value=True):
            probe = _probe_docker_desktop()
        self.assertTrue(probe.available)
        self.assertIsNotNone(probe.warning)
        self.assertIn("performance", probe.warning)


class TestMacOSProbes(unittest.TestCase):
    def test_podman_machine_requires_running_machine(self):
        with patch("west_env.backend._binary_version", return_value="podman 4.x"), \
             patch("west_env.backend._podman_machine_running", return_value=False):
            probe = _probe_podman_machine()
        self.assertFalse(probe.available)

    def test_podman_machine_available(self):
        with patch("west_env.backend._binary_version", return_value="podman 4.x"), \
             patch("west_env.backend._podman_machine_running", return_value=True):
            probe = _probe_podman_machine()
        self.assertTrue(probe.available)

    def test_docker_machine_available(self):
        with patch("west_env.backend._binary_version", return_value="Docker 24"):
            probe = _probe_docker_machine()
        self.assertTrue(probe.available)


class TestDetectAll(unittest.TestCase):
    def test_linux_probes_podman_and_docker(self):
        with patch("west_env.backend._probe_podman_native",
                   return_value=BackendProbe("podman-native", True, "v4")), \
             patch("west_env.backend._probe_docker_native",
                   return_value=BackendProbe("docker-native", True, "v24")):
            result = detect_all("linux")
        self.assertIn("podman-native", result)
        self.assertIn("docker-native", result)

    def test_win32_probes_hyperv_and_desktop(self):
        with patch("west_env.backend._probe_podman_machine_hyperv",
                   return_value=BackendProbe("podman-machine-hyperv", False)), \
             patch("west_env.backend._probe_docker_desktop",
                   return_value=BackendProbe("docker-desktop", True, "v24")):
            result = detect_all("win32")
        self.assertIn("podman-machine-hyperv", result)
        self.assertIn("docker-desktop", result)

    def test_darwin_probes_podman_machine_and_docker(self):
        with patch("west_env.backend._probe_podman_machine",
                   return_value=BackendProbe("podman-machine", True, "v4")), \
             patch("west_env.backend._probe_docker_machine",
                   return_value=BackendProbe("docker-machine", True, "v24")):
            result = detect_all("darwin")
        self.assertIn("podman-machine", result)
        self.assertIn("docker-machine", result)


class TestSelect(unittest.TestCase):
    def test_auto_linux_prefers_podman_over_docker(self):
        with patch("west_env.backend.detect_all", return_value={
            "podman-native": BackendProbe("podman-native", True, "v4"),
            "docker-native": BackendProbe("docker-native", True, "v24"),
        }):
            name, probe, warns = select("auto", "linux")
        self.assertEqual(name, "podman-native")
        self.assertEqual(warns, [])

    def test_auto_linux_falls_back_to_docker(self):
        with patch("west_env.backend.detect_all", return_value={
            "podman-native": BackendProbe("podman-native", False, notes=["not found"]),
            "docker-native": BackendProbe("docker-native", True, "v24"),
        }):
            name, probe, warns = select("auto", "linux")
        self.assertEqual(name, "docker-native")
        self.assertIn("Skipped podman-native", warns[0])

    def test_auto_raises_when_none_available(self):
        with patch("west_env.backend.detect_all", return_value={
            "podman-native": BackendProbe("podman-native", False, notes=["not found"]),
            "docker-native": BackendProbe("docker-native", False, notes=["not found"]),
        }):
            with self.assertRaises(RuntimeError):
                select("auto", "linux")

    def test_explicit_preferred_returns_it(self):
        probe = BackendProbe("podman-native", True, "v4")
        with patch("west_env.backend.detect_all", return_value={"podman-native": probe}):
            name, p, warns = select("podman-native", "linux")
        self.assertEqual(name, "podman-native")

    def test_explicit_preferred_raises_if_unavailable(self):
        with patch("west_env.backend.detect_all", return_value={
            "podman-native": BackendProbe("podman-native", False, notes=["not found"]),
        }), patch("west_env.backend._probe_podman_native",
                  return_value=BackendProbe("podman-native", False, notes=["not found"])):
            with self.assertRaises(RuntimeError):
                select("podman-native", "linux")

    def test_docker_desktop_warning_propagated(self):
        probe = BackendProbe("docker-desktop", True, "v24",
                             warning="performance warning")
        with patch("west_env.backend.detect_all", return_value={"docker-desktop": probe}), \
             patch("west_env.backend._FALLBACK_CHAIN",
                   {"win32": ["docker-desktop"]}):
            name, p, warns = select("auto", "win32")
        self.assertIn("performance warning", warns)


class TestFallbackChainWin32(unittest.TestCase):
    def test_win32_prefers_podman_hyperv_over_docker_desktop(self):
        with patch("west_env.backend.detect_all", return_value={
            "podman-machine-hyperv": BackendProbe("podman-machine-hyperv", True, "v4"),
            "docker-desktop": BackendProbe("docker-desktop", True, "v24",
                                           warning="perf warn"),
        }):
            name, probe, warns = select("auto", "win32")
        self.assertEqual(name, "podman-machine-hyperv")
        self.assertEqual(warns, [])  # No warning when preferred backend works


class TestContainerBackend(unittest.TestCase):
    def test_binary_name_for_podman_machine_hyperv(self):
        b = ContainerBackend("podman-machine-hyperv")
        self.assertEqual(b.name, "podman")

    def test_binary_name_for_docker_desktop(self):
        b = ContainerBackend("docker-desktop")
        self.assertEqual(b.name, "docker")

    def test_binary_name_for_podman_native(self):
        b = ContainerBackend("podman-native")
        self.assertEqual(b.name, "podman")

    def test_binary_name_for_docker_native(self):
        b = ContainerBackend("docker-native")
        self.assertEqual(b.name, "docker")


class TestDoctorLines(unittest.TestCase):
    def test_doctor_lines_pass_case(self):
        with patch("west_env.backend.select",
                   return_value=("podman-native",
                                 BackendProbe("podman-native", True, "podman v4"),
                                 [])), \
             patch("west_env.backend.detect_all", return_value={
                 "podman-native": BackendProbe("podman-native", True, "podman v4"),
             }):
            lines = doctor_lines("linux")
        self.assertTrue(any("backend selected: podman-native" in line for line in lines))
        self.assertTrue(any("PASS" in line for line in lines))

    def test_doctor_lines_fail_case(self):
        with patch("west_env.backend.select",
                   side_effect=RuntimeError("No backend found")), \
             patch("west_env.backend.detect_all", return_value={}):
            lines = doctor_lines("linux")
        self.assertTrue(any("FAIL" in line for line in lines))


if __name__ == "__main__":
    unittest.main()
