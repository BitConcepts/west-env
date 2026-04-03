"""Unit tests for west_env.util."""

# SPDX-License-Identifier: Apache-2.0

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from west_env.util import host_shell_command


class UtilTests(unittest.TestCase):
    def test_host_shell_command_prefers_pwsh_on_windows(self):
        with patch("west_env.util.os.name", "nt"), patch(
            "west_env.util.which",
            side_effect=lambda name: (
                r"C:\Program Files\PowerShell\7\pwsh.exe"
                if name == "pwsh"
                else None
            ),
        ), patch.dict(
            "west_env.util.os.environ",
            {"COMSPEC": r"C:\Windows\System32\cmd.exe"},
            clear=True,
        ):
            self.assertEqual(
                host_shell_command(),
                [r"C:\Program Files\PowerShell\7\pwsh.exe"],
            )

    def test_host_shell_command_uses_shell_on_posix(self):
        with patch("west_env.util.os.name", "posix"), patch.dict(
            "west_env.util.os.environ",
            {"SHELL": "/bin/zsh"},
            clear=True,
        ):
            self.assertEqual(host_shell_command(), ["/bin/zsh"])


if __name__ == "__main__":
    unittest.main()
