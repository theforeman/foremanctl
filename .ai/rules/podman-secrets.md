---
name: podman-secrets
description: >-
  Naming conventions and requirements for Podman secrets in foremanctl.
  All agents creating or modifying secret-related code must follow these rules.
applies-to:
  - src/roles/
references:
  - DEVELOPMENT.md
---

# Rules - Podman Secrets Conventions

Configuration files and credentials for containerized services are stored as Podman secrets and mounted into containers. All new secrets must follow these conventions.

## Naming

### Config Files

```shell
<role_namespace>-<filename>-<extension>
```

When additional application context is needed:

```shell
<role_namespace>-<app>-<filename>-<extension>
```

### Strings (Passwords, Tokens, etc.)

```shell
<role_namespace>-<descriptive_name>
```

When additional application context is needed:

```shell
<role_namespace>-<app>-<descriptive_name>
```

## Required Labels

Every Podman secret MUST include these labels:

### Config Files

- `filename` -- the file name with extension (e.g. `settings.yml`)
- `app` -- the application that uses the configuration file (e.g. `foreman`)

### Strings

- `app` -- the application that uses the string (e.g. `postgresql`)

## Inspection Commands

```bash
# List all secrets
podman secret ls

# View a secret's content
podman secret inspect --showsecret --format "{{.SecretData}}" <secret-name>
```

## Rules

- NEVER store credentials or sensitive configuration in plain text files, Ansible variables, or version control.
- ALWAYS use Podman secrets for configuration files mounted into containers.
- ALWAYS include the required labels on every new secret.
- ALWAYS follow the naming convention -- no ad-hoc naming.
- Secret names must be unique across the entire deployment.
- When a role manages multiple configuration files, each gets its own secret following the naming pattern.
