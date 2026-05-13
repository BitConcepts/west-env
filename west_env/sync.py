# SPDX-License-Identifier: Apache-2.0
"""Workspace synchronization layer for west-env.

Implements four workspace modes:

  sync   rsync host → VM/container volume; sync artifacts back.
         Recommended on Windows (avoids NTFS→Linux bind-mount overhead).
  copy   Copy source into container at build start; copy artifacts out at end.
         Portable fallback, no volume required.
  tmpfs  Source synced; build directory is a container tmpfs.
         Maximum build speed, artifacts lost on container exit unless synced back.
  bind   Direct host-path bind mount (Linux/macOS native; WARNING on Windows).

Exclusion patterns (source sync only):
  build/, .cache/, twister-out/, .west/, *.egg-info/
  Configurable via west-env.yml sync.exclude.
"""

import fnmatch
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Directories always excluded from source → container sync
DEFAULT_EXCLUDES = [
    "build",
    ".cache",
    "twister-out",
    ".west",
    "*.egg-info",
    "__pycache__",
    ".git",
    ".venv",
    "venv",
]

# Artifact extensions sync'd back from container → host
ARTIFACT_EXTENSIONS = {".elf", ".bin", ".hex", ".map", ".lst", ".s19"}


class SyncWarning(UserWarning):
    pass


def _warn_bind_on_windows(workspace_mode: str):
    """Print a performance warning if bind mode is used on Windows."""
    if workspace_mode == "bind" and sys.platform == "win32":
        import warnings
        warnings.warn(
            "[WARN] workspace_mode=bind on Windows mounts C:\\ paths into a Linux "
            "container. Build performance will be poor due to NTFS→Linux filesystem "
            "overhead. Consider workspace_mode=sync with a Podman Hyper-V backend.",
            SyncWarning,
            stacklevel=3,
        )


def _is_excluded(path: Path, root: Path, patterns: list) -> bool:
    """Return True if *path* (relative to *root*) matches any exclusion pattern."""
    try:
        rel = path.relative_to(root)
    except ValueError:
        return False
    parts = rel.parts
    for pattern in patterns:
        # Match against any component in the path
        if any(fnmatch.fnmatch(part, pattern) for part in parts):
            return True
    return False


def _copy_tree(src: Path, dst: Path, excludes: list):
    """Recursively copy *src* → *dst* honouring *excludes*."""
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if _is_excluded(item, src, excludes):
            continue
        dest = dst / item.name
        if item.is_dir():
            _copy_tree(item, dest, excludes)
        else:
            shutil.copy2(str(item), str(dest))


def _rsync_to(src: Path, dst_spec: str, excludes: list):
    """rsync source → dst_spec, applying excludes.  Falls back to shutil on Windows."""
    if shutil.which("rsync"):
        cmd = ["rsync", "-a", "--delete"]
        for exc in excludes:
            cmd += ["--exclude", exc]
        cmd += [str(src) + "/", dst_spec]
        subprocess.check_call(cmd)
    else:
        # Fallback: plain Python copy (slower, no --delete)
        dst_path = Path(dst_spec)
        _copy_tree(src, dst_path, excludes)


