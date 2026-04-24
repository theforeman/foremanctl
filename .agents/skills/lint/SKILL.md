---
name: lint
description: >-
  Runs ansible-lint and Python linting across the foremanctl codebase.
  Reports issues and applies safe auto-fixes.
argument-hint: "[src|development|all]"
references:
  - .ansible-lint
  - .github/workflows/test.yml
---

# Skill - Lint

Run linting tools across the foremanctl codebase.

## Input

`$ARGUMENTS` -- optional scope:

- empty or `all` -> lint both `src/` and `development/`
- `src` -> lint only the production codebase
- `development` -> lint only the development codebase

## Workflow

### 1. Ansible Lint

ansible-lint must be run from within each data directory separately, matching CI behavior:

```bash
cd src; ../.venv/bin/ansible-lint
```

```bash
cd development; ../.venv/bin/ansible-lint
```

### 2. Categorize Results

Group findings by:

- **Errors** -- must be fixed before merging (CI will fail)
- **Warnings** -- should be fixed but won't block CI
- **Style** -- optional improvements

### 3. Apply Safe Fixes

For each fixable issue:

- YAML formatting (truthy values, line length, indentation)
- Missing FQCN (replace `copy` with `ansible.builtin.copy`)
- Missing task names (add descriptive names)

Do NOT fix:

- Issues that change task behavior or conditions
- Issues that require understanding business context

### 4. Verify Fixes

Re-run ansible-lint after fixes to confirm resolution:

```bash
cd src; ansible-lint
cd development; ansible-lint
```

### 5. Report

Output a summary:

```markdown
## Lint Results

### src/
- Fixed: N issues (list)
- Remaining: M issues (list with explanations)

### development/
- Fixed: N issues (list)
- Remaining: M issues (list with explanations)
```

## CI Context

The GitHub Actions workflow runs:

1. `ansible-lint` with `working_directory: src`
2. `ansible-lint` with `working_directory: development`

Each directory has its own `ansible.cfg` and `requirements.yml`. Lint must pass in both for CI to be green.
