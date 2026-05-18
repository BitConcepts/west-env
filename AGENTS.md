# west-env — Agent Governance

This project was imported by specsmith. The governance files contain detected structure. Review and enrich with your agent.

## Project Summary
- **Languages**: python, markdown, yaml
- **Build system**: pyproject
- **Test framework**: pytest
- **Files detected**: 75
- **Modules**: west_commands, west_env

## Workflow Rules
1. Read AGENTS.md fully before starting any task.
2. Log all changes in LEDGER.md.
3. Map changes to requirements in docs/REQUIREMENTS.md.
4. Verify against docs/TESTS.md.


---
## Governance commands (specsmith_run / /specsmith)

All specsmith governance operations should be invoked through the
``specsmith_run`` agent tool or the ``/specsmith`` REPL slash command.

**In the Nexus REPL:**

```
/specsmith save               # backup + commit + push governance state
/specsmith load               # pull + restore governance state
/specsmith audit --strict     # strict governance audit
/specsmith status             # show governance status
/specsmith push               # git push governance changes
/specsmith pull               # git pull governance changes
/specsmith sync               # full two-way sync
/specsmith watch              # watch CI and block until green
```

**Verb shortcuts** (single word, no prefix needed in tool calls):
``save``, ``load``, ``push``, ``pull``, ``sync``, ``audit``, ``status``,
``watch``, ``commit``, ``validate``, ``doctor``, ``run``.

These are all equivalent: ``specsmith_run("save")``,
``specsmith_run("/specsmith save")``, ``specsmith_run("specsmith save")``.
