# SPDX-License-Identifier: Apache-2.0

import subprocess
from shutil import which


class ContainerEngine:
    def __init__(self, name):
        self.name = name

    def run(self, args):
        subprocess.check_call([self.name] + args)


def engine_available(name):
    return which(name) is not None


def detect_engine(preferred=None):
    docker = engine_available("docker")
    podman = engine_available("podman")

    if preferred and preferred != "auto":
        if not engine_available(preferred):
            raise RuntimeError(f"Requested engine not available: {preferred}")
        return preferred, False

    if docker and podman:
        return "docker", True

    if docker:
        return "docker", False

    if podman:
        return "podman", False

    raise RuntimeError("No supported container engine found")


def get_engine(cfg_engine):
    name, warned = detect_engine(cfg_engine)
    return ContainerEngine(name), warned
