# Feature Plan — west-env

Realigned 2026-05-13. 12 vertical slices mapped to realigned requirements.
Each slice is independently deliverable and testable.

---

## Slice 1 — Architecture + Requirement Migration ✅

**Description**: Rewrite governance documents to reflect the cross-platform, Windows-first direction. No source code changes.
**Requirements covered**: All (governance alignment)
**Deliverables**: REALIGNMENT-REPORT.md, ARCHITECTURE.md (rewrite), REQUIREMENTS.md (rewrite), TESTS.md (rewrite), FEATURE-PLAN.md
**Acceptance**: `specsmith validate` passes with all 47 REQ IDs; `specsmith audit` shows ≥ 27 checks passing.
**Status**: Complete (this session)

---

## Slice 2 — Backend Detection + Doctor

**Description**: Replace `west_env.engine` with `west_env.backend`. Detect all 6 backend types. Implement platform fallback chain. Expand `west env doctor` with structured backend report. Extend `EnvConfig` to parse `backend` and `workspace_mode`.
**Requirements covered**: REQ-BACKEND-001, REQ-BACKEND-002, REQ-BACKEND-003, REQ-BACKEND-004, REQ-CONFIG-002, REQ-CONFIG-003, REQ-CONFIG-004, REQ-WINPERF-002, REQ-WINPERF-003
**Deliverables**:
- `west_env/backend.py` (new — replaces engine.py)
- Updated `west_env/config.py` (backend + workspace_mode fields)
- Updated `west_commands/env.py` (doctor sub-action expanded)
- `tests/test_backend.py` (TEST-BACKEND-001 through TEST-BACKEND-004)
**Acceptance**: All TEST-BACKEND-* pass; `west env doctor` on Windows lists backend, fallback chain, and performance warning when applicable.

---

## Slice 3 — Workspace Sync Manager

**Description**: Implement `west_env.sync` with all four workspace modes: `sync`, `copy`, `tmpfs`, `bind`. Bind-mount mode on Windows emits a warning. Source-only sync excludes build/cache dirs.
**Requirements covered**: REQ-WORKSPACE-001, REQ-WORKSPACE-002, REQ-WORKSPACE-003, REQ-WORKSPACE-004, REQ-WINPERF-001, REQ-WINPERF-003
**Deliverables**:
- `west_env/sync.py` (new)
- Updated `west_env/container.py` (delegates workspace strategy to sync module)
- Updated `west_env/config.py` (sync exclusion patterns)
- `tests/test_sync.py` (TEST-WORKSPACE-001 through TEST-WORKSPACE-004)
**Acceptance**: All TEST-WORKSPACE-* pass; bind mode on Windows prints warning to stderr; sync is idempotent.

---

## Slice 4 — Build Runner

**Description**: Expand `west env build` to use the backend abstraction and workspace sync layer. Support passthrough args. Integrate with Slice 2 (backend selection) and Slice 3 (workspace mode).
**Requirements covered**: REQ-PLATFORM-001, REQ-PLATFORM-003, REQ-CMD-006
**Deliverables**:
- Updated `west_commands/env.py` (`build` action uses backend + sync)
- Updated `tests/test_west_e2e.py` (backend + sync integration)
**Acceptance**: `west env build` succeeds on Linux native CI with docker backend and bind mode; workspace validation runs before build.

---

## Slice 5 — Cache Manager

**Description**: Implement `west_env.cache` with named volume management for ccache, west modules, Zephyr SDK, and pip. Add `west env cache stats` and `west env cache reset` sub-commands.
**Requirements covered**: REQ-CACHE-001, REQ-CACHE-002, REQ-CACHE-003, REQ-CACHE-004
**Deliverables**:
- `west_env/cache.py` (new)
- Updated `west_env/config.py` (cache sub-section)
- Updated `west_commands/env.py` (`cache` action)
- `tests/test_cache.py` (TEST-CACHE-001 through TEST-CACHE-004 unit coverage)
**Acceptance**: ccache volume persists across container restarts; `west env cache stats` reports volume size; `west env cache reset --ccache` clears it.

---

## Slice 6 — Windows PowerShell Wrappers

**Description**: Implement `west_env.platform` for Windows. Generate `.ps1` wrapper scripts for all actions (setup, sync, build, flash, debug, cache, benchmark). Wrappers call `west env <action>` with correct arguments; no Bash or WSL required.
**Requirements covered**: REQ-PLATFORM-001, REQ-PLATFORM-002, REQ-PLATFORM-003, REQ-WINNUX-001, REQ-WINNUX-002, REQ-WINNUX-003
**Deliverables**:
- `west_env/platform.py` (new — Windows path)
- Generated `scripts/west-env-build.ps1` et al. (template-based)
- Updated `west_commands/env.py` (`generate-tasks` action)
- `tests/test_platform_windows.py` (TEST-PLATFORM-001 Windows branch)
**Acceptance**: PowerShell wrappers generated and executable from `pwsh`; no bash/wsl in wrapper content; `west env build` callable via wrapper.

