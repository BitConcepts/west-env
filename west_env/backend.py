# SPDX-License-Identifier: Apache-2.0
"""Backend detection and selection for west-env.

Replaces the simple engine.py two-backend model with a full platform-aware
backend detector covering all six supported container/VM backends.

Backends:
  podman-machine-hyperv  Podman machine backed by Hyper-V VM  (Windows preferred)
  docker-desktop         Docker Desktop (WSL2 backend)         (Windows fallback)
  podman-native          Podman binary, native Linux daemon    (Linux preferred)
  docker-native          Docker binary, native Linux daemon    (Linux)
  podman-machine         Podman machine (non-Hyper-V VM)       (macOS preferred)
  docker-machine         Docker Desktop (macOS)                (macOS fallback)
"""

import json
import subprocess
import sys
from dataclasses import dataclass, field
from shutil import which
from typing import Optional


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class BackendProbe:
    """Result of probing a single backend."""

    name: str
    available: bool
    version: Optional[str] = None
    warning: Optional[str] = None
    notes: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Low-level probes  (all subprocess calls isolated here for easy mocking)
# ---------------------------------------------------------------------------


def _binary_version(cmd: str, version_flag: str = "version") -> Optional[str]:
    """Return first line of `cmd version_flag` output, or None if unavailable."""
    if not which(cmd):
        return None
    try:
        out = subprocess.check_output(
            [cmd, version_flag],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        )
        return out.strip().splitlines()[0]
    except Exception:  # noqa
        return None


