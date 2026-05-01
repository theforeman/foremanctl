---
name: safety
description: >-
  Safety rules for all AI agents working with foremanctl. Prevents destructive
  operations and protects production deployments.
applies-to:
  - "*"
---

# Rules - Safety Rules

These rules apply to ALL agents and commands. They are non-negotiable.

## Destructive Command Blocklist

NEVER execute these commands without explicit user confirmation:

- `rm -rf /` or `rm -rf ~` or any recursive delete of system directories
- `git push --force` to `master` or `main`
- `DROP TABLE`, `DROP DATABASE`, or other destructive SQL
- `chmod 777` on any path
- `podman system prune` or `podman volume prune` without confirmation
- `vagrant destroy` without confirmation
- `systemctl stop` or `systemctl disable` on production services without confirmation

## Production Awareness

foremanctl targets REAL production deployments of Foreman and Katello. AI agents must understand:

- `./foremanctl deploy` modifies the target system. NEVER run it without explicit user confirmation.
- `./foremanctl` operates on production infrastructure by default. The development equivalent is `./forge`.
- Podman secrets may contain production credentials. NEVER log, print, or expose secret values.
- Changes to `src/` affect production deployments. Changes to `development/` affect dev/test only.

## Git Safety

- NEVER force-push to `master`.
- NEVER rewrite history on shared branches.
- NEVER commit files containing credentials, secrets, or sensitive data.
- Check `.gitignore` before staging new files.

## Ansible Safety

- NEVER use `ansible.builtin.shell` or `ansible.builtin.command` with unvalidated user input.
- NEVER disable SSL verification in production playbooks.
- NEVER hardcode passwords or tokens in playbooks, roles, or variables.
- ALWAYS use `--check` mode when suggesting dry-run verification to users.

## File System Safety

- NEVER modify files outside the repository working directory without explicit permission.
- NEVER overwrite `.var/` state files -- they contain deployment state and answers.
- NEVER delete `build/` directories without confirming the user wants to rebuild collections.

## When in Doubt

- Ask the user before executing any command that modifies system state.
- Prefer read-only operations (inspect, list, show) over write operations.
- Suggest `--check` or dry-run equivalents when available.
- If a command could affect production, warn the user explicitly.
