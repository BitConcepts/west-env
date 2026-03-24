# SPDX-License-Identifier: Apache-2.0

import hashlib
from pathlib import Path
import subprocess
from west.util import west_topdir
from west_env.engine import get_engine

CONTAINER_WORKDIR = "/work"


def _volume_name(workspace: Path) -> str:
    """Deterministic volume name for the build cache."""
    digest = hashlib.sha256(str(workspace).encode()).hexdigest()[:12]
    return f"west-env-build-{digest}"


def _ensure_volume(engine, name: str):
    """Create a named volume if it does not already exist."""
    result = subprocess.run(
        [engine.name, "volume", "inspect", name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        subprocess.check_call(
            [engine.name, "volume", "create", name],
            stdout=subprocess.DEVNULL,
        )


def _container_workdir(workspace: Path) -> str:
    """Compute the container working directory from host cwd."""
    host_cwd = Path.cwd().resolve()
    try:
        rel = host_cwd.relative_to(workspace)
        rel_posix = rel.as_posix()
        return (
            CONTAINER_WORKDIR
            if rel_posix == "."
            else f"{CONTAINER_WORKDIR}/{rel_posix}"
        )
    except ValueError:
        return CONTAINER_WORKDIR


def _git_safe_dir_cmd():
    return "git config --global safe.directory '*'"


def _container_prep_cmd():
    """Commands to run before the main command inside the container.

    Installs project-specific Python deps that may not be in the base image.
    Uses --quiet and allows failure on individual packages so the build
    isn't blocked by optional deps.
    """
    return (
        "pip install --quiet --disable-pip-version-check "
        "-r /work/external/zephyr/modules/canopennode/zephyr/requirements.txt "
        "2>/dev/null || true"
    )


# -----------------------------------------------------------------
# Bind-mount mode (original behavior)
# -----------------------------------------------------------------
def run_container(cfg, command, interactive=False):
    engine, warned = get_engine(cfg.engine)

    if warned:
        print("[WARN] Both Docker and Podman detected; using Docker")

    workspace = Path(west_topdir()).resolve()
    container_wd = _container_workdir(workspace)

    args = [
        "run",
        "--rm",
        "-v",
        f"{workspace}:{CONTAINER_WORKDIR}",
        "-w",
        container_wd,
        "-e",
        "PYTHONPATH=/work/modules/west-env",
    ]

    if interactive:
        args.append("-it")

    full_cmd = " ".join(command)
    args.append(cfg.image)
    args.extend([
        "sh",
        "-c",
        f"{_git_safe_dir_cmd()} && {_container_prep_cmd()} && exec {full_cmd}",
    ])

    engine.run(args)


# -----------------------------------------------------------------
# Volume mode:
#
# The workspace (source, .west/, external/) is bind-mounted from the
# host so west can resolve the manifest and find all modules.  Only
# the build output directory is placed on a named Docker volume for
# fast I/O.  This avoids the expensive NTFS-to-ext4 translation for
# the thousands of intermediate files cmake/ninja produce.
#
# After the build, final artifacts (ELF, HEX, MAP) are extracted
# back to the host so flash and debug tools can access them.
# -----------------------------------------------------------------
def run_container_volume(cfg, command, interactive=False, build_dir=None):
    """Run a command with bind-mounted workspace + build-dir on a volume."""
    engine, warned = get_engine(cfg.engine)

    if warned:
        print("[WARN] Both Docker and Podman detected; using Docker")

    workspace = Path(west_topdir()).resolve()
    container_wd = _container_workdir(workspace)
    vol = _volume_name(workspace)
    _ensure_volume(engine, vol)

    # Container build path (posix)
    if build_dir:
        container_build = f"{CONTAINER_WORKDIR}/{build_dir.replace(chr(92), '/')}"
    else:
        container_build = f"{CONTAINER_WORKDIR}/build"

    args = [
        "run",
        "--rm",
        "-v", f"{workspace}:{CONTAINER_WORKDIR}",
        "-v", f"{vol}:{container_build}",
        "-w", container_wd,
        "-e", "PYTHONPATH=/work/modules/west-env",
    ]

    if interactive:
        args.append("-it")

    full_cmd = " ".join(command)
    args.append(cfg.image)
    args.extend([
        "sh",
        "-c",
        f"{_git_safe_dir_cmd()} && {_container_prep_cmd()} && exec {full_cmd}",
    ])

    engine.run(args)


def extract_artifacts(cfg, build_dir):
    """Copy final build artifacts from the volume back to the host."""
    engine, _ = get_engine(cfg.engine)
    workspace = Path(west_topdir()).resolve()
    vol = _volume_name(workspace)
    container_build = f"{CONTAINER_WORKDIR}/{build_dir.replace(chr(92), '/')}"

    # Ensure host build directory exists
    host_build = workspace / build_dir.replace("\\", "/")
    host_build.mkdir(parents=True, exist_ok=True)

    # Extract only the final artifacts (small, fast)
    artifact_globs = "zephyr/zephyr.elf zephyr/zephyr.hex zephyr/zephyr.bin zephyr/zephyr.map zephyr/.config"

    print(f"Extracting build artifacts ...")

    dump_cmd = [
        engine.name, "run", "--rm",
        "-v", f"{vol}:{container_build}",
        "-w", container_build,
        cfg.image,
        "sh", "-c",
        f"tar cf - {artifact_globs} 2>/dev/null",
    ]

    extract_cmd = ["tar", "xf", "-", "-C", str(host_build)]

    dump_proc = subprocess.Popen(dump_cmd, stdout=subprocess.PIPE)
    ext_proc = subprocess.Popen(extract_cmd, stdin=dump_proc.stdout)
    dump_proc.stdout.close()
    ext_proc.communicate()

    if ext_proc.returncode != 0:
        print("WARNING: artifact extraction may have been incomplete")
    else:
        print("Artifacts extracted.")


def check_container(cfg):
    try:
        engine, warned = get_engine(cfg.engine)
        subprocess.check_output([engine.name, "--version"])
        print(f"[PASS] container engine: {engine.name}")

        if warned:
            print("[WARN] both Docker and Podman detected")
            print("       using Docker by default")
            print("       consider setting engine explicitly")

    except Exception as e:
        print(f"[FAIL] container engine error: {e}")
        return False

    if not cfg.image:
        print("[FAIL] no container image configured")
        return False

    try:
        subprocess.check_output(
            [engine.name, "image", "inspect", cfg.image],
            stderr=subprocess.DEVNULL,
        )
        print(f"[PASS] container image available: {cfg.image}")
    except Exception:  # noqa
        print(f"[WARN] container image not present locally: {cfg.image}")
        print("       it will be pulled on first use")

    return True
