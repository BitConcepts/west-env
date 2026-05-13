# SPDX-License-Identifier: Apache-2.0

import configparser
import sys
from pathlib import Path

import yaml


def _west_topdir():
    from west.util import west_topdir

    return west_topdir()


_VALID_BACKENDS = {
    "auto",
    "podman-machine-hyperv",
    "docker-desktop",
    "podman-native",
    "docker-native",
    "podman-machine",
    "docker-machine",
    # Legacy single-binary names still accepted
    "docker",
    "podman",
}

_VALID_WORKSPACE_MODES = {"sync", "copy", "tmpfs", "bind"}


class EnvConfig:
    """Parsed west-env.yml configuration.

    Supports both the legacy format (env.type / env.container.engine) and
    the new format (env.backend / env.workspace_mode / cache / git / jlink).
    Legacy fields are preserved so existing tests and code continue to work.
    """

    def __init__(self, data):
        data = data or {}
        env = data.get("env", {})

        # ------------------------------------------------------------------
        # Legacy fields (backward compat — engine.py era)
        # ------------------------------------------------------------------
        self.env_type = env.get("type", "native")
        _container_section = env.get("container", {})
        self.container = _container_section
        self.image = env.get("image") or _container_section.get("image")
        _old_engine = _container_section.get("engine", "docker")
        self.engine = _old_engine  # kept for backward compat

        # ------------------------------------------------------------------
        # New fields
        # ------------------------------------------------------------------
        # backend: new name takes priority; fall back to mapping old engine
        _raw_backend = env.get("backend", None)
        if _raw_backend is not None:
            self.backend = _raw_backend
        elif self.env_type == "native":
            self.backend = "auto"
        else:
            # Map old engine name to a new backend name
            self.backend = {
                "docker": "docker-native",
                "podman": "podman-native",
                "auto": "auto",
            }.get(_old_engine, _old_engine)

        # workspace_mode: new field; default is platform-aware
        _raw_mode = env.get("workspace_mode", None)
        if _raw_mode is not None:
            self.workspace_mode = _raw_mode
        else:
            # Legacy bind-mount behaviour preserved when old format used
            # New format gets platform-aware default
            if env.get("backend") is not None:
                self.workspace_mode = "sync" if sys.platform == "win32" else "bind"
            else:
                self.workspace_mode = "bind"

        # Cache sub-section
        _cache = data.get("cache", {})
        self.cache_ccache = bool(_cache.get("ccache", False))
        self.cache_modules = bool(_cache.get("modules", False))
        self.cache_sdk = bool(_cache.get("sdk", False))
        self.cache_pip = bool(_cache.get("pip", False))

        # Git credential sub-section
        _git = data.get("git", {})
        self.git_credential_helper = _git.get("credential_helper", "auto")

        # J-Link sub-section
        _jlink = data.get("jlink", {})
        self.jlink_mode = _jlink.get("mode", "host")

        # ------------------------------------------------------------------
        # Validation
        # ------------------------------------------------------------------
        if self.env_type not in {"native", "container"}:
            raise ValueError(f"unsupported env.type: {self.env_type}")

        if _old_engine not in {"auto", "docker", "podman"}:
            raise ValueError(f"unsupported env.container.engine: {_old_engine}")

        if self.backend not in _VALID_BACKENDS:
            raise ValueError(f"unsupported env.backend: {self.backend}")

        if self.workspace_mode not in _VALID_WORKSPACE_MODES:
            raise ValueError(f"unsupported env.workspace_mode: {self.workspace_mode}")

        if self.jlink_mode not in {"host", "tcp-server", "none"}:
            raise ValueError(f"unsupported jlink.mode: {self.jlink_mode}")


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
