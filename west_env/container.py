from pathlib import Path
import subprocess
from west.util import west_topdir
from west_env.engine import get_engine

CONTAINER_WORKDIR = "/work"


def run_container(cfg, command, interactive=False):
    engine, warned = get_engine(cfg.engine)

    if warned:
        print("[WARN] Both Docker and Podman detected; using Docker")
        print("       Set engine explicitly in west-env.yml to silence this warning")

    host_topdir = Path(west_topdir()).resolve()
    host_cwd = Path.cwd().resolve()

    try:
        rel_cwd = host_cwd.relative_to(host_topdir)
        container_wd = f"{CONTAINER_WORKDIR}/{rel_cwd.as_posix()}"
    except ValueError:
        container_wd = CONTAINER_WORKDIR

    args = [
        "run",
        "--rm",
        "-v",
        f"{host_topdir}:{CONTAINER_WORKDIR}",
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
