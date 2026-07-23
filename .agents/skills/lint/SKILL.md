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

1. Set up virtual environment (builds Ansible collections)
2. Ansible lint
3. Ruff

All commands below run from the **project root**.

### Set up virtual environment

```shell
./setup-environment
source .venv/bin/activate
```

`setup-environment` installs Python dependencies and runs `make build/collections/foremanctl build/collections/forge`. Ansible lint needs those collection trees (same paths as the `foremanctl` and `forge` wrappers).

### Ansible lint

Run each tree in a subshell from the project root. Set `ANSIBLE_COLLECTIONS_PATH` and disable system collection scanning so lint resolves the same collections as deploy, without picking up unrelated system installs.

```shell
# src (production playbooks and roles)
ANSIBLE_COLLECTIONS_PATH="$PWD/build/collections/foremanctl" ANSIBLE_COLLECTIONS_SCAN_SYS_PATH=false \
  bash -c '(cd src && ansible-lint)'

# development (dev playbooks and roles; exclude vendored collections from lint targets)
ANSIBLE_COLLECTIONS_PATH="$PWD/build/collections/forge" ANSIBLE_COLLECTIONS_SCAN_SYS_PATH=false \
  bash -c '(cd development && ansible-lint --exclude ../build/collections)'
```

Use `$PWD` so collection paths stay correct after the subshell changes directory (a bare `build/collections/...` path would be resolved from inside `src/` or `development/` and fail).

Do **not** chain `cd src && ansible-lint` and `cd development && ansible-lint` in one shell — after the first command the working directory is `src/`, so `cd development` fails.

If ansible-lint reports missing modules or roles despite collections being built, clear stale caches and rerun:

```shell
rm -rf src/.cache development/.cache
```

Fix all findings. Do not ignore any findings.

### Ruff

```shell
ruff check tests/ src/ development/scripts/ inventories/
```

Fix all findings. Do not ignore any findings.
