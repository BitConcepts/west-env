# SPDX-License-Identifier: Apache-2.0
"""Tests for west_env.util — check_python() and check_west()."""

import collections
import sys
from unittest.mock import patch

import pytest

from west_env.util import MIN_PYTHON, check_python, check_west

# ---------------------------------------------------------------------------
# Helper: a tuple-subclass that also exposes .major / .minor attributes so
# that check_python()'s f-string formatting works, just like sys.version_info.
# ---------------------------------------------------------------------------
_FakeVI = collections.namedtuple("version_info", ["major", "minor", "micro", "releaselevel", "serial"])


class TestCheckPython:
    def test_current_version_passes(self):
        """The Python running the tests is >=3.10, so this must return True."""
        assert check_python() is True

    def test_minimum_version_passes(self):
        at_min = _FakeVI(MIN_PYTHON[0], MIN_PYTHON[1], 0, "final", 0)
        with patch("west_env.util.sys") as mock_sys:
            mock_sys.version_info = at_min
            result = check_python()
        assert result is True

    def test_old_major_fails(self, capsys):
        old = _FakeVI(2, 7, 18, "final", 0)
        with patch("west_env.util.sys") as mock_sys:
            mock_sys.version_info = old
            result = check_python()
        assert result is False
        assert "[FAIL]" in capsys.readouterr().out

    def test_too_old_minor_fails(self, capsys):
        # 3.9 is below MIN_PYTHON (3.10)
        too_old = _FakeVI(3, 9, 0, "final", 0)
        with patch("west_env.util.sys") as mock_sys:
            mock_sys.version_info = too_old
            result = check_python()
        assert result is False

    def test_pass_message_contains_version(self, capsys):
        check_python()
        out = capsys.readouterr().out
        assert "[PASS]" in out
        assert f"{sys.version_info.major}.{sys.version_info.minor}" in out


class TestCheckWest:
    def test_west_found(self, capsys):
        with patch("west_env.util.subprocess.check_output", return_value=b"west 1.5.0"):
            result = check_west()
        assert result is True
        assert "[PASS]" in capsys.readouterr().out

    def test_west_not_found(self, capsys):
        with patch(
            "west_env.util.subprocess.check_output",
            side_effect=FileNotFoundError("west not found"),
        ):
            result = check_west()
        assert result is False
        assert "[FAIL]" in capsys.readouterr().out

    def test_west_subprocess_error(self, capsys):
        """Any exception (e.g. CalledProcessError) counts as west missing."""
        import subprocess

        with patch(
            "west_env.util.subprocess.check_output",
            side_effect=subprocess.CalledProcessError(1, "west"),
        ):
            result = check_west()
        assert result is False
