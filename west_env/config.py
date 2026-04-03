# SPDX-License-Identifier: Apache-2.0

import configparser
from pathlib import Path

import yaml


def _west_topdir():
    from west.util import west_topdir
    return west_topdir()

class EnvConfig:
    def __init__(self, data):
        data = data or {}
        env = data.get("env", {})

        self.env_type = env.get("type", "native")
        self.container = env.get("container", {})
        self.image = self.container.get("image")
        self.engine = self.container.get("engine", "docker")

        if self.env_type not in {"native", "container"}:
            raise ValueError(f"unsupported env.type: {self.env_type}")

        if self.engine not in {"auto", "docker", "podman"}:
            raise ValueError(
                f"unsupported env.container.engine: {self.engine}"
            )


def find_config_path(topdir=None):
    if topdir is None:
        topdir_path = Path(_west_topdir()).resolve()
    else:
        topdir_path = Path(topdir).resolve()

    cfg_path = topdir_path / ".west" / "config"
    cp = configparser.ConfigParser()
    cp.read(cfg_path)

    manifest_path = cp.get("manifest", "path", fallback=".")
    manifest_dir = (topdir_path / manifest_path).resolve()
    return manifest_dir / "west-env.yml"


def load_config(topdir=None):
    path = find_config_path(topdir)
    if not path.exists():
        return EnvConfig({})

    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return EnvConfig(data)
