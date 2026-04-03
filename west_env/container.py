# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import shlex
import subprocess

from west_env.engine import get_engine

CONTAINER_WORKDIR = "/work"


def _west_topdir():
    from west.util import west_topdir
    return west_topdir()


def _container_workdir(workspace, host_cwd):
    try:
        rel = host_cwd.relative_to(workspace)
        return f"{CONTAINER_WORKDIR}/{rel.as_posix()}"
    except ValueError:
        return CONTAINER_WORKDIR


def _container_args(
    cfg, command, interactive=False, workspace=None, host_cwd=None
):
    if not cfg.image:
        raise RuntimeError("no container image configured")

    engine, warned = get_engine(cfg.engine)

    # Canonical west topdir (directory containing .west/)
    workspace = Path(workspace or _west_topdir()).resolve()

    # Host cwd (perhaps inside the workspace)
    host_cwd = Path(host_cwd or Path.cwd()).resolve()
    container_wd = _container_workdir(workspace, host_cwd)

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
    ]

    if interactive:
        args.extend(["-i", "-t"])

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
    full_cmd = shlex.join(command)

    args.append(cfg.image)
    args.extend([
        "sh",
        "-c",
        f"{git_prep} && exec {full_cmd}",
    ])
    return engine, warned, args


def run_container(cfg, command, interactive=False):
    engine, warned, args = _container_args(
        cfg, command, interactive=interactive
    )

    if warned:
        print("[WARN] Both Docker and Podman detected; using Docker")

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


def check_container_workspace(cfg, workspace, manifest_rel):
    quoted_manifest = shlex.quote(manifest_rel)
    command = [
        "sh",
        "-c",
        f"test -d .west && test -f {quoted_manifest}",
    ]

    engine, _, args = _container_args(
        cfg,
        command,
        workspace=workspace,
        host_cwd=workspace,
    )
    subprocess.check_output(
        [engine.name] + args,
        stderr=subprocess.DEVNULL,
    )
