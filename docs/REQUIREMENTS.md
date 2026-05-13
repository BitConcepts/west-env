# Requirements — west-env

Realigned 2026-05-13. 47 active requirements across 15 groups.
Retired requirements (REQ-ENGINE-*, REQ-CONTAINER-001, REQ-UTIL-002, REQ-CMD-001–005) are documented in docs/REALIGNMENT-REPORT.md and must not be reused.

---

## Platform (REQ-PLATFORM)

### REQ-PLATFORM-001
- **Component**: west_env.platform
- **Status**: Planned (Slice 6–7)
- **Description**: `west-env` supports Windows, Linux, and macOS as first-class host platforms. All actions are reachable from the host OS CLI without requiring WSL, SSH, or any Linux shell on the host.

### REQ-PLATFORM-002
- **Component**: west_env.platform
- **Status**: Planned (Slice 6–7)
- **Description**: Platform-native wrapper scripts are generated for every action. Windows generates `.ps1` PowerShell wrappers; Linux and macOS generate `.sh` shell wrappers.

### REQ-PLATFORM-003
- **Component**: west_env.platform
- **Status**: Planned (Slice 6–7)
- **Description**: Command semantics (argument names, exit codes, stdout format) are identical across platforms so documentation written for one OS applies to all others.

---

## Windows Native UX (REQ-WINNUX)

### REQ-WINNUX-001
- **Component**: west_env.vscode, west_env.platform
- **Status**: Planned (Slice 6, 8)
- **Description**: Windows developers use standard Windows VSCode. No VSCode Remote WSL extension is required or assumed for source editing or task execution.

### REQ-WINNUX-002
- **Component**: west_env.platform
- **Status**: Planned (Slice 6)
- **Description**: All `west env` actions are accessible via PowerShell wrappers. No Bash, WSL shell, or POSIX shell is required on the Windows host.

### REQ-WINNUX-003
- **Component**: west_env.platform, west_env.vscode
- **Status**: Planned (Slice 6, 8)
- **Description**: Source files are edited from the Windows filesystem (not from a WSL or container path). Sync (Layer 4) transfers them to the build environment.

### REQ-WINNUX-004
- **Component**: west_env.credentials
- **Status**: Planned (Slice 9)
- **Description**: Windows Git credentials (SSH keys, HTTPS credential manager) that already work in PowerShell continue to work without reconfiguration inside the build container.

---

## Windows Performance (REQ-WINPERF)

### REQ-WINPERF-001
- **Component**: west_env.sync, west_env.backend
- **Status**: Planned (Slice 2, 3)
- **Description**: The default Windows build workspace is a Linux ext4 volume inside a Podman Hyper-V VM (or equivalent). Direct `C:\...` bind mounts into a Linux container are not the default.

### REQ-WINPERF-002
- **Component**: west_env.backend
- **Status**: Planned (Slice 2)
- **Description**: On Windows, Podman machine backed by Hyper-V (`podman-machine-hyperv`) is the recommended backend when Hyper-V is available and enabled.

### REQ-WINPERF-003
- **Component**: west_env.backend, west_env.sync
- **Status**: Planned (Slice 2, 3)
- **Description**: When Docker Desktop (WSL2 bind mount) is the only available backend on Windows, `west env doctor` emits a clear performance warning and documents the recommended alternative.

### REQ-WINPERF-004
- **Component**: west_env.platform
- **Status**: Planned (Slice 11)
- **Description**: `west env benchmark` records build time, machine specs, and workspace mode. Results are stored locally for comparison.

---

## Workspace Synchronization (REQ-WORKSPACE)

### REQ-WORKSPACE-001
- **Component**: west_env.sync
- **Status**: Planned (Slice 3)
- **Description**: `west env sync` transfers source files from the host into the container/VM workspace. Generated directories (`build/`, `.cache/`, SDK downloads) are excluded from the source sync by default.

### REQ-WORKSPACE-002
- **Component**: west_env.sync
- **Status**: Planned (Slice 3)
- **Description**: `west env sync --back` (or equivalent artifact sync) transfers build outputs (`.elf`, `.bin`, `.hex`, `.map`) from the container/VM back to the host.

### REQ-WORKSPACE-003
- **Component**: west_env.sync
- **Status**: Planned (Slice 3)
- **Description**: Sync exclusion patterns are configurable in `west-env.yml` and default-exclude: `build/`, `.cache/`, `twister-out/`, `.west/`, and any directory matching `*.egg-info`.

### REQ-WORKSPACE-004
- **Component**: west_env.sync
- **Status**: Planned (Slice 3)
- **Description**: Workspace sync state is inspectable (`west env sync --status`) and recoverable (re-running sync is idempotent and non-destructive to source files).

