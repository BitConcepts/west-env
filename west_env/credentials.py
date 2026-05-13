# SPDX-License-Identifier: Apache-2.0
"""Git credential forwarding for west-env containers.

Strategy selection (in priority order):
  openssh-agent    Forward the host SSH agent socket into the container.
                   On Windows: uses the Windows OpenSSH agent service.
  credential-manager  Configure Git to delegate to the host credential manager.
                      (HTTPS remotes only; requires host-side credential store.)
  none             No credential forwarding.  Private repos will fail to clone.

The strategy is auto-detected when git.credential_helper = auto.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------

def _ssh_agent_socket() -> Optional[str]:
    """Return the SSH agent socket path if an agent is running, else None."""
    # Standard POSIX env var
    sock = os.environ.get("SSH_AUTH_SOCK")
    if sock and Path(sock).exists():
        return sock

    # Windows: OpenSSH agent pipe path
    if sys.platform == "win32":
        # Windows SSH agent exposes a named pipe; we can't forward it directly
        # to Linux containers, but we can detect if it's running.
        try:
            result = subprocess.run(
                ["sc", "query", "ssh-agent"],
                capture_output=True, text=True, timeout=5,
            )
            if "RUNNING" in result.stdout:
                return "\\\\pipe\\openssh-ssh-agent"
        except Exception:  # noqa
            pass

    return None


def _git_credential_manager_installed() -> bool:
    """Return True if Git Credential Manager is configured on the host."""
    try:
        out = subprocess.check_output(
            ["git", "config", "--global", "credential.helper"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        return bool(out)
    except Exception:  # noqa
        return False


# ---------------------------------------------------------------------------
# Strategy detection
# ---------------------------------------------------------------------------

def detect_strategy(preferred: str = "auto") -> str:
    """Return the active credential strategy name.

    Returns one of: 'openssh-agent', 'credential-manager', 'none'.
    """
    if preferred != "auto":
        return preferred

    sock = _ssh_agent_socket()
    if sock:
        return "openssh-agent"

    if _git_credential_manager_installed():
        return "credential-manager"

    return "none"


def container_args(strategy: Optional[str] = None) -> list:
    """Return docker/podman run args that forward credentials into the container.

    Args:
        strategy: One of 'openssh-agent', 'credential-manager', 'none', or None
                  to auto-detect.

    Returns:
        List of -v / -e args to append to docker run.
    """
    strat = strategy or detect_strategy()

    if strat == "openssh-agent":
        return _openssh_agent_args()

    if strat == "credential-manager":
        # Nothing to mount; we configure git inside the container instead
        return []

    return []  # 'none'


def _openssh_agent_args() -> list:
    """Return args to forward the SSH agent socket."""
    if sys.platform == "win32":
        # Windows SSH agent uses a named pipe that can't be directly forwarded.
        # In practice, SSH_AUTH_SOCK can be set to a relay socket by tools like
        # npiperelay or pageant-compatible agents.  We expose whatever is set.
        sock = os.environ.get("SSH_AUTH_SOCK", "")
        if sock:
            return [
                "-v", f"{sock}:/tmp/ssh-agent.sock",
                "-e", "SSH_AUTH_SOCK=/tmp/ssh-agent.sock",
            ]
        return []

    sock = _ssh_agent_socket()
    if sock:
        return [
            "-v", f"{sock}:/tmp/ssh-agent.sock:ro",
            "-e", "SSH_AUTH_SOCK=/tmp/ssh-agent.sock",
        ]
    return []


# ---------------------------------------------------------------------------
# Doctor check
# ---------------------------------------------------------------------------

def doctor_lines(preferred: str = "auto") -> list:
    """Return doctor output lines for the credential strategy."""
    strat = detect_strategy(preferred)
    lines = []

    if strat == "openssh-agent":
        sock = _ssh_agent_socket()
        lines.append("[PASS] git credentials: openssh-agent")
        if sock:
            lines.append(f"       socket: {sock}")
        else:
            lines.append("[WARN] SSH_AUTH_SOCK not set; agent may not be running")

    elif strat == "credential-manager":
        try:
            helper = subprocess.check_output(
                ["git", "config", "--global", "credential.helper"],
                text=True, stderr=subprocess.DEVNULL,
            ).strip()
        except Exception:  # noqa
            helper = "(unknown)"
        lines.append(f"[PASS] git credentials: credential-manager ({helper})")
        lines.append("       Note: HTTPS remotes only; SSH remotes require agent forwarding.")

    else:
        lines.append("[WARN] git credentials: none — private repos will fail inside container")
        lines.append("       Set SSH_AUTH_SOCK or configure git credential.helper on host")

    return lines


# ---------------------------------------------------------------------------
# Git safe.directory (re-exported for convenience)
# ---------------------------------------------------------------------------

GIT_SAFE_DIRECTORY_CMD = "git config --global safe.directory '*'"
