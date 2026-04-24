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

# Rules - Podman Secrets

Configuration files and credentials for containerized services are stored as Podman secrets and mounted into containers. All new secrets must follow these conventions.

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