---

## Slice 7 — Linux / macOS Shell Wrappers

**Description**: Implement `west_env.platform` for Linux and macOS. Generate `.sh` wrapper scripts with identical semantics to Windows `.ps1` wrappers.
**Requirements covered**: REQ-PLATFORM-001, REQ-PLATFORM-002, REQ-PLATFORM-003
**Deliverables**:
- Updated `west_env/platform.py` (POSIX path)
- Generated `scripts/west-env-build.sh` et al.
- `tests/test_platform_posix.py` (TEST-PLATFORM-001 POSIX branch, TEST-PLATFORM-002)
**Acceptance**: Shell wrappers are executable (`chmod +x`); `--help` output matches Windows wrappers argument-for-argument.

---

## Slice 8 — VSCode Tasks

**Description**: Implement `west_env.vscode` to generate `.vscode/tasks.json`. Windows tasks call `.ps1`; Linux/macOS call `.sh`. No Remote WSL dependency. All tasks use host terminal profile.
**Requirements covered**: REQ-VSCODE-001, REQ-VSCODE-002, REQ-VSCODE-003, REQ-VSCODE-004, REQ-WINNUX-001
**Deliverables**:
- `west_env/vscode.py` (new)
- Generated `.vscode/tasks.json` template
- `tests/test_vscode.py` (TEST-VSCODE-001)
**Acceptance**: Generated `tasks.json` parseable JSON; Windows tasks contain no `bash`/`wsl`; Linux/macOS tasks reference `.sh` wrappers; `type` field is `shell` not `process`.

---

## Slice 9 — Git Credential Validation

**Description**: Implement `west_env.credentials`. Forward Windows OpenSSH agent socket into container. Document HTTPS credential-manager fallback. Add credential check to `west env doctor`.
**Requirements covered**: REQ-GIT-001, REQ-GIT-002, REQ-GIT-003, REQ-GIT-004, REQ-WINNUX-004
**Deliverables**:
- `west_env/credentials.py` (new)
- Updated `west_commands/env.py` (doctor includes credential check)
- `tests/test_credentials.py` (TEST-GIT-001 unit, TEST-GIT-002)
- Docs: `docs/git-credentials.md`
**Acceptance**: On Windows, `SSH_AUTH_SOCK` forwarded into container; `west env doctor` reports active strategy; no keys appear in container `env` or filesystem.

---

## Slice 10 — J-Link Host Flashing

**Description**: Implement `west_env.flash`. On Windows, invoke Windows J-Link tools on synced artifact paths. Provide optional TCP GDB server mode. Ensure USB passthrough is not required.
**Requirements covered**: REQ-JLINK-001, REQ-JLINK-002, REQ-JLINK-003, REQ-JLINK-004
**Deliverables**:
- `west_env/flash.py` (new)
- Updated `west_commands/env.py` (`flash` and `debug` actions)
- Updated `west_env/config.py` (`jlink` sub-section)
- Docs: `docs/flashing.md`
**Acceptance**: TEST-JLINK-001 manual pass on Windows + hardware; TCP GDB server mode connects from container GDB to Windows J-Link server.

---

## Slice 11 — Benchmarks

**Description**: Implement `west env benchmark`. Run a reference build (e.g. `hello_world` for `native_sim`) under each workspace mode and record wall-clock time, machine specs, backend, and Zephyr revision. Store results in `docs/benchmarks/`.
**Requirements covered**: REQ-WINPERF-004, REQ-TESTABILITY-003
**Deliverables**:
- Updated `west_commands/env.py` (`benchmark` action)
- `docs/benchmarks/` directory with schema JSON
- `tests/test_benchmark.py` (output schema validation)
**Acceptance**: `west env benchmark` completes and writes a valid JSON result file; TEST-WINPERF-001 manual pass documenting sync vs bind build time comparison on Windows.

---

## Slice 12 — Docs + Troubleshooting

**Description**: Write user-facing documentation: README rewrite, platform-specific quick-start guides, troubleshooting guide, FAQ.
**Requirements covered**: REQ-PLATFORM-001, REQ-PLATFORM-002, REQ-PLATFORM-003, REQ-WINNUX-001 through REQ-WINNUX-004 (documented), REQ-TESTABILITY-002
**Deliverables**:
- Rewritten `README.md` (cross-platform, Windows-first framing)
- `docs/quickstart-windows.md`
- `docs/quickstart-linux.md`
- `docs/quickstart-macos.md`
- `docs/troubleshooting.md`
- `docs/git-credentials.md` (if not done in Slice 9)
- `docs/flashing.md` (if not done in Slice 10)
**Acceptance**: README makes no claim of WSL or Remote WSL requirement. Quick-start guides are validated by a fresh install on the target platform.
