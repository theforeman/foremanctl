---
name: add-playbook
description: >-
  Scaffolds a new playbook directory with the correct naming conventions,
  metadata.obsah.yaml, and playbook YAML file for foremanctl or forge.
argument-hint: "<command-name> [--tool foremanctl|forge] [--include FRAGMENT...]"
references:
  - docs/developer/playbooks-and-roles.md
---

# Commands - Add Playbook

Scaffold a new CLI subcommand as an Ansible playbook for foremanctl or forge.

## Input

`$ARGUMENTS`:
- `<command-name>` (required) -- the subcommand name (lowercase, hyphenated)
- `--tool foremanctl|forge` -- which CLI tool the command belongs to (default: `foremanctl`)
- `--include FRAGMENT...` -- metadata fragments to include (e.g. `_tuning`, `_certificate_source`)

## Workflow

### 1. Determine Target Directory

- `foremanctl` -> `src/playbooks/<command-name>/`
- `forge` -> `development/playbooks/<command-name>/`

### 2. Create the Playbook YAML

The filename must match the directory name:

```
<target>/playbooks/<command-name>/<command-name>.yaml
```

Minimal playbook:

```yaml
---
- name: <Command description>
  hosts: all
  roles: []
```

### 3. Create metadata.obsah.yaml

Every subcommand needs metadata with at least a `help` field:

```yaml
---
help: |
  <Description shown in --help output>
```

Add variables if the command accepts parameters:

```yaml
variables:
  <variable_name>:
    help: <Description>
    choices:
      - option1
      - option2
```

Add `include` for shared metadata fragments:

```yaml
include:
  - _tuning
  - _certificate_source
```

### 4. Create a Shared Fragment (if applicable)

If the new command introduces reusable options, create a fragment:

```
<target>/playbooks/_<fragment_name>/metadata.obsah.yaml
```

Fragment directories use `_` prefix and contain ONLY `metadata.obsah.yaml`.

### 5. Validate

```bash
# For src/ playbooks only
pytest tests/playbooks_test.py -vv

# Run ansible-lint
cd <target>; ansible-lint
```

## Checklist

- [ ] Directory name is lowercase with hyphens
- [ ] Playbook YAML filename matches directory name
- [ ] `metadata.obsah.yaml` has at least a `help` field
- [ ] Shared options use `include` to reference `_`-prefixed fragments (not duplicated)
- [ ] `ansible-lint` passes
- [ ] `playbooks_test.py` passes (for `src/` playbooks)

## Examples

**Simple command (forge):**

```
development/playbooks/my-command/
  my-command.yaml
  metadata.obsah.yaml
```

**Command with shared options (foremanctl):**

```
src/playbooks/my-command/
  my-command.yaml
  metadata.obsah.yaml     # includes: [_tuning, _certificate_source]
```
