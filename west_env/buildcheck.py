# SPDX-License-Identifier: Apache-2.0
"""Stale build directory detection for west-env.

When a user switches between native execution mode and container mode, the
existing build/ directory contains CMake cache entries that reference absolute
paths for the old mode:

  Native mode:   CMAKE_SOURCE_DIR = /home/user/workspace  (host path)
  Container mode: CMAKE_SOURCE_DIR = /work                (container mount)

If the mode switches, the stale paths cause confusing CMake failures.
This module detects the mismatch and warns the user before the build starts.
"""

import shutil
from pathlib import Path
from typing import Optional


# CMakeCache entries that contain the workspace root path
_CMAKE_SOURCE_KEYS = (
    "CMAKE_SOURCE_DIR:STATIC=",
    "CMAKE_HOME_DIRECTORY:INTERNAL=",
)

# The path prefix used inside all west-env containers
CONTAINER_WORK_PREFIX = "/work"


def _read_cmake_source_dir(build_dir: Path) -> Optional[str]:
    """Return the CMAKE_SOURCE_DIR from build/CMakeCache.txt, or None."""
    cache = build_dir / "CMakeCache.txt"
    if not cache.exists():
        return None
    try:
        with cache.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                stripped = line.strip()
                for key in _CMAKE_SOURCE_KEYS:
                    if stripped.startswith(key):
                        return stripped[len(key) :]
    except OSError:
        return None
    return None


def detect_stale_build(build_dir: Path, use_container: bool) -> Optional[str]:
    """Check whether an existing build directory was created in a different mode.

    Args:
        build_dir:     Path to the CMake build directory (usually <topdir>/build).
        use_container: True if the current invocation will run in a container.

    Returns:
        A human-readable warning string if the build directory is stale,
        or None if everything looks fine (or the directory does not exist yet).
    """
    if not build_dir.exists():
        return None

    source_dir = _read_cmake_source_dir(build_dir)
    if source_dir is None:
        # Build dir exists but no CMakeCache — not yet configured, no conflict.
        return None

    was_container_build = source_dir.startswith(CONTAINER_WORK_PREFIX)

    if use_container and not was_container_build:
        return (
            f"[WARN] Stale build directory: {build_dir}\n"
            f"       It was created in native mode (source: {source_dir})\n"
            f"       but you are now building in container mode (source: /work/...).\n"
            f"       CMake cache paths will be wrong and the build will fail.\n"
            f"       Remove the build directory first, or pass --clean to do it automatically."
        )

    if not use_container and was_container_build:
        return (
            f"[WARN] Stale build directory: {build_dir}\n"
            f"       It was created in container mode (source: {source_dir})\n"
            f"       but you are now building in native mode.\n"
            f"       CMake cache paths will be wrong and the build will fail.\n"
            f"       Remove the build directory first, or pass --clean to do it automatically."
        )

    return None


def clean_build_dir(build_dir: Path) -> None:
    """Remove the build directory unconditionally."""
    if build_dir.exists():
        shutil.rmtree(build_dir)
