# SPDX-License-Identifier: Apache-2.0
"""Tests for west_env.engine — engine detection logic."""

from unittest.mock import patch

import pytest

from west_env.engine import ContainerEngine, detect_engine, engine_available


def _make_which(available: set):
    """Return a which() side_effect that recognises names in *available*."""
    return lambda name: f"/usr/bin/{name}" if name in available else None


class TestEngineAvailable:
    def test_found(self):
        with patch("west_env.engine.which", return_value="/usr/bin/docker"):
            assert engine_available("docker") is True

    def test_not_found(self):
        with patch("west_env.engine.which", return_value=None):
            assert engine_available("docker") is False


class TestDetectEngine:
    def test_docker_only(self):
        with patch("west_env.engine.which", side_effect=_make_which({"docker"})):
            name, warned = detect_engine()
        assert name == "docker"
        assert warned is False

    def test_podman_only(self):
        with patch("west_env.engine.which", side_effect=_make_which({"podman"})):
            name, warned = detect_engine()
        assert name == "podman"
        assert warned is False

    def test_both_prefers_docker_and_warns(self):
        with patch("west_env.engine.which", side_effect=_make_which({"docker", "podman"})):
            name, warned = detect_engine()
        assert name == "docker"
        assert warned is True

    def test_neither_raises(self):
        with patch("west_env.engine.which", side_effect=_make_which(set())):
            with pytest.raises(RuntimeError, match="No supported container engine"):
                detect_engine()

    def test_preferred_docker_available(self):
        with patch("west_env.engine.which", side_effect=_make_which({"docker"})):
            name, warned = detect_engine(preferred="docker")
        assert name == "docker"
        assert warned is False

    def test_preferred_docker_unavailable_raises(self):
        with patch("west_env.engine.which", side_effect=_make_which({"podman"})):
            with pytest.raises(RuntimeError, match="not available"):
                detect_engine(preferred="docker")

    def test_preferred_podman_available(self):
        with patch("west_env.engine.which", side_effect=_make_which({"podman"})):
            name, warned = detect_engine(preferred="podman")
        assert name == "podman"
        assert warned is False

    def test_preferred_auto_both_warns(self):
        with patch("west_env.engine.which", side_effect=_make_which({"docker", "podman"})):
            name, warned = detect_engine(preferred="auto")
        assert name == "docker"
        assert warned is True

    def test_preferred_auto_docker_only(self):
        with patch("west_env.engine.which", side_effect=_make_which({"docker"})):
            name, warned = detect_engine(preferred="auto")
        assert name == "docker"
        assert warned is False

    def test_preferred_auto_podman_only(self):
        with patch("west_env.engine.which", side_effect=_make_which({"podman"})):
            name, warned = detect_engine(preferred="auto")
        assert name == "podman"
        assert warned is False
