# Tests — west-env

Realigned 2026-05-13. Unit tests: `pytest tests/`. Integration: GitHub Actions CI. Manual: documented steps below.
Retired tests (TEST-ENGINE-*, TEST-CONTAINER-002/003, TEST-UTIL-001/002) are kept in this file for traceability but are no longer governance-active. The underlying test functions still execute in CI.

---

## Retained: Config Tests

### TEST-CONFIG-001
- **File**: tests/test_config.py — `ConfigTests.test_find_config_path_uses_manifest_directory`
- Covers: REQ-CONFIG-001
- **Status**: Passing

### TEST-CONFIG-002
- **File**: tests/test_config.py — `ConfigTests.test_load_config_reads_manifest_local_file_not_cwd`
- Covers: REQ-CONFIG-001, REQ-CONFIG-002, REQ-CONFIG-003
- **Status**: Passing
- **Note**: REQ-CONFIG-002/003 are extended in Slice 2; this test covers current (pre-extension) parse semantics.

### TEST-CONFIG-003
- **File**: tests/test_config.py — `ConfigTests.test_load_config_handles_empty_file`
- Covers: REQ-CONFIG-004
- **Status**: Passing
- **Note**: REQ-CONFIG-004 defaults will become platform-aware in Slice 2; test will be updated then.

## Retained: Container Tests

### TEST-CONTAINER-001
- **File**: tests/test_container.py — `ContainerTests.test_container_args_preserve_relative_cwd_and_quote_command`
- Covers: REQ-CONTAINER-002, REQ-CONTAINER-003
- **Status**: Passing

### TEST-CONTAINER-004
- **File**: tests/test_container.py — `ContainerTests.test_check_container_workspace_uses_selected_engine`
- Covers: REQ-CMD-006
- **Status**: Passing

### TEST-CONTAINER-005
- **File**: tests/test_container.py — `ContainerTests.test_check_container_workspace_uses_docker_when_configured`
- Covers: REQ-CMD-006
- **Status**: Passing

## Retained: Integration Tests (CI)

### TEST-BUILD-001
- **File**: .github/workflows/ci.yml — `unit-tests` job
- **Type**: integration
- Covers: REQ-BUILD-001, REQ-UTIL-001, REQ-TESTABILITY-001, REQ-TESTABILITY-002
- **Status**: CI

### TEST-BUILD-002
- **File**: .github/workflows/ci.yml — `native-sim-build` job
- **Type**: integration
- Covers: REQ-BUILD-001, REQ-UTIL-001
- **Status**: CI

---

## Retired Tests (traceability only — not governance-active)

These tests still execute in CI but their requirement targets are retired. They will be superseded in the slices noted.

### TEST-ENGINE-001 through TEST-ENGINE-006
- **File**: tests/test_engine.py
- Covers: REQ-CMD-001
- **Status**: Passing (CI); formerly covered REQ-ENGINE-001/002/003 (RETIRED); superseded by TEST-BACKEND-* in Slice 2

### TEST-CONTAINER-002
- **File**: tests/test_container.py — `ContainerTests.test_container_args_use_workspace_root_when_cwd_is_outside_workspace`
- Covers: REQ-CONTAINER-001
- **Status**: Passing (CI); REQ-CONTAINER-001 RETIRED; superseded by TEST-WORKSPACE-* in Slice 3

### TEST-CONTAINER-003
- **File**: tests/test_container.py — `ContainerTests.test_run_container_uses_detected_engine`
- Covers: REQ-UTIL-002
- **Status**: Passing (CI); REQ-UTIL-002 RETIRED; superseded by TEST-PLATFORM-* in Slice 6–7

### TEST-UTIL-001 / TEST-UTIL-002
- **File**: tests/test_util.py
- Covers: REQ-UTIL-002
- **Status**: Passing (CI); REQ-UTIL-002 RETIRED; superseded by TEST-PLATFORM-* in Slice 6–7

---

## New Test Stubs — Slice 2: Backend Detection

### TEST-BACKEND-001
- **Type**: unit
- Covers: REQ-BACKEND-001
- **Status**: TODO (Slice 2)
- **Steps**: Mock `which`, `subprocess` for all 6 backend probes. Assert detector returns correct backend type and version string for each combination.

