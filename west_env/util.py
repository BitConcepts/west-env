# SPDX-License-Identifier: Apache-2.0

import subprocess
import sys

MIN_PYTHON = (3, 10)


def run_host(cmd):
    subprocess.check_call(cmd)


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
