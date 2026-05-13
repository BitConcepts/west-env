# SPDX-License-Identifier: Apache-2.0
"""VSCode tasks.json generator for west-env.

Generates .vscode/tasks.json with tasks for:
  setup          Initialize the environment and backend.
  sync           Sync source files to container/VM workspace.
  build          Run west env build.
  sync-back      Sync build artifacts back to host.
  flash          Flash firmware using host tools.
  debug          Start debug session.
  cache-stats    Show cache volume stats.
  cache-reset    Reset all cache volumes.
  benchmark      Run benchmark build and record results.

Platform rules:
  Windows  → tasks invoke PowerShell wrappers (.ps1).  No bash/wsl paths.
  Linux    → tasks invoke shell wrappers (.sh).
  macOS    → tasks invoke shell wrappers (.sh).

No task assumes or requires VSCode Remote WSL.
All tasks use the "shell" type with the host terminal profile.
"""

import json
import sys
from pathlib import Path


# Wrapper file extensions per platform
_EXT = {
    "win32":  ".ps1",
    "darwin": ".sh",
    "linux":  ".sh",
}

# Shell invocation per platform
_SHELL = {
    "win32":  {"executable": "pwsh", "args": ["-NoProfile", "-File"]},
    "darwin": {"executable": "/bin/sh", "args": []},
    "linux":  {"executable": "/bin/sh", "args": []},
}

# Action definitions: (task_label, command_args, group, detail)
_ACTIONS = [
    ("west-env: setup",        ["setup"],                  "build",  "Initialize backend and workspace"),
    ("west-env: sync",         ["sync"],                   "build",  "Sync source files to container/VM"),
    ("west-env: build",        ["build"],                  "build",  "Build firmware in container"),
    ("west-env: sync-back",    ["sync", "--back"],         "build",  "Sync artifacts back to host"),
    ("west-env: flash",        ["flash"],                  None,     "Flash firmware with host J-Link"),
    ("west-env: debug",        ["debug"],                  None,     "Start debug session"),
    ("west-env: cache-stats",  ["cache", "stats"],         None,     "Show cache volume statistics"),
    ("west-env: cache-reset",  ["cache", "reset"],         None,     "Reset all cache volumes"),
    ("west-env: benchmark",    ["benchmark"],              None,     "Run benchmark build"),
]


def generate_tasks(
    project_root: Path,
    host_platform: str = None,
    scripts_dir: str = "scripts",
) -> dict:
    """Generate a tasks.json dict for the given project root and platform.

    Args:
        project_root: Absolute path to the west workspace root.
        host_platform: Override sys.platform ('win32'/'linux'/'darwin').
        scripts_dir: Directory (relative to project_root) containing wrappers.

    Returns:
        dict that can be written as .vscode/tasks.json.
    """
    plat = host_platform or sys.platform
    ext = _EXT.get(plat, ".sh")

    tasks = []
    for label, args, group, detail in _ACTIONS:
        # Wrapper script name: west-env-<action>.<ext>
        action_name = args[0]
        wrapper = f"{scripts_dir}/west-env-{action_name}{ext}"

        # Build command: on Windows use pwsh -File <wrapper> [args...]
        # On POSIX use sh <wrapper> [args...]
        if plat == "win32":
            command = wrapper
            task_args = args[1:] if len(args) > 1 else []
        else:
            command = wrapper
            task_args = args[1:] if len(args) > 1 else []

        task = {
            "label": label,
            "type": "shell",
            "command": command,
            "args": task_args,
            "options": {
                "cwd": "${workspaceFolder}",
            },
            "presentation": {
                "echo": True,
                "reveal": "always",
                "focus": False,
                "panel": "shared",
            },
        }

        if group == "build":
            task["group"] = {"kind": "build", "isDefault": label == "west-env: build"}

        if detail:
            task["detail"] = detail

        tasks.append(task)

    return {
        "version": "2.0.0",
        "_generated_by": "west-env generate-tasks",
        "_platform": plat,
        "tasks": tasks,
    }


def write_tasks(project_root: Path, host_platform: str = None, scripts_dir: str = "scripts"):
    """Write .vscode/tasks.json to project_root.

    Creates .vscode/ if it does not exist.
    """
    vscode_dir = project_root / ".vscode"
    vscode_dir.mkdir(parents=True, exist_ok=True)
    tasks_path = vscode_dir / "tasks.json"
    data = generate_tasks(project_root, host_platform=host_platform, scripts_dir=scripts_dir)
    tasks_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return tasks_path