### TEST-BACKEND-002
- **Type**: unit (Windows-only)
- Covers: REQ-BACKEND-002
- **Status**: TODO (Slice 2)
- **Steps**: Mock `Get-WindowsOptionalFeature` output. Assert detector identifies Hyper-V enabled/disabled correctly and selects or skips `podman-machine-hyperv`.

### TEST-BACKEND-003
- **Type**: manual + unit
- Covers: REQ-BACKEND-003, REQ-WINPERF-003
- **Status**: TODO (Slice 2)
- **Steps**: Run `west env doctor` with only Docker Desktop available on Windows. Verify output contains performance warning and recommendation for Podman Hyper-V.

### TEST-BACKEND-004
- **Type**: unit
- Covers: REQ-BACKEND-004
- **Status**: TODO (Slice 2)
- **Steps**: Parametrize backend availability combinations per platform. Assert fallback chain produces the correct ordered selection with/without warnings.

---

## New Test Stubs — Slice 3: Workspace Sync

### TEST-WORKSPACE-001
- **Type**: unit
- Covers: REQ-WORKSPACE-001, REQ-WORKSPACE-003
- **Status**: TODO (Slice 3)
- **Steps**: Create temp workspace with `build/`, `.cache/`, source files. Run `sync`. Assert source files transferred and excluded dirs not present in destination.

### TEST-WORKSPACE-002
- **Type**: unit
- Covers: REQ-WORKSPACE-002
- **Status**: TODO (Slice 3)
- **Steps**: Populate container/VM build dir with `.elf`, `.bin`, `.hex` files. Run `sync --back`. Assert artifacts appear in host output directory.

### TEST-WORKSPACE-003
- **Type**: unit
- Covers: REQ-WORKSPACE-003
- **Status**: TODO (Slice 3)
- **Steps**: Configure custom exclusion pattern in `west-env.yml`. Assert the custom pattern is excluded and a non-matching file is transferred.

### TEST-WORKSPACE-004
- **Type**: unit
- Covers: REQ-WORKSPACE-004
- **Status**: TODO (Slice 3)
- **Steps**: Run `west env sync --status`. Assert idempotency by running twice. Assert second run does not modify existing synced files.

---

## New Test Stubs — Slice 5: Cache

### TEST-CACHE-001
- **Type**: integration (requires backend)
- Covers: REQ-CACHE-001
- **Status**: TODO (Slice 5)
- **Steps**: Run two builds with `cache.ccache: true`. Assert ccache volume exists after first build. Assert second build shows cache hit rate > 0%.

### TEST-CACHE-002
- **Type**: integration
- Covers: REQ-CACHE-002
- **Status**: TODO (Slice 5)
- **Steps**: Run `west env sync` followed by `west update` inside container with `cache.modules: true`. Assert west module volume persists between container restarts.

### TEST-CACHE-003
- **Type**: integration
- Covers: REQ-CACHE-003
- **Status**: TODO (Slice 5)
- **Steps**: Run `west env build` twice with SDK cache enabled. Assert SDK is not re-downloaded on second run.

### TEST-CACHE-004
- **Type**: unit + manual
- Covers: REQ-CACHE-004
- **Status**: TODO (Slice 5)
- **Steps**: Run `west env cache stats`. Assert output includes volume name, size, and ccache hit rate. Run `west env cache reset --ccache`. Assert ccache volume is cleared.

---

## New Test Stubs — Slice 6/7: Platform Wrappers

### TEST-PLATFORM-001
- **Type**: unit
- Covers: REQ-PLATFORM-001, REQ-PLATFORM-002
- **Status**: TODO (Slice 6–7)
- **Steps**: On each platform (Windows CI, Linux CI, macOS CI), assert that generated wrappers exist with the correct extension (`.ps1` / `.sh`) and are executable.

### TEST-PLATFORM-002
- **Type**: unit
- Covers: REQ-PLATFORM-003
- **Status**: TODO (Slice 6–7)
- **Steps**: Assert that `--help` output of each action is identical across platforms (same argument names, same exit codes for success/failure).

