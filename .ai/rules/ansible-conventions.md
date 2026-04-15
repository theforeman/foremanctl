---
name: ansible-conventions
description: >-
  Coding conventions for Ansible playbooks, roles, and metadata in foremanctl.
  All agents working with Ansible code must follow these rules.
applies-to:
  - src/playbooks/
  - src/roles/
  - development/playbooks/
  - development/roles/
references:
  - docs/developer/playbooks-and-roles.md
---

# Rules - Ansible Conventions

These rules apply to all Ansible code in foremanctl.

## Playbook Naming

- Each playbook directory under `playbooks/` becomes a CLI subcommand via obsah.
- **Directory name** = subcommand name. Use lowercase with hyphens (`pull-images`, `deploy-dev`).
- **Playbook YAML filename must match the directory name.** Example: `deploy/deploy.yaml`, NOT `deploy/main.yaml`.
- Shared metadata fragments use `_` prefix with underscores (`_certificate_source`, `_database_mode`). They contain ONLY `metadata.obsah.yaml` -- no playbook YAML.
- Every subcommand directory must have a `metadata.obsah.yaml` with at least a `help` field.

## Role Naming

- Use **lowercase with underscores**: `foreman_proxy`, `post_install`, `check_hostname`.
- Name roles after the service or concern they manage: `redis`, `httpd`, `certificates`.

## File Extensions

- Use `.yaml` for playbook and task files, not `.yml`.
- Use `.j2` for Jinja2 templates.

## Task Requirements

- Every task MUST have a `name` field with a descriptive, human-readable name.
- Use fully qualified collection names (FQCN) for all modules: `ansible.builtin.copy`, NOT `copy`.
- Tasks must be idempotent. If using `ansible.builtin.command` or `ansible.builtin.shell`, use `creates`, `removes`, or `when` to ensure idempotency.
- File and template tasks MUST include an explicit `mode` parameter.

## Handlers

- Use handlers for service state changes (restart, reload).
- Handler names use Title Case: `Restart Foreman Proxy`, `Refresh Foreman Proxy`.
- Tasks that change service configuration MUST use `notify` to trigger handlers, not inline service tasks.

## Variables

- Variable names use `snake_case`.
- Obsah auto-converts `snake_case` to `--hyphen-case` CLI flags. Override with `parameter` in metadata only when necessary.
- Default values belong in `src/vars/defaults.yml` or role `defaults/main.yaml`, not hardcoded in tasks.
- Sensitive values (passwords, keys) must use Podman secrets, never Ansible variables in plain text.

## metadata.obsah.yaml

- `help` is required for every subcommand.
- Use `include` to reference shared fragments rather than duplicating variable definitions across subcommands.
- Variable properties: `help` (required), `parameter`, `action`, `choices`, `type`, `persist`, `dest`.
- Constraint types: `required_together`, `required_if`.

## Linting

- ansible-lint must pass on both `src/` and `development/` independently.
- Run from within the directory: `cd src; ansible-lint` and `cd development; ansible-lint`.
- Do NOT add `# noqa` comments without explicit justification.
