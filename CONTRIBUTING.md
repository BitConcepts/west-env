# Contributing to west-env

## Governance

This project uses the specsmith AEE governance model.
- `AGENTS.md` — agent governance rules (read before starting any task)
- `LEDGER.md` — append-only change log (record every session)
- `docs/REQUIREMENTS.md` — all changes must map to a requirement
- `docs/TESTS.md` — all requirements must have a test

## Workflow

1. Read `AGENTS.md` and recent `LEDGER.md`.
2. Propose changes (see `docs/governance/SESSION-PROTOCOL.md`).
3. Implement against the relevant slice in `docs/FEATURE-PLAN.md`.
4. Run `pytest tests/` and `ruff check west_env/ west_commands/ tests/`.
5. Run `specsmith audit` to confirm 28/28 checks pass.
6. Record in `LEDGER.md`.

## Code style

- Python 3.10+, no type annotations required but welcomed.
- `ruff` for linting and formatting (`line-length = 120`, `E402` ignored).
- All subprocess calls must be isolated in testable functions so they can be mocked.
- New modules go in `west_env/`; the command entry point is `west_commands/env.py`.

## Tests

```sh
pip install -e ".[dev]"
pytest tests/test_config.py tests/test_backend.py tests/test_sync.py tests/test_new_modules.py -v
ruff check west_env/ west_commands/ tests/ --select=E,F,W
```

Tests that require Docker are gated with `@unittest.skipUnless(docker_available(), ...)`.
Tests that require hardware (J-Link) are marked `TODO (manual)` in `docs/TESTS.md`.

## Platform testing

The CI matrix covers Windows, Linux, and macOS × Python 3.10/3.11/3.12.
Please verify your change passes on all three platforms before opening a PR.
Docker integration tests run on ubuntu-latest only.

## Requirement traceability

Every code change must map to one or more requirements in `docs/REQUIREMENTS.md`.
If your change introduces a new capability, add the requirement first, then implement.
If it retires a requirement, update `docs/REALIGNMENT-REPORT.md` and mark it retired.