---

## Cache (REQ-CACHE)

### REQ-CACHE-001
- **Component**: west_env.cache
- **Status**: Planned (Slice 5)
- **Description**: ccache is persisted in a named Docker/Podman volume that survives container recreation. Cache is automatically mounted when `cache.ccache: true` in `west-env.yml`.

### REQ-CACHE-002
- **Component**: west_env.cache
- **Status**: Planned (Slice 5)
- **Description**: The west module cache (`.west/`, Zephyr modules) is persisted in a named volume when `cache.modules: true`, avoiding repeated `west update` downloads.

### REQ-CACHE-003
- **Component**: west_env.cache
- **Status**: Planned (Slice 5)
- **Description**: Zephyr SDK and pip package caches are persisted in named volumes where applicable, avoiding re-download on clean container runs.

### REQ-CACHE-004
- **Component**: west_env.cache
- **Status**: Planned (Slice 5)
- **Description**: `west env cache stats` reports volume sizes and hit rates (ccache). `west env cache reset [--all | --ccache | --modules]` prunes the selected volume(s).

---

## Git Credentials (REQ-GIT)

### REQ-GIT-001
- **Component**: west_env.credentials
- **Status**: Planned (Slice 9)
- **Description**: Host Git credentials are forwarded into the build container. No tokens, keys, or credential files are copied into container images.

### REQ-GIT-002
- **Component**: west_env.credentials
- **Status**: Planned (Slice 9)
- **Description**: On Windows, the Windows OpenSSH agent (`ssh-agent` service or `pageant`-compatible socket) is forwarded into the container so SSH-based Git operations work without re-entering credentials.

### REQ-GIT-003
- **Component**: west_env.credentials
- **Status**: Planned (Slice 9)
- **Description**: When SSH agent forwarding is unavailable, HTTPS credential-manager delegation is documented and configurable (`git.credential_helper: credential-manager` in `west-env.yml`).

### REQ-GIT-004
- **Component**: west_env.credentials
- **Status**: Planned (Slice 9)
- **Description**: `west env doctor` reports the active credential strategy and whether it successfully authenticates (dry-run `git ls-remote` on a configured test URL if provided).

---

## J-Link / Flash (REQ-JLINK)

### REQ-JLINK-001
- **Component**: west_env.flash
- **Status**: Planned (Slice 10)
- **Description**: On Windows, the default flash path uses Windows-native SEGGER J-Link tools operating on build artifacts synced to a Windows path by Layer 4. No USB passthrough into the container is required.

### REQ-JLINK-002
- **Component**: west_env.flash, west_env.sync
- **Status**: Planned (Slice 10)
- **Description**: `west env flash` ensures build artifacts are synced to the host before invoking the host J-Link tool. Sync-back is automatic when `workspace_mode` is `sync` or `copy`.

### REQ-JLINK-003
- **Component**: west_env.flash
- **Status**: Planned (Slice 10)
- **Description**: USB device passthrough into the container is not required for the default flash path. The architecture explicitly avoids this dependency on Windows.

### REQ-JLINK-004
- **Component**: west_env.flash
- **Status**: Planned (Slice 10)
- **Description**: An optional TCP J-Link/GDB server mode is supported (`jlink.mode: tcp-server`) for container-side debugging via a J-Link GDB server running on the Windows host.

---

## VSCode Integration (REQ-VSCODE)

### REQ-VSCODE-001
- **Component**: west_env.vscode
- **Status**: Planned (Slice 8)
- **Description**: `west env generate-tasks` produces a `.vscode/tasks.json` with tasks for: setup, sync, build, flash, debug, benchmark. Tasks call the platform wrapper scripts.

### REQ-VSCODE-002
- **Component**: west_env.vscode
- **Status**: Planned (Slice 8)
- **Description**: On Windows, generated VSCode tasks invoke PowerShell wrappers (`.ps1`). No task uses `bash`, `sh`, or WSL paths.

### REQ-VSCODE-003
- **Component**: west_env.vscode
- **Status**: Planned (Slice 8)
- **Description**: On Linux and macOS, generated VSCode tasks invoke shell wrappers (`.sh`). Task definitions are structurally identical to Windows tasks, differing only in the wrapper path.

### REQ-VSCODE-004
- **Component**: west_env.vscode
- **Status**: Planned (Slice 8)
- **Description**: No generated task assumes or requires the VSCode Remote WSL extension. All tasks run in the host terminal profile.

---

## Backend Detection (REQ-BACKEND)

