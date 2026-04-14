# Playbooks and Roles

This document covers how playbooks and roles are organized, named, and wired up to CLI commands.

## How CLI Commands Map to Playbook Directories

`foremanctl` (production deployment tool) and `forge` (development and testing tool) are both wrappers around [Obsah](https://github.com/theforeman/obsah). Each wrapper sets the `OBSAH_DATA` environment variable, which tells Obsah where to discover playbook directories and expose them as CLI subcommands.

- `foremanctl` → playbooks in `src/playbooks/`
- `forge` → playbooks in `development/playbooks/`

Here are a few examples:

| Directory                           | CLI command              |
| ----------------------------------- | ------------------------ |
| `src/playbooks/deploy/`             | `foremanctl deploy`      |
| `src/playbooks/features/`           | `foremanctl features`    |
| `development/playbooks/vms/`        | `forge vms`              |
| `development/playbooks/deploy-dev/` | `forge deploy-dev`       |


## Naming Conventions

### Playbooks

Each directory under `playbooks/` becomes a CLI subcommand (e.g. `foremanctl deploy`, `forge vms`).

- **Directory name** becomes the subcommand name (handled by Obsah), so use lowercase with hyphens as separators (e.g. `pull-images`, `deploy-dev`).
- **Playbook YAML filename must match the directory name.** For example, `deploy/deploy.yaml`, `pull-images/pull-images.yaml`.
- **Every subcommand must have a `metadata.obsah.yaml`** with at least a `help` field.

### Roles

Roles live under `src/roles/` (production) and `development/roles/` (development).

- Use **lowercase with underscores** as separators: `postgresql`, `foreman_proxy`, `post_install`, `foreman_development`.
- Name roles after the service or concern they manage: `redis`, `httpd`, `certificates`, `systemd_target`.

## Shared Metadata Fragments

Directories prefixed with `_` (underscore) contain reusable metadata that can be included by subcommands via the `include` field. They are **not** exposed as CLI commands.

- Use the `_` prefix to indicate the directory is a fragment, not a standalone command.
- Fragment directories contain only a `metadata.obsah.yaml` — no playbook YAML file.
- Name them after the concept they represent.
- When a subcommand includes a fragment, the fragment's variables and constraints are merged into its CLI interface.

Here are a few examples:

| Fragment               | What it provides                              |
| ---------------------- | --------------------------------------------- |
| `_certificate_source`  | Certificate source selection                  |
| `_database_mode`       | Internal vs external database                 |
| `_database_connection` | External database connection details          |
| `_tuning`              | Performance tuning profile                    |
| `_flavor_features`     | `--add-feature`, `--remove-feature`, `flavor` |


## metadata.obsah.yaml Reference

The general `metadata.obsah.yaml` format is documented in the [Obsah playbook metadata guide](https://github.com/theforeman/obsah/blob/master/docs/source/development.rst#exposing-playbooks-using-metadata). Below is a quick reference followed by patterns specific to foremanctl.

### `help`

Short description shown in `--help` output. Required for every subcommand.

```yaml
help: |
  Pull necessary container images
```

### `variables`

Each key becomes an Ansible variable passed to the playbook. Obsah auto-converts `snake_case` names to `--hyphen-case` CLI flags (e.g. `foreman_initial_admin_password` becomes `--foreman-initial-admin-password`) unless overridden with `parameter`.


| Property    | Description                                                                                                                                          | Example                                         |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| `help`      | Description shown in `--help`. Required.                                                                                                             | `"Initial password for the admin user."`        |
| `parameter` | Override the auto-generated CLI flag name                                                                                                            | `--certificate-cname`, `vm_action` (positional) |
| `action`    | How the CLI handles the value. See actions table below.                                                                                              | `store`, `append_unique`, `store_true etc.`     |
| `choices`   | Restrict accepted values to a fixed list of options.                                                                                                 | `[internal, external]`                          |
| `type`      | Value type validation provided by Obsah (see `obsah.types` for available types).                                                                     | `FQDN`, `AbsolutePath`                          |
| `persist`   | Whether Obsah saves the value parameter to its answers file so it is reused on subsequent runs. Defaults to `true`. Set `false` to avoid persistance | `false`                                         |
| `dest`      | It controls which attribute name the parsed value is stored under. By default argparse uses the variable name, but dest overrides it.                                   | `features`                                      |


**Actions:**


| Action          | Behavior                                                              |
| --------------- | --------------------------------------------------------------------- |
| `store`         | Store a single value (default).                                       |
| `store_true`    | Boolean flag, sets the variable to `true` when present.               |
| `append`        | Collect multiple values into a list. Can be specified multiple times. |
| `append_unique` | Like `append`, but deduplicates values.                               |
| `remove`        | Remove a value from the list variable specified by `dest`.            |


**Examples:**

Simple variable with choices:

```yaml
variables:
  database_mode:
    help: Defaults to internal. Set to 'external' if using an external database.
    choices:
      - internal
      - external
```

Remove action paired with another variable (the `dest` field ties `remove_features` to the `features` list):

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

### Constraints for validating flag combinations

Foremanctl uses `constraints` to enforce rules between related flags:

```yaml
constraints:
  required_together:
    - [database_ssl_mode, database_ssl_ca]
  required_if:
    - ['database_mode', 'external', ['database_host']]
```

- `required_together` — all variables in the set must be provided if any one is.
In the example above, `database_ssl_mode` and `database_ssl_ca` must be provided together.
- `required_if` — variables that become required when another variable has a specific value.
In the example above, if `database_mode` is `external`, then `database_host` is required.

### Full example

Based on `src/playbooks/deploy/metadata.obsah.yaml`:

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
  certificates_cnames:
    help: Additional DNS name for Subject Alternative Names. Can be specified multiple times.
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

## How to Add a New Command

1. Create a directory under `src/playbooks/<command-name>/` (or `development/playbooks/` for dev tools).
2. Add `<command-name>.yaml` playbook file — the filename must match the directory name.
3. Add `metadata.obsah.yaml` with at least a `help` field.
4. If the command shares options with existing commands, use `include` to reference `_`-prefixed fragments rather than duplicating variable definitions.
5. Add roles to `src/roles/` or `development/roles/` as needed, using `snake_case` names.
6. Run `pytest tests/playbooks_test.py` to verify the playbook is discoverable, documented, and correctly named.
  > [!NOTE]
  > This test suite only covers `src/playbooks/` (it sets `OBSAH_DATA=src`).
7. Run `ansible-lint` to check for linting issues in your playbook and roles.

