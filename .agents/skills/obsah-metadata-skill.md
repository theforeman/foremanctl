---
name: obsah-metadata
description: >-
  Deep reference on the metadata.obsah.yaml schema used to define CLI
  subcommands in foremanctl and forge. Covers help, variables, constraints,
  includes, and all variable properties.
technologies:
  - yaml
  - ansible
references:
  - docs/developer/playbooks-and-roles.md
  - https://github.com/theforeman/obsah/blob/master/docs/source/development.rst
---

# Skill - Obsah Metadata Schema

`obsah` is the Ansible playbook execution engine that powers foremanctl and forge. Each CLI subcommand is defined by a `metadata.obsah.yaml` file in the playbook directory.

## Overview

`metadata.obsah.yaml` defines:

- Help text for the subcommand
- CLI parameters (variables) with validation
- Constraints between parameters
- Includes to share parameter definitions across subcommands

## `help` (required)

Short description shown in `--help` output:

```yaml
help: |
  Install
```

## `variables`

Each key becomes an Ansible variable passed to the playbook. obsah auto-converts `snake_case` names to `--hyphen-case` CLI flags unless overridden.

### Variable Properties

| Property | Required | Description | Example |
|----------|----------|-------------|---------|
| `help` | Yes | Description shown in `--help` | `"Initial password for the admin user."` |
| `parameter` | No | Override the auto-generated CLI flag name | `--certificate-cname`, `vm_action` (positional) |
| `action` | No | How the CLI handles the value (see Actions) | `store`, `append_unique` |
| `choices` | No | Restrict to a fixed list of values | `[internal, external]` |
| `type` | No | Value type validation (obsah.types) | `FQDN`, `AbsolutePath` |
| `persist` | No | Save value to answers file for reuse (default: `true`) | `false` |
| `dest` | No | Override the attribute name for the parsed value | `features` |

### Actions

| Action | Behavior |
|--------|----------|
| `store` | Store a single value (default) |
| `store_true` | Boolean flag, sets variable to `true` when present |
| `append` | Collect multiple values into a list (repeatable flag) |
| `append_unique` | Like `append`, but deduplicates values |
| `remove` | Remove a value from the list variable specified by `dest` |

### Examples

**Simple variable with choices:**

```yaml
variables:
  database_mode:
    help: Defaults to internal. Set to 'external' if using an external database.
    choices:
      - internal
      - external
```

**Append/remove pair with shared dest:**

```yaml
variables:
  features:
    parameter: --add-feature
    help: Additional features to enable in this deployment.
    action: append_unique
  remove_features:
    parameter: --remove-feature
    help: Additional features to disable in this deployment.
    action: remove
    dest: features
```

**Custom type and parameter override:**

```yaml
variables:
  certificates_cnames:
    help: Additional DNS name for Subject Alternative Names. Can be specified multiple times.
    action: append_unique
    type: FQDN
    parameter: --certificate-cname
```

**Positional argument:**

```yaml
variables:
  vm_action:
    parameter: vm_action
    help: Start the virtual machines
    choices:
      - start
      - stop
```

## `constraints`

Enforce rules between related flags:

### `required_together`

All variables in the set must be provided if any one is:

```yaml
constraints:
  required_together:
    - [database_ssl_mode, database_ssl_ca]
```

### `required_if`

Variables that become required when another variable has a specific value:

```yaml
constraints:
  required_if:
    - ['database_mode', 'external', ['database_host']]
```

Format: `[variable, value, [required_variables]]`

## `include`

Reference shared metadata fragments to avoid duplicating variable definitions:

```yaml
include:
  - _certificate_source
  - _database_mode
  - _database_connection
  - _tuning
  - _flavor_features
```

Fragment directories are prefixed with `_` and contain only `metadata.obsah.yaml`. When included, their variables and constraints are merged into the including subcommand's CLI interface.

## Full Example

From `src/playbooks/deploy/metadata.obsah.yaml`:

```yaml
---
help: |
  Install

variables:
  foreman_initial_admin_username:
    help: Initial username for the admin user.
  foreman_initial_admin_password:
    help: Initial password for the admin user.
  foreman_puma_workers:
    help: Number of workers for Puma.
  pulp_worker_count:
    help: Number of Pulp workers. Defaults to 8 or the number of CPU cores, whichever is smaller.
  external_authentication:
    help: External authentication method to use
    choices:
      - ipa
      - ipa_with_api
  external_authentication_pam_service:
    help: Name of the PAM service to use for IPA authentication
  certificates_cnames:
    help: Additional DNS name to include in Subject Alternative Names for certificates. Can be specified multiple times.
    action: append_unique
    type: FQDN
    parameter: --certificate-cname

include:
  - _certificate_source
  - _database_mode
  - _database_connection
  - _tuning
  - _flavor_features
```

## Parameter Persistence

By default, obsah persists parameter values to an answers file (`.var/lib/foremanctl/`) so they are reused on subsequent runs. Set `persist: false` for one-time parameters that should not be remembered.