### TEST-WINNUX-001
- **Type**: manual (Windows)
- Covers: REQ-WINNUX-001, REQ-WINNUX-002
- **Status**: TODO (Slice 6)
- **Pre-conditions**: Windows host, PowerShell 7, VSCode installed (no Remote WSL extension).
- **Steps**: Open VSCode. Run `west env build` from PowerShell terminal. Verify build completes without invoking WSL or Bash.
- **Pass**: Build succeeds; no `wsl`, `bash`, or `/usr/bin/` paths appear in terminal output.

### TEST-WINNUX-002
- **Type**: manual (Windows)
- Covers: REQ-WINNUX-003, REQ-WINNUX-004
- **Status**: TODO (Slice 9)
- **Pre-conditions**: Windows host, SSH key registered with Windows OpenSSH agent, private Zephyr repo.
- **Steps**: Run `west update` inside container via `west env sync && west env build`. Verify Git clones succeed using Windows SSH credentials.
- **Pass**: `west update` succeeds; no password prompt; no credential file copied into container.

---

## New Test Stubs — Slice 8: VSCode Tasks

### TEST-VSCODE-001
- **Type**: unit
- Covers: REQ-VSCODE-001, REQ-VSCODE-002, REQ-VSCODE-003, REQ-VSCODE-004
- **Status**: TODO (Slice 8)
- **Steps**: Run `west env generate-tasks` on each platform. Assert `.vscode/tasks.json` is created. On Windows, assert no task contains `bash`, `sh`, or `wsl`. On Linux/macOS, assert tasks contain `.sh` paths.

---

## New Test Stubs — Slice 9: Git Credentials

### TEST-GIT-001
- **Type**: manual (Windows)
- Covers: REQ-GIT-001, REQ-GIT-002
- **Status**: TODO (Slice 9)
- **Pre-conditions**: Windows OpenSSH agent running with SSH key loaded. Private Zephyr module hosted on SSH remote.
- **Steps**: Run `west env build` (which executes `west update` inside container). Verify SSH authentication succeeds using forwarded agent socket.
- **Pass**: `git clone` inside container succeeds; no private key file appears inside container image.

### TEST-GIT-002
- **Type**: unit
- Covers: REQ-GIT-003, REQ-GIT-004
- **Status**: TODO (Slice 9)
- **Steps**: Mock credential-manager config. Run `west env doctor`. Assert output identifies credential strategy and reports pass/fail for authentication dry-run.

---

## New Test Stubs — Slice 10: J-Link / Flash

### TEST-JLINK-001
- **Type**: manual (Windows + hardware)
- Covers: REQ-JLINK-001, REQ-JLINK-002, REQ-JLINK-003
- **Status**: TODO (Slice 10)
- **Pre-conditions**: Windows host, J-Link for Windows installed, target board connected via USB J-Link.
- **Steps**: Run `west env build`, then `west env flash`. Verify artifact sync-back runs, then `JLinkExe` is invoked on the Windows-side `.hex` file.
- **Pass**: Board flashed successfully. No USB device passthrough configuration required.

### TEST-JLINK-002
- **Type**: manual (Windows)
- Covers: REQ-JLINK-004
- **Status**: TODO (Slice 10)
- **Steps**: Configure `jlink.mode: tcp-server` in `west-env.yml`. Run `west env debug`. Verify J-Link GDB server starts on Windows host and GDB inside container connects via TCP.
- **Pass**: GDB connects and halts target.

---

## New Test Stubs — Slice 11: Benchmark

### TEST-WINPERF-001
- **Type**: manual (Windows)
- Covers: REQ-WINPERF-001, REQ-WINPERF-002, REQ-WINPERF-004, REQ-TESTABILITY-003
- **Status**: TODO (Slice 11)
- **Pre-conditions**: Windows host, Podman Hyper-V available.
- **Steps**: Build `hello_world` twice: once with `workspace_mode: bind` (Docker Desktop), once with `workspace_mode: sync` (Podman Hyper-V). Run `west env benchmark` for each. Record build times.
- **Pass**: `sync` mode build time is documented. Results saved in `docs/benchmarks/`.

---

## Coverage Summary

All 47 active requirements have at least one test entry (automated, CI, or manual stub).
No coverage gaps carried forward from pre-realignment state.
Both former gaps (REQ-CMD-003, REQ-CMD-005) are resolved by retirement of those requirements.
