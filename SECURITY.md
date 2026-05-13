# Security Policy

## Supported versions

Only the current `main` branch is actively maintained.

## Reporting a vulnerability

Please use the repository's **private vulnerability reporting** feature (GitHub → Security → Report a vulnerability). Do not open a public issue.

Include:
- Description of the vulnerability
- Steps to reproduce
- Affected versions
- Proposed fix (if any)

We aim to acknowledge reports within 48 hours and publish a fix or advisory within 14 days.

## Security design

Key security properties maintained by `west-env`:

| Property | Guarantee |
|----------|-----------|
| Container images | Never contain tokens, passwords, or private keys |
| SSH credentials | Forwarded via agent socket only; no key files copied |
| Git credential manager | Host-side only; no HTTPS tokens enter the container |
| Workspace bind mounts | Limited to the west workspace directory |
| `git safe.directory` | Applied as `*` inside containers for Zephyr compatibility |

## Dependency security

Dependencies are audited weekly via `pip-audit` in CI.
Dependabot monitors both PyPI packages and GitHub Actions for version updates.

## Scope

This project is experimental and intended for local development and CI.
It is not hardened for multi-tenant or production infrastructure.
