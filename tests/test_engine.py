"""Unit tests for west_env.engine."""

# SPDX-License-Identifier: Apache-2.0

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from west_env.engine import detect_engine


class EngineTests(unittest.TestCase):
    def test_detect_engine_prefers_docker_when_both_are_available(self):
        with patch(
            "west_env.engine.engine_available",
            side_effect=lambda name: name in {"docker", "podman"},
        ):
            self.assertEqual(detect_engine("auto"), ("docker", True))

    def test_detect_engine_uses_docker_when_only_docker_is_available(self):
        with patch(
            "west_env.engine.engine_available",
            side_effect=lambda name: name == "docker",
        ):
            self.assertEqual(detect_engine("auto"), ("docker", False))

    def test_detect_engine_uses_podman_when_only_podman_is_available(self):
        with patch(
            "west_env.engine.engine_available",
            side_effect=lambda name: name == "podman",
        ):
            self.assertEqual(detect_engine("auto"), ("podman", False))

    def test_detect_engine_respects_explicit_podman_preference(self):
        with patch(
            "west_env.engine.engine_available",
            side_effect=lambda name: name in {"docker", "podman"},
        ):
            self.assertEqual(detect_engine("podman"), ("podman", False))

    def test_detect_engine_raises_for_missing_preferred_engine(self):
        with patch(
            "west_env.engine.engine_available",
            side_effect=lambda name: False,
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "Requested engine not available: docker",
            ):
                detect_engine("docker")

    def test_detect_engine_raises_when_no_supported_engine_exists(self):
        with patch(
            "west_env.engine.engine_available",
            side_effect=lambda name: False,
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "No supported container engine found",
            ):
                detect_engine("auto")


if __name__ == "__main__":
    unittest.main()