### REQ-BACKEND-001
- **Component**: west_env.backend
- **Status**: Planned (Slice 2)
- **Description**: The backend detector probes for all supported backends: `docker`, `podman`, `podman machine`, and `docker-desktop`. It reports availability, version, and any constraints (e.g. Hyper-V enabled, WSL2 present).

### REQ-BACKEND-002
- **Component**: west_env.backend
- **Status**: Planned (Slice 2)
- **Description**: On Windows, the detector checks whether Hyper-V is enabled (via `Get-WindowsOptionalFeature` or equivalent) to determine if `podman-machine-hyperv` is viable.

### REQ-BACKEND-003
- **Component**: west_env.backend, west_commands.env
- **Status**: Planned (Slice 2)
- **Description**: `west env doctor` prints the detected backend, the selection rationale, any fallbacks skipped, and actionable remediation for each issue found.

### REQ-BACKEND-004
- **Component**: west_env.backend
- **Status**: Planned (Slice 2)
- **Description**: The backend fallback chain on Windows is: `podman-machine-hyperv` → `docker-desktop` → `bind` (with warning). On Linux: `podman-native` → `docker-native`. On macOS: `podman-machine` → `docker-machine`.

---

## Testability (REQ-TESTABILITY)

### REQ-TESTABILITY-001
- **Component**: docs/TESTS.md
- **Status**: Active (governance)
- **Description**: Every active requirement maps to at least one test entry in `docs/TESTS.md`. Tests may be automated (pytest/CI) or manual with documented steps and expected results.

### REQ-TESTABILITY-002
- **Component**: docs/TESTS.md
- **Status**: Active (governance)
- **Description**: Manual tests include: exact pre-conditions, step-by-step instructions, expected output or observable behaviour, and pass/fail criteria.

### REQ-TESTABILITY-003
- **Component**: docs/TESTS.md
- **Status**: Active (governance)
- **Description**: Performance tests (`west env benchmark`) record: machine model, OS, backend, workspace mode, Zephyr revision, and wall-clock build time. Results are stored in `docs/benchmarks/`.

---

## Config (REQ-CONFIG) — retained/modified

### REQ-CONFIG-001
- **Component**: west_env.config
- **Status**: Implemented
- **Description**: `find_config_path()` resolves the `west-env.yml` path from the manifest directory declared in `.west/config`, not from the current working directory.

### REQ-CONFIG-002
- **Component**: west_env.config
- **Status**: Planned (Slice 2 — extended)
- **Description**: `EnvConfig` parses `env.backend` (selecting from the supported backend identifiers) and `env.workspace_mode` (`sync` | `copy` | `tmpfs` | `bind`). Unknown values raise `ValueError`.

### REQ-CONFIG-003
- **Component**: west_env.config
- **Status**: Planned (Slice 2 — extended)
- **Description**: `EnvConfig` parses `cache`, `git`, and `jlink` sub-sections. Unknown top-level keys raise `ValueError`.

### REQ-CONFIG-004
- **Component**: west_env.config
- **Status**: Planned (Slice 2 — extended)
- **Description**: When `west-env.yml` is absent or empty, `load_config()` returns platform-aware defaults: `backend="auto"`, `workspace_mode="sync"` on Windows and `"bind"` on Linux/macOS, `image=None`.

---

## Container Execution (REQ-CONTAINER) — retained

### REQ-CONTAINER-002
- **Component**: west_env.container
- **Status**: Implemented
- **Description**: All command arguments are shell-quoted via `shlex.join` before being passed to `sh -c`, so paths and names containing spaces are handled correctly.

### REQ-CONTAINER-003
- **Component**: west_env.container
- **Status**: Implemented
- **Description**: Before running any command, the container layer executes `git config --global safe.directory '*'` inside the container so that Zephyr west extensions load under Git >= 2.35.

---

## Utilities (REQ-UTIL) — retained

### REQ-UTIL-001
- **Component**: west_env.util
- **Status**: Implemented
- **Description**: `check_python()` enforces a minimum Python version of 3.10 and prints a `[PASS]` or `[FAIL]` diagnostic.

---

## Command Validation (REQ-CMD) — partially retained

### REQ-CMD-006
- **Component**: west_commands.env
- **Status**: Implemented
- **Description**: `validate_workspace_layout()` asserts that `.west/` exists and the configured manifest file is present before any container operation; exits with a descriptive `FATAL` message on failure.

---

## Build (REQ-BUILD)

### REQ-BUILD-001
- **Build system**: pyproject / setuptools
- **Status**: Implemented
- **Description**: The package installs via `pip install -e ".[test]"` and all unit tests pass via `pytest tests/`.

