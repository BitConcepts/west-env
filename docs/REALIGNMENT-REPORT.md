# Realignment Report — west-env

**Date**: 2026-05-13
**Trigger**: Transition from single-platform container wrapper to cross-platform Zephyr RTOS developer environment (Windows / Linux / macOS).

---

## 1. Inventory of Current State

### Architecture
Single-layer Python library. Dispatches `west env` sub-commands (`init`, `build`, `shell`, `doctor`) to the native host or a single OCI container, with the workspace bind-mounted at `/work`. No Windows-specific UX, no workspace sync layer, no J-Link, no Git credential forwarding, no VSCode integration, no caching strategy.

### Requirement summary
19 active requirements across: REQ-CONFIG-001–004, REQ-ENGINE-001–003, REQ-CONTAINER-001–003, REQ-UTIL-001–002, REQ-CMD-001–006, REQ-BUILD-001.

### Tests
14 test entries across config, engine, container, util, CI integration.

### Feature plan
None existed.

### Platform assumptions found
- Nominally cross-platform (Python + YAML) but no explicit Windows UX design.
- Engine detection only probes `docker`/`podman` in PATH — no Podman machine or Hyper-V detection.
- Workspace binding via host CWD bind mount, which is slow on Windows (NTFS→Linux).
- No Git credential forwarding documented.
- No J-Link strategy.

### Existing Docker/Podman/WSL assumptions found
- `detect_engine()` knows only `docker` and `podman` binary names.
- Container workspace mounted via host path — problematic on Windows.
- No Podman machine, no Hyper-V VM, no WSL2 guidance.

---

## 2. Requirement Classification

| ID | Summary | Classification | Reason | New ID / Fate |
|---|---|---|---|---|
| REQ-CONFIG-001 | Config path resolves from manifest dir | KEEP | Still valid; mechanism unchanged | REQ-CONFIG-001 |
| REQ-CONFIG-002 | Parse env.type (native\|container) | MODIFY | Needs workspace_mode field; backend replaces engine | REQ-CONFIG-002 |
| REQ-CONFIG-003 | Parse engine (auto\|docker\|podman) | MODIFY | Must expand to podman-machine, hyper-v, detect | REQ-CONFIG-003 |
| REQ-CONFIG-004 | Default to native, docker, None | MODIFY | Defaults must be platform-aware | REQ-CONFIG-004 |
| REQ-ENGINE-001 | detect_engine auto, prefer docker | RETIRE | Superseded by REQ-BACKEND-001 + REQ-BACKEND-004 | — |
| REQ-ENGINE-002 | Explicit engine preference | RETIRE | Absorbed into REQ-BACKEND-001 | — |
| REQ-ENGINE-003 | RuntimeError no engine found | RETIRE | Absorbed into REQ-BACKEND-003 (doctor reports) | — |
| REQ-CONTAINER-001 | Mount workspace at /work | RETIRE | Superseded by REQ-WORKSPACE-001–004 (richer model) | — |
| REQ-CONTAINER-002 | Shell-quote args via shlex | KEEP | Always needed; no change | REQ-CONTAINER-002 |
| REQ-CONTAINER-003 | git safe.directory in container | KEEP | Still required for Git ≥ 2.35 | REQ-CONTAINER-003 |
| REQ-UTIL-001 | Python ≥ 3.10 check | KEEP | Unchanged | REQ-UTIL-001 |
| REQ-UTIL-002 | host_shell_command() platform | RETIRE | Superseded by REQ-PLATFORM-002 (explicit wrapper model) | — |
| REQ-CMD-001 | west env init/build/shell/doctor | RETIRE | Command set expands; split across platform + feature groups | — |
| REQ-CMD-002 | west env build proxies west build | RETIRE | Build runner is Slice 4; covered by WORKSPACE + PLATFORM | — |
| REQ-CMD-003 | west env shell interactive | RETIRE | Shell wrapper covered by REQ-PLATFORM-002 | — |
| REQ-CMD-004 | west env doctor | RETIRE | Doctor greatly expanded; covered by REQ-BACKEND-003 | — |
| REQ-CMD-005 | --container flag | RETIRE | Replaced by --backend/--mode concept; was ambiguous | — |
| REQ-CMD-006 | validate_workspace_layout | KEEP | Pre-flight validation still valid | REQ-CMD-006 |
| REQ-BUILD-001 | pyproject install + pytest pass | KEEP | Package build contract unchanged | REQ-BUILD-001 |

**Summary**: 6 KEEP, 3 MODIFY, 10 RETIRE, 38 new requirements added across 10 new groups.

---

## 3. Coverage Gap Resolution

Both previously unfixable coverage gaps are **eliminated** by this realignment:

| Former Gap | Former REQ | Resolution |
|---|---|---|
| No CI test for interactive shell dispatch | REQ-CMD-003 | **RETIRED** — superseded by REQ-PLATFORM-002 |
| No unit test for --container flag | REQ-CMD-005 | **RETIRED** — superseded by REQ-BACKEND-001 / REQ-WINPERF-003 |

Neither gap carries forward. The new test matrix (see TESTS.md) defines explicit test stubs for all new requirements.

---

## 4. Impacted Files

| File | Change |
|---|---|
| `docs/REALIGNMENT-REPORT.md` | Created (this document) |
| `docs/ARCHITECTURE.md` | Complete rewrite — 8 layers, 3 platforms, 4 backends, 4 workspace modes |
| `docs/REQUIREMENTS.md` | 10 old groups retired/replaced; 10 new groups; 47 active requirements |
| `docs/TESTS.md` | 9 tests retired, 6 retained (updated), 27 new test stubs |
| `docs/FEATURE-PLAN.md` | Created — 12 vertical implementation slices |
| `west_env/container.py` | No changes in this realignment; Slice 2–4 target |
| `west_commands/env.py` | No changes in this realignment; Slice 4–8 target |
| `west_env/engine.py` | No changes; will be renamed/replaced in Slice 2 |

---

## 5. Migration Rules Applied

- REQ-ENGINE-* IDs are retired and must not be reused.
- REQ-CMD-001–005 IDs are retired and must not be reused.
- REQ-CONTAINER-001 is retired; REQ-CONTAINER-002/003 are kept.
- REQ-UTIL-002 is retired.
- REQ-CONFIG-002/003/004 IDs are retained but meanings are extended (not replaced).
- No contradictory old requirements left active; all retired entries documented here.
