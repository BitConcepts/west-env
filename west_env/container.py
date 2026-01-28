# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import subprocess
from west.util import west_topdir
from west_env.engine import get_engine

CONTAINER_WORKDIR = "/work"


def run_container(cfg, command, interactive=False):
    engine, warned = get_engine(cfg.engine)

    if warned:
        print("[WARN] Both Docker and Podman detected; using Docker")

    # Canonical west topdir (directory containing .west/)
    workspace = Path(west_topdir()).resolve()

    # Host cwd (perhaps inside the workspace)
    host_cwd = Path.cwd().resolve()

    try:
        rel = host_cwd.relative_to(workspace)
        container_wd = f"{CONTAINER_WORKDIR}/{rel.as_posix()}"
    except ValueError:
        container_wd = CONTAINER_WORKDIR

    # -------------------------------------------------
    # Prepare container invocation
    # -------------------------------------------------
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

    # -------------------------------------------------
    # Git safety + command execution
    #
    # Git >= 2.35 refuses to operate on mounted repos
    # unless explicitly marked safe. If this step is
    # missing, Zephyr west extension commands (build,
    # flash, etc.) will NOT load.
    # -------------------------------------------------
    git_prep = (
        "git config --global --add safe.directory /work && "
        "git config --global --add safe.directory /work/zephyr"
    )

    full_cmd = " ".join(command)

    args.append(cfg.image)
    args.extend([
        "sh",
        "-c",
        f"{git_prep} && exec {full_cmd}",
    ])

    engine.run(args)


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
