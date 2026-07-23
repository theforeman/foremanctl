---
name: lint
description: >-
  Run linters after finishing a change. Use when any YAML and code files have been changed.
---

# Lint

Run project code checks.

## Canonical docs

- [AGENTS.md](../../../AGENTS.md) — common lint commands
- [Playbooks and Roles](../../../docs/developer/playbooks-and-roles.md) — secrets, OAuth, naming
- Custom rules: `../../../.ansible-lint-rules/` (source of truth for enforceable constraints)
- Config: `../../../.ansible-lint`

## Workflow

1. Set up virtual environment
2. Ansible lint
3. Ruff

### Set up virtual environment

```shell
# (in project root dir)
./setup-environment
source .venv/bin/activate
```

### Ansible lint

```shell
# (in project root dir)
cd src && ansible-lint
cd development && ansible-lint
```

Fix all findings. Do not ignore any findings.

### Ruff

```shell
# (in project root dir)
ruff check tests/ src/ development/scripts/ inventories/
```

Fix all findings. Do not ignore any findings.
