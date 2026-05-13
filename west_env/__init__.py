# SPDX-License-Identifier: Apache-2.0

try:
    from importlib.metadata import version as _pkg_version

    __version__ = _pkg_version("west-env")
except Exception:  # noqa
    __version__ = "0.1.0"
