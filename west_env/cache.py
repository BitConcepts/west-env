# SPDX-License-Identifier: Apache-2.0
"""Named-volume cache manager for west-env.

Manages persistent Docker/Podman volumes for:
  ccache   Compiler cache; survives container recreation.
  modules  west module cache (.west/, Zephyr sources).
  sdk      Zephyr SDK binaries.
  pip      pip download/wheel cache.

Usage
-----
  west env cache stats     — report volume sizes and ccache hit rate
  west env cache reset     — prune all cache volumes
  west env cache reset --ccache   — prune ccache only
  west env cache reset --modules  — prune west modules only
"""

import subprocess
from typing import Optional


# Volume name templates
_VOLUME_NAMES = {
    "ccache": "west-env-cache-ccache",
    "modules": "west-env-cache-modules",
    "sdk": "west-env-cache-sdk",
    "pip": "west-env-cache-pip",
}


class CacheManager:
    """Manages west-env named volumes."""

    def __init__(self, engine_name: str = "docker"):
        self.engine = engine_name

    # ------------------------------------------------------------------
    # Volume args (to be injected into docker/podman run)
    # ------------------------------------------------------------------

    def volume_args(self, ccache: bool = False, modules: bool = False, sdk: bool = False, pip: bool = False) -> list:
        """Return `-v` mount args for the enabled caches."""
        args = []
        if ccache:
            args += ["-v", f"{_VOLUME_NAMES['ccache']}:/root/.cache/ccache"]
            args += ["-e", "CCACHE_DIR=/root/.cache/ccache"]
        if modules:
            args += ["-v", f"{_VOLUME_NAMES['modules']}:/work/.west-cache"]
        if sdk:
            args += ["-v", f"{_VOLUME_NAMES['sdk']}:/opt/zephyr-sdk"]
        if pip:
            args += ["-v", f"{_VOLUME_NAMES['pip']}:/root/.cache/pip"]
        return args

    def volume_args_from_config(self, cfg) -> list:
        """Convenience: extract cache flags from an EnvConfig."""
        return self.volume_args(
            ccache=getattr(cfg, "cache_ccache", False),
            modules=getattr(cfg, "cache_modules", False),
            sdk=getattr(cfg, "cache_sdk", False),
            pip=getattr(cfg, "cache_pip", False),
        )

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        """Return a dict of {volume_name: size_bytes or None}."""
        result = {}
        for key, name in _VOLUME_NAMES.items():
            size = self._volume_size(name)
            result[key] = {"volume": name, "size_bytes": size}
        result["ccache_stats"] = self._ccache_stats()
        return result

    def print_stats(self):
        """Print a human-readable cache stats report."""
        data = self.stats()
        print("west-env cache volumes:")
        for key in ("ccache", "modules", "sdk", "pip"):
            info = data[key]
            size = info["size_bytes"]
            size_str = f"{size // 1024 // 1024} MB" if size is not None else "not created"
            print(f"  {key:10s}  {info['volume']:40s}  {size_str}")
        cc = data.get("ccache_stats") or {}
        if cc:
            print("\nccache stats:")
            for k, v in cc.items():
                print(f"  {k}: {v}")

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self, which: str = "all"):
        """Remove (prune) the specified cache volume(s).

        Args:
            which: 'all', 'ccache', 'modules', 'sdk', or 'pip'.
        """
        if which == "all":
            targets = list(_VOLUME_NAMES.values())
        elif which in _VOLUME_NAMES:
            targets = [_VOLUME_NAMES[which]]
        else:
            raise ValueError(f"Unknown cache target: {which!r}. Choose from: all, {', '.join(_VOLUME_NAMES)}")
        for volume in targets:
            self._remove_volume(volume)
            print(f"[OK] removed cache volume: {volume}")

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _volume_exists(self, name: str) -> bool:
        try:
            subprocess.check_call(
                [self.engine, "volume", "inspect", name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def _volume_size(self, name: str) -> Optional[int]:
        if not self._volume_exists(name):
            return None
        try:
            out = subprocess.check_output(
                [self.engine, "system", "df", "--format", "{{.Name}}\t{{.Size}}"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            for line in out.splitlines():
                parts = line.split("\t")
                if len(parts) == 2 and parts[0] == name:
                    return _parse_size(parts[1])
        except Exception:  # noqa
            pass
        return None

    def _ccache_stats(self) -> dict:
        if not self._volume_exists(_VOLUME_NAMES["ccache"]):
            return {}
        try:
            out = subprocess.check_output(
                [
                    self.engine,
                    "run",
                    "--rm",
                    "-v",
                    f"{_VOLUME_NAMES['ccache']}:/root/.cache/ccache",
                    "-e",
                    "CCACHE_DIR=/root/.cache/ccache",
                    "alpine",
                    "sh",
                    "-c",
                    "apk add --no-cache ccache -q && ccache -s 2>/dev/null",
                ],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=30,
            )
            stats = {}
            for line in out.splitlines():
                if "  " in line and line.strip():
                    parts = line.rsplit("  ", 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val = parts[1].strip()
                        if key:
                            stats[key] = val
            return stats
        except Exception:  # noqa
            return {}

    def _remove_volume(self, name: str):
        if not self._volume_exists(name):
            return
        try:
            subprocess.check_call(
                [self.engine, "volume", "rm", name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Failed to remove volume {name!r}. Make sure no containers are using it.") from exc


def _parse_size(size_str: str) -> Optional[int]:
    """Parse Docker size string (e.g. '1.5GB', '512MB') to bytes."""
    s = size_str.strip().upper()
    try:
        if s.endswith("GB"):
            return int(float(s[:-2]) * 1024**3)
        if s.endswith("MB"):
            return int(float(s[:-2]) * 1024**2)
        if s.endswith("KB"):
            return int(float(s[:-2]) * 1024)
        if s.endswith("B"):
            return int(float(s[:-1]))
        return int(float(s))
    except (ValueError, TypeError):
        return None