def _podman_machine_running() -> bool:
    """Return True if at least one Podman machine is in 'Running' state."""
    if not which("podman"):
        return False
    try:
        out = subprocess.check_output(
            ["podman", "machine", "list", "--format", "json"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        )
        machines = json.loads(out)
        return any(m.get("Running") or m.get("State") == "running" for m in machines)
    except Exception:  # noqa
        return False


def _hyperv_enabled() -> bool:
    """Return True if Hyper-V is enabled on Windows (requires PowerShell)."""
    if sys.platform != "win32":
        return False
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All"
                " -ErrorAction SilentlyContinue).State",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return "Enabled" in result.stdout
    except Exception:  # noqa
        return False


def _docker_uses_wsl2() -> bool:
    """Return True if the running Docker daemon reports a WSL2/Desktop backend."""
    if not which("docker"):
        return False
    try:
        out = subprocess.check_output(
            ["docker", "info", "--format", "{{.OperatingSystem}}"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        )
        return "Docker Desktop" in out or "WSL" in out
    except Exception:  # noqa
        return False


# ---------------------------------------------------------------------------
# Per-backend probe functions
# ---------------------------------------------------------------------------


def _probe_podman_machine_hyperv() -> BackendProbe:
    ver = _binary_version("podman")
    if ver is None:
        return BackendProbe("podman-machine-hyperv", False, notes=["podman not found in PATH"])
    if not _hyperv_enabled():
        return BackendProbe(
            "podman-machine-hyperv",
            False,
            version=ver,
            notes=["Hyper-V not enabled — run as admin or enable via Windows Features"],
        )
    if not _podman_machine_running():
        return BackendProbe(
            "podman-machine-hyperv", False, version=ver, notes=["No running Podman machine — run: podman machine start"]
        )
    return BackendProbe("podman-machine-hyperv", True, version=ver)


def _probe_docker_desktop() -> BackendProbe:
    ver = _binary_version("docker")
    if ver is None:
        return BackendProbe("docker-desktop", False, notes=["docker not found in PATH"])
    if not _docker_uses_wsl2():
        return BackendProbe(
            "docker-desktop", False, version=ver, notes=["Docker found but does not appear to be Docker Desktop/WSL2"]
        )
    return BackendProbe(
        "docker-desktop",
        True,
        version=ver,
        warning="Docker Desktop (WSL2 bind mount) detected. "
        "Build performance on C:\\ paths may be poor. "
        "Consider Podman machine (Hyper-V) for better performance.",
    )


def _probe_podman_native() -> BackendProbe:
    ver = _binary_version("podman")
    if ver is None:
        return BackendProbe("podman-native", False, notes=["podman not found in PATH"])
    return BackendProbe("podman-native", True, version=ver)


def _probe_docker_native() -> BackendProbe:
    ver = _binary_version("docker")
    if ver is None:
        return BackendProbe("docker-native", False, notes=["docker not found in PATH"])
    return BackendProbe("docker-native", True, version=ver)


def _probe_podman_machine() -> BackendProbe:
    ver = _binary_version("podman")
    if ver is None:
        return BackendProbe("podman-machine", False, notes=["podman not found in PATH"])
    if not _podman_machine_running():
        return BackendProbe(
            "podman-machine", False, version=ver, notes=["No running Podman machine — run: podman machine start"]
        )
    return BackendProbe("podman-machine", True, version=ver)


def _probe_docker_machine() -> BackendProbe:
    ver = _binary_version("docker")
    if ver is None:
        return BackendProbe("docker-machine", False, notes=["docker not found in PATH"])
    return BackendProbe("docker-machine", True, version=ver)


# ---------------------------------------------------------------------------
# Detection entry points
# ---------------------------------------------------------------------------


def detect_all(host_platform: Optional[str] = None) -> dict:
    """Probe all backends and return a dict keyed by backend name.

    Args:
        host_platform: Override sys.platform (for testing). 'win32' / 'linux' / 'darwin'.

    Returns:
        Mapping of backend name -> BackendProbe.
    """
    plat = host_platform or sys.platform

    if plat == "win32":
        probes = [
            _probe_podman_machine_hyperv,
            _probe_docker_desktop,
        ]
    elif plat == "darwin":
        probes = [
            _probe_podman_machine,
            _probe_docker_machine,
        ]
    else:  # linux and anything else
        probes = [
            _probe_podman_native,
            _probe_docker_native,
        ]

    return {fn().name: fn() for fn in probes}


# Fallback chains per platform
_FALLBACK_CHAIN = {
    "win32": ["podman-machine-hyperv", "docker-desktop"],
    "darwin": ["podman-machine", "docker-machine"],
    "linux": ["podman-native", "docker-native"],
}


def select(preferred: str = "auto", host_platform: Optional[str] = None):
    """Select the best available backend.

    Args:
        preferred: Explicit backend name, or 'auto'.
        host_platform: Override sys.platform (for testing).

    Returns:
        Tuple of (backend_name, BackendProbe, list_of_warning_strings).

    Raises:
        RuntimeError: If no backend is available.
    """
    plat = host_platform or sys.platform
    probes = detect_all(plat)
    warnings = []

    if preferred and preferred != "auto":
        probe = probes.get(preferred)
        if probe is None:
            # Try to probe it even if not in default chain for this platform
            probe_fn = {
                "podman-machine-hyperv": _probe_podman_machine_hyperv,
                "docker-desktop": _probe_docker_desktop,
                "podman-native": _probe_podman_native,
                "docker-native": _probe_docker_native,
                "podman-machine": _probe_podman_machine,
                "docker-machine": _probe_docker_machine,
            }.get(preferred)
            if probe_fn:
                probe = probe_fn()
            else:
                raise RuntimeError(f"Unknown backend: {preferred!r}")
        if not probe.available:
            raise RuntimeError(
                f"Requested backend {preferred!r} is not available: " + "; ".join(probe.notes or ["unknown reason"])
            )
        if probe.warning:
            warnings.append(probe.warning)
        return preferred, probe, warnings

    # Auto-select: walk fallback chain
    chain = _FALLBACK_CHAIN.get(plat, ["podman-native", "docker-native"])
    for name in chain:
        probe = probes.get(name)
        if probe is None:
            # Probe on demand if not in dict
            probe_fns = {
                "podman-machine-hyperv": _probe_podman_machine_hyperv,
                "docker-desktop": _probe_docker_desktop,
                "podman-native": _probe_podman_native,
                "docker-native": _probe_docker_native,
                "podman-machine": _probe_podman_machine,
                "docker-machine": _probe_docker_machine,
            }
            if name in probe_fns:
                probe = probe_fns[name]()
            else:
                continue
        if probe.available:
            if probe.warning:
                warnings.append(probe.warning)
            return name, probe, warnings
        # Record what was skipped
        for note in probe.notes:
            warnings.append(f"Skipped {name}: {note}")

    raise RuntimeError(f"No supported container backend found on {plat}. Install Docker or Podman and try again.")


def doctor_lines(host_platform: Optional[str] = None) -> list:
    """Return a list of doctor output lines describing backend state."""
    plat = host_platform or sys.platform
    probes = detect_all(plat)
    lines = []

    try:
        name, probe, sel_warnings = select(host_platform=plat)
        lines.append(f"[PASS] backend selected: {name}")
        if probe.version:
            lines.append(f"       version: {probe.version}")
        for w in sel_warnings:
            lines.append(f"[WARN] {w}")
    except RuntimeError as exc:
        lines.append(f"[FAIL] {exc}")

    lines.append("")
    lines.append("Backend probe results:")
    for name, probe in probes.items():
        status = "[PASS]" if probe.available else "[SKIP]"
        ver = f" ({probe.version})" if probe.version else ""
        lines.append(f"  {status} {name}{ver}")
        for note in probe.notes or []:
            lines.append(f"         {note}")

    return lines


# ---------------------------------------------------------------------------
# Compatibility shim — keep engine-style interface for container.py
# ---------------------------------------------------------------------------


class ContainerBackend:
    """Thin wrapper that mimics ContainerEngine for use in container.py."""

    def __init__(self, name: str):
        # Map new backend names to the underlying binary name
        _binary_map = {
            "podman-machine-hyperv": "podman",
            "docker-desktop": "docker",
            "podman-native": "podman",
            "docker-native": "docker",
            "podman-machine": "podman",
            "docker-machine": "docker",
        }
        self.name = _binary_map.get(name, name.split("-")[0])
        self.backend_name = name

    def run(self, args: list):
        subprocess.check_call([self.name] + args)


def get_backend(preferred: str = "auto", host_platform: Optional[str] = None):
    """Return (ContainerBackend, warned) — compatible with get_engine() interface."""
    try:
        name, probe, warnings = select(preferred=preferred, host_platform=host_platform)
        warned = bool(warnings)
        return ContainerBackend(name), warned
    except RuntimeError:
        raise
