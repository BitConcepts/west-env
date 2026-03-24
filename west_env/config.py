# SPDX-License-Identifier: Apache-2.0

import yaml
from pathlib import Path


class EnvConfig:
    def __init__(self, data):
        self.env_type = data.get("env", {}).get("type", "native")
        self.container = data.get("env", {}).get("container", {})

        self.image = self.container.get("image")
        self.engine = self.container.get("engine", "docker")

        # "bind" (default) or "volume" (sync-build-extract for Windows perf)
        self.sync_mode = self.container.get("sync_mode", "bind")

        # Optional build directory (relative to west topdir)
        build = data.get("env", {}).get("build", {})
        self.build_dir = build.get("dir")  # e.g. "build"


def load_config():
    path = Path("west-env.yml")
    if not path.exists():
        return EnvConfig({})

    with path.open() as f:
        data = yaml.safe_load(f)

    return EnvConfig(data)
