# SPDX-License-Identifier: Apache-2.0

import os
import subprocess
import sys
from shutil import which

MIN_PYTHON = (3, 10)


def run_host(cmd):
    subprocess.check_call(cmd)


def host_shell_command():
    if os.name == "nt":
        for shell in ("pwsh", "powershell"):
            path = which(shell)
            if path:
                return [path]

        return [os.environ.get("COMSPEC", "cmd.exe")]

    shell = os.environ.get("SHELL")
    if shell:
        return [shell]

    return ["/bin/sh"]


def check_python():
    version = sys.version_info
    if version < MIN_PYTHON:
        print(
            f"[FAIL] Python {version.major}.{version.minor} "
            f"(minimum required: {MIN_PYTHON[0]}.{MIN_PYTHON[1]})"
        )
        return False

    print(
        f"[PASS] Python {version.major}.{version.minor}.{version.micro}"
    )
    return True


def check_west():
    try:
        subprocess.check_output(["west", "--version"])
        print("[PASS] west is installed")
        return True
    except Exception:  # noqa
        print("[FAIL] west not found in PATH")
        return False
