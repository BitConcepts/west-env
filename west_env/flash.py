# SPDX-License-Identifier: Apache-2.0
"""Flash and debug support for west-env.

Default mode (jlink.mode = host):
  Build artifacts are synced to the host by the workspace sync layer.
  Windows-native SEGGER J-Link tools are invoked on the synced .hex/.elf file.
  No USB passthrough into the container is required.

TCP server mode (jlink.mode = tcp-server):
  J-Link GDB server is started on the host.
  GDB inside the container connects via TCP (configurable port, default 2331).
"""

import subprocess
import sys
from pathlib import Path
from shutil import which
from typing import Optional


# ---------------------------------------------------------------------------
# J-Link discovery
# ---------------------------------------------------------------------------

_JLINK_SEARCH_PATHS_WIN = [
    r"C:\Program Files\SEGGER\JLink",
    r"C:\Program Files (x86)\SEGGER\JLink",
]
_JLINK_SEARCH_PATHS_LINUX = [
    "/opt/SEGGER/JLink",
    "/usr/bin",
    "/usr/local/bin",
]
_JLINK_SEARCH_PATHS_MAC = [
    "/Applications/SEGGER/JLink",
    "/usr/local/bin",
]


def find_jlink_exe(name: str = "JLinkExe") -> Optional[Path]:
    """Return the path to a J-Link executable, or None if not found."""
    # Check PATH first
    found = which(name)
    if found:
        return Path(found)

    # Windows also checks .exe
    if sys.platform == "win32":
        found = which(name + ".exe")
        if found:
            return Path(found)
        for search in _JLINK_SEARCH_PATHS_WIN:
            candidate = Path(search) / (name + ".exe")
            if candidate.is_file():
                return candidate

    elif sys.platform == "darwin":
        for search in _JLINK_SEARCH_PATHS_MAC:
            candidate = Path(search) / name
            if candidate.is_file():
                return candidate

    else:  # Linux
        for search in _JLINK_SEARCH_PATHS_LINUX:
            candidate = Path(search) / name
            if candidate.is_file():
                return candidate

    return None


# ---------------------------------------------------------------------------
# Flash
# ---------------------------------------------------------------------------


class FlashManager:
    """Manages J-Link host flashing and debug server."""

    def __init__(self, jlink_mode: str = "host", gdb_port: int = 2331):
        self.mode = jlink_mode
        self.gdb_port = gdb_port

    def flash(self, artifact: Path, device: str = "auto", extra_args: Optional[list] = None):
        """Flash a firmware artifact using the host J-Link.

        Args:
            artifact: Path to .hex, .elf, or .bin file (on the host filesystem).
            device:   J-Link device name (e.g. 'nRF52840_xxAA'). 'auto' uses
                      J-Link's auto-detection where supported.
            extra_args: Extra arguments passed to JLinkExe / JLinkCommander.
        """
        jlink = find_jlink_exe()
        if jlink is None:
            raise RuntimeError(
                "J-Link host tools not found. Install SEGGER J-Link from https://www.segger.com/downloads/jlink/"
            )

        artifact = Path(artifact)
        if not artifact.is_file():
            raise FileNotFoundError(f"Artifact not found: {artifact}")

        # Build a J-Link commander script
        script_lines = [
            "si SWD",
            "speed 4000",
        ]
        if device and device != "auto":
            script_lines.insert(0, f"device {device}")

        ext = artifact.suffix.lower()
        if ext == ".hex":
            script_lines += [f"loadfile {artifact}", "r", "g", "exit"]
        elif ext in (".elf", ".bin"):
            script_lines += [f"loadfile {artifact}", "r", "g", "exit"]
        else:
            raise ValueError(f"Unsupported artifact extension: {ext!r}")

        script = "\n".join(script_lines)

        cmd = [str(jlink), "-autoconnect", "1", "-commanderscript", "/dev/stdin"]
        if extra_args:
            cmd += extra_args

        proc = subprocess.run(
            cmd,
            input=script,
            text=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"JLink flash failed with exit code {proc.returncode}")

    def start_gdb_server(self, device: str, port: Optional[int] = None) -> subprocess.Popen:
        """Start a J-Link GDB server on the host.

        Returns the server subprocess.  Call .terminate() when done.

        Args:
            device: J-Link device name.
            port:   GDB port (default: self.gdb_port = 2331).
        """
        jlink_gdb = find_jlink_exe("JLinkGDBServerCL") or find_jlink_exe("JLinkGDBServer")
        if jlink_gdb is None:
            raise RuntimeError(
                "J-Link GDB Server not found. Install SEGGER J-Link from https://www.segger.com/downloads/jlink/"
            )

        _port = port or self.gdb_port
        cmd = [
            str(jlink_gdb),
            "-device",
            device,
            "-if",
            "SWD",
            "-speed",
            "4000",
            "-port",
            str(_port),
            "-nogui",
        ]
        return subprocess.Popen(cmd)


# ---------------------------------------------------------------------------
# Doctor check
# ---------------------------------------------------------------------------


def doctor_lines(jlink_mode: str = "host") -> list:
    """Return doctor output lines for flash/debug readiness."""
    lines = []
    jlink = find_jlink_exe()
    if jlink:
        lines.append(f"[PASS] J-Link host tools: {jlink}")
    else:
        if jlink_mode == "none":
            lines.append("[INFO] J-Link: disabled (jlink.mode = none)")
        else:
            lines.append("[WARN] J-Link host tools not found in PATH or standard locations")
            lines.append("       Install from https://www.segger.com/downloads/jlink/")

    lines.append(f"       mode: {jlink_mode}")
    if jlink_mode == "tcp-server":
        gdb_srv = find_jlink_exe("JLinkGDBServerCL") or find_jlink_exe("JLinkGDBServer")
        if gdb_srv:
            lines.append(f"[PASS] J-Link GDB server: {gdb_srv}")
        else:
            lines.append("[WARN] J-Link GDB Server not found (needed for tcp-server mode)")

    return lines