class WorkspaceSync:
    """Manages source ↔ container workspace synchronization."""

    def __init__(self, workspace_mode: str = "bind", excludes: Optional[list] = None):
        self.mode = workspace_mode
        self.excludes = list(excludes or DEFAULT_EXCLUDES)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def warn_if_needed(self):
        """Emit performance warning if mode is 'bind' on Windows."""
        _warn_bind_on_windows(self.mode)

    def volume_args(self, host_workspace: Path, engine_name: str) -> list:
        """Return the docker/podman volume/tmpfs args for the chosen mode.

        These args are appended to `docker run` / `podman run`.
        """
        host_workspace = host_workspace.resolve()
        if self.mode == "bind":
            self.warn_if_needed()
            return ["-v", f"{host_workspace}:/work"]
        elif self.mode in ("sync", "copy"):
            # Named volume (caller is responsible for populating it first)
            volume_name = f"west-env-ws-{_workspace_slug(host_workspace)}"
            return ["-v", f"{volume_name}:/work"]
        elif self.mode == "tmpfs":
            volume_name = f"west-env-ws-{_workspace_slug(host_workspace)}"
            return [
                "-v", f"{volume_name}:/work",
                "--mount", "type=tmpfs,destination=/work/build",
            ]
        else:
            raise ValueError(f"Unknown workspace mode: {self.mode!r}")

    def sync_to_volume(self, host_workspace: Path, engine: str, volume_name: str):
        """Copy source files from host into a named Docker/Podman volume.

        Uses a temporary container to write into the volume.
        Excluded directories (build/, .cache/, etc.) are not copied.
        """
        host_workspace = host_workspace.resolve()
        # On Windows fall back to docker cp approach; on POSIX use tar pipe
        if sys.platform == "win32" or not shutil.which("tar"):
            _sync_via_docker_cp(engine, host_workspace, volume_name, self.excludes)
        else:
            _sync_via_tar_pipe(engine, host_workspace, volume_name, self.excludes)

    def sync_from_volume(self, engine: str, volume_name: str, host_dst: Path):
        """Copy build artifacts from a named volume back to the host."""
        host_dst.mkdir(parents=True, exist_ok=True)
        # Extract artifact files from /work/build inside the volume
        extract_cmd = [
            engine, "run", "--rm",
            "-v", f"{volume_name}:/work",
            "-v", f"{host_dst}:/output",
            "alpine",
            "sh", "-c",
            "find /work/build -type f \\( "
            + " -o ".join(f"-name '*{ext}'" for ext in ARTIFACT_EXTENSIONS)
            + " \\) -exec cp --parents {} /output/ \\; 2>/dev/null || true",
        ]
        try:
            subprocess.check_call(extract_cmd, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            pass  # Non-fatal: no artifacts yet

    def status(self, host_workspace: Path) -> dict:
        """Return a dict describing sync state."""
        host_workspace = host_workspace.resolve()
        volume_name = f"west-env-ws-{_workspace_slug(host_workspace)}"
        return {
            "mode": self.mode,
            "host_workspace": str(host_workspace),
            "volume_name": volume_name,
            "excludes": self.excludes,
        }


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _workspace_slug(path: Path) -> str:
    """Return a short, filesystem-safe identifier for a workspace path."""
    return path.name.lower().replace(" ", "-").replace("\\", "-").replace("/", "-")[:40]


def _sync_via_tar_pipe(engine: str, src: Path, volume_name: str, excludes: list):
    """Pipe a tar stream into a volume via a temporary container."""
    # Build exclude args for tar
    tar_excludes = []
    for exc in excludes:
        tar_excludes += ["--exclude", exc]

    tar_proc = subprocess.Popen(
        ["tar", "-cf", "-"] + tar_excludes + ["-C", str(src), "."],
        stdout=subprocess.PIPE,
    )
    docker_proc = subprocess.Popen(
        [engine, "run", "--rm", "-v", f"{volume_name}:/work", "-i", "alpine",
         "tar", "-xf", "-", "-C", "/work"],
        stdin=tar_proc.stdout,
    )
    tar_proc.stdout.close()
    docker_proc.wait()
    tar_proc.wait()


def _sync_via_docker_cp(engine: str, src: Path, volume_name: str, excludes: list):
    """Copy files into a volume using `docker cp` via a scratch container."""
    # Create a scratch container
    cid = subprocess.check_output(
        [engine, "create", "-v", f"{volume_name}:/work", "alpine", "true"],
        text=True,
    ).strip()
    try:
        # Copy each file not matching excludes
        for item in src.iterdir():
            if not _is_excluded(item, src, excludes):
                subprocess.check_call(
                    [engine, "cp", str(item), f"{cid}:/work/{item.name}"],
                    stderr=subprocess.DEVNULL,
                )
    finally:
        subprocess.call([engine, "rm", cid], stderr=subprocess.DEVNULL)
