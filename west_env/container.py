from pathlib import Path
import subprocess
from west.util import west_topdir
from west_env.engine import get_engine

CONTAINER_WORKDIR = "/work"


def run_container(cfg, command, interactive=False):
    engine, warned = get_engine(cfg.engine)

    if warned:
        print("[WARN] Both Docker and Podman detected; using Docker")

    workspace = Path(west_topdir()).resolve()
    mount_root = workspace.parent
    workspace_name = workspace.name

    container_workspace = f"{CONTAINER_WORKDIR}/{workspace_name}"

    host_cwd = Path.cwd().resolve()

    try:
        rel = host_cwd.relative_to(workspace)
        container_wd = f"{container_workspace}/{rel.as_posix()}"
    except ValueError:
        container_wd = container_workspace

    args = [
        "run",
        "--rm",
        "-v",
        f"{mount_root}:{CONTAINER_WORKDIR}",
        "-w",
        container_wd,
    ]

    if interactive:
        args += ["-it"]

    args.append(cfg.image)
    args += command

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
    except Exception:
        print(f"[WARN] container image not present locally: {cfg.image}")
        print("       it will be pulled on first use")

    return True
