from pathlib import Path
import subprocess
from west_env.engine import get_engine

def run_container(cfg, command, interactive=False):
    engine, warned = get_engine(cfg.engine)

    if warned:
        print("[WARN] Both Docker and Podman detected; using Docker")
        print("       Set engine explicitly in west-env.yml to silence this warning")

    workdir = Path.cwd()

    args = [
        "run", "--rm",
        "-v", f"{workdir}:{workdir}",
        "-w", str(workdir),
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
