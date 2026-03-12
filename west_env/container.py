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
        rel_posix = rel.as_posix()
        # rel_posix is '.' when cwd equals the workspace root; avoid '/work/.'
        container_wd = (
            CONTAINER_WORKDIR
            if rel_posix == "."
            else f"{CONTAINER_WORKDIR}/{rel_posix}"
        )
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
    # Git >= 2.35 refuses to operate on bind-mounted repos
    # owned by a different uid (common in Docker) unless
    # the directory is explicitly marked safe.
    #
    # We use the '*' wildcard to cover the entire workspace
    # tree regardless of how the user has named and placed
    # their Zephyr project path in west.yml.  A hardcoded
    # path such as '/work/zephyr' breaks any project whose
    # zephyr/ directory is already taken by a Zephyr module
    # integration directory (zephyr/module.yml), forcing
    # them to use an alternate path (e.g. deps/zephyr).
    #
    # Using '*' is intentional and safe: the container is
    # already a trust boundary.
    # -------------------------------------------------
    git_prep = "git config --global safe.directory '*'"

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
