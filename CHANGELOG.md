# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-05-13

Initial release of `west-env` — a cross-platform Zephyr RTOS developer
environment manager. Builds run in Linux containers or VMs; developers edit,
flash, and debug from their host OS without WSL, Remote SSH, or slow bind-mount
builds.

### Added

#### Core infrastructure
- `west env` west extension command with actions: `init`, `build`, `shell`,
  `doctor`, `sync`, `flash`, `debug`, `cache`, `benchmark`, `generate-tasks`,
  `version`
- `west-env.yml` manifest-local configuration (resolves from manifest directory,
  not CWD). Supports both legacy (`env.type`/`env.container.*`) and new
  (`env.backend`, `env.workspace_mode`, `cache.*`, `git.*`, `jlink.*`) formats
- `__version__` attribute in `west_env` package (readable via
  `importlib.metadata` and `west env version`)

#### Platform support (Windows / Linux / macOS)
- Six-backend auto-detector (`west_env.backend`):
  `podman-machine-hyperv`, `docker-desktop`, `podman-native`,
  `docker-native`, `podman-machine`, `docker-machine`
- Platform-aware fallback chain: Podman Hyper-V → Docker Desktop (Windows);
  Podman native → Docker native (Linux); Podman machine → Docker Desktop
  (macOS)
- Hyper-V availability check via PowerShell on Windows
- Platform-native wrapper script generator (`west_env.platform`): `.ps1`
  on Windows (no Bash, no WSL), `.sh` on Linux/macOS
- `west env generate-tasks` writes `.vscode/tasks.json` with no Remote WSL
  dependency (`west_env.vscode`)

#### Workspace synchronisation (`west_env.sync`)
- Four workspace modes: `sync` (rsync to VM ext4 — Windows default), `copy`,
  `tmpfs`, `bind`
- Bind mount on Windows emits `SyncWarning` (NTFS→Linux overhead)
- Source-only sync with configurable exclusion patterns (`build/`, `.cache/`,
  `twister-out/`, `.west/`, `*.egg-info`)
- `west env sync --back` syncs build artifacts (`.elf`, `.bin`, `.hex`, `.map`)
  back to host

#### Build safety (`west_env.buildcheck`)
- Stale build directory detection via `CMakeCache.txt` `CMAKE_SOURCE_DIR`
- `west env build` warns with `[WARN]` and exits 1 if mode switched (native
  ↔ container) without cleaning
- `--clean` flag auto-removes stale `build/` before proceeding

#### Cache management (`west_env.cache`)
- Persistent named volumes for ccache, west modules, Zephyr SDK, pip
- `west env cache stats` — volume sizes and ccache hit rate
- `west env cache reset [--ccache | --modules]` — targeted volume pruning
- `CCACHE_DIR` environment variable forwarded into container

#### Git credential forwarding (`west_env.credentials`)
- Windows OpenSSH agent socket forwarded via `SSH_AUTH_SOCK`
- HTTPS Git Credential Manager fallback detection
- `west env doctor` reports active credential strategy
- No tokens, keys, or credential files copied into container images
- `PYTHONDONTWRITEBYTECODE=1` set in all container invocations, preventing
  root-owned `__pycache__` in mounted workspace volumes

#### Flash and debug (`west_env.flash`)
- Windows-native J-Link host flash (`jlink.mode: host`): build artifacts
  synced to Windows path, flashed with Windows J-Link tools — no USB
  passthrough required
- Optional TCP J-Link/GDB server mode (`jlink.mode: tcp-server`) for
  container-side GDB sessions
- J-Link search paths: Windows `C:\Program Files\SEGGER\JLink`, Linux
  `/opt/SEGGER/JLink`, macOS `/Applications/SEGGER/JLink`
- `west env doctor` reports J-Link availability

#### Benchmarking
- `west env benchmark`: timed build with JSON output to `docs/benchmarks/`
  recording machine, OS, Python version, backend, workspace mode, and
  elapsed seconds

#### CI / testing
- CI matrix: lint (ruff), unit tests (Windows / Linux / macOS ×
  Python 3.10 / 3.11 / 3.12), Docker integration, Podman integration,
  native-sim Zephyr build, pip-audit security scan
- 141 unit tests across all platforms
- `tests/test_backend.py` — 6-backend detector unit tests
- `tests/test_sync.py` — workspace sync and exclusion tests
- `tests/test_new_modules.py` — cache, credentials, VSCode, platform, flash
- `tests/test_buildcheck.py` — 18 stale build detection tests
- `tests/test_podman_integration.py` — Podman rootless integration tests
  (ubuntu CI)
- macOS backend detection smoke test in unit-tests matrix
- Dependabot: pip and GitHub Actions weekly updates
- `pip-audit` security scan on every push

#### Documentation
- `docs/ARCHITECTURE.md` — 8-layer architecture, 3 platforms, 6 backends,
  4 workspace modes
- `docs/REQUIREMENTS.md` — 47+ active requirements across 15 groups
- `docs/TESTS.md` — full test matrix with requirement traceability
- `docs/FEATURE-PLAN.md` — 12 vertical implementation slices
- `docs/REALIGNMENT-REPORT.md` — requirement migration history
- `docs/quickstart-windows.md`, `docs/quickstart-linux.md`,
  `docs/quickstart-macos.md`
- `docs/git-credentials.md`, `docs/flashing.md`, `docs/troubleshooting.md`
- `CONTRIBUTING.md`, `SECURITY.md` (expanded)

### Changed

- `west env doctor` extended: backend detection report, credential strategy,
  J-Link status, version header
- `west env build` now checks for stale CMake build directories (mode
  mismatch) before running
- Configuration schema extended with `backend`, `workspace_mode`, `cache`,
  `git`, `jlink` top-level sections; fully backward-compatible with legacy
  `env.type` / `env.container.*` format
- README rewritten: Windows-first framing, accurate platform table, no stale
  WSL build claims, all current commands documented

### Removed

- EDSSharp / CANopenEditor bind-mount from container invocation (was
  project-specific; not appropriate for a general-purpose tool)

### Fixed

- Container invocations set `PYTHONDONTWRITEBYTECODE=1` preventing root-owned
  `__pycache__` files in the workspace volume (caused `PermissionError` on
  Docker CI test cleanup)
- `dev-release.yml` broken `sed` version extraction replaced with Python
  `tomllib` parsing
- Docker/Podman e2e tests use `ignore_cleanup_errors=True` on
  `TemporaryDirectory` for robustness against root-owned cleanup remnants

### Security

- No tokens, SSH keys, or credential files are ever written into container
  images or volume mounts
- `pip-audit` runs on every push; Dependabot monitors PyPI and Actions weekly

[Unreleased]: https://github.com/BitConcepts/west-env/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/BitConcepts/west-env/releases/tag/v0.1.0
