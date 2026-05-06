# Migrating from foreman-installer to foremanctl

## Overview

When upgrading from foreman-installer to foremanctl, the `foremanctl migrate` command helps convert your existing configuration to the new format.

By default, `foremanctl migrate` previews the migration without making any changes. Use `--apply` to perform the actual migration.

## Prerequisites

Before migrating, ensure the following:

1. **Foreman deployment using foreman-installer** - You should have an existing Foreman deployment has been installed using foreman-installer and has an answers file to migrate from.

2. **foremanctl is installed** on the system:
   ```bash
   # Enable the foremanctl repository
   dnf copr enable @theforeman/foremanctl rhel-9-x86_64

   # Install foremanctl
   dnf install foremanctl
   ```

   For more installation options, see the main [README](../README.md#packages).

## Migration Workflow

1. **Preview the migration** (no changes are made):
   ```bash
   foremanctl migrate
   ```

2. **Review the output** for any warnings about unmapped parameters

3. **Apply the migration** when satisfied:
   ```bash
   foremanctl migrate --apply
   ```

4. **Deploy using foremanctl**:
   ```bash
   foremanctl deploy
   ```

## Command Usage

### Preview Migration

Preview the migrated configuration without making any changes:
```bash
foremanctl migrate
```

This shows:
- Mapped answer file parameters and their new values
- Unmappable parameters that need manual review
- Certificate state detected on the system

### Apply Migration

Perform the actual migration:
```bash
foremanctl migrate --apply
```

This:
- Writes migrated parameters to the foremanctl configuration
- Normalizes installer certificates into `/var/lib/foremanctl/certs/`
- Backs up the original `/root/ssl-build/` directory to `/root/ssl-build.bak/`

### Custom Answer File

Migrate from a specific answer file:
```bash
foremanctl migrate --answer-file /path/to/custom-answers.yaml
foremanctl migrate --apply --answer-file /path/to/custom-answers.yaml
```

### Write to a Custom Path

Write the migrated parameters to a specific file for inspection:
```bash
foremanctl migrate --output /tmp/migrated.yaml
```

## Command Options

- `--apply` - Perform the migration. Without this flag, only previews what would happen.
- `--answer-file PATH` - Path to the foreman-installer answer file. If not specified, reads the currently active scenario and extracts the answer file path from it.
- `--output PATH` - Path for the migrated configuration. If not specified and `--apply` is used, writes to the foremanctl configuration.

> [!NOTE]
> Unlike other `foremanctl` commands, migrate does not persist parameters between runs. Each migration is independent.

## Parameter Mappings

The migrate command automatically maps foreman-installer parameters to foremanctl parameters. For a complete list of all parameter mappings, see the [Parameters documentation](parameters.md#mapping).

## Example

Below is an example showing how the transformation works:

### Input (foreman-installer format)

```yaml
foreman:
  db_host: database.example.com
  db_port: 5432
  db_database: foreman
  db_username: foreman_user
  db_password: secret123
  db_manage: true
  initial_admin_username: admin
  initial_admin_password: changeme
```

### Output (foremanctl format)

```yaml
database_host: database.example.com
database_port: 5432
database_mode: external
foreman_database_name: foreman
foreman_database_password: secret123
foreman_database_user: foreman_user
foreman_initial_admin_password: changeme
foreman_initial_admin_username: admin
```

## Handling Unmapped Parameters

When the migration completes, you may see warnings like:

> [!WARNING]  
> The following parameters could not be mapped:
>  - katello::enable_ostree
> - foreman::some_other_param

These parameters need to be manually reviewed and added to the new configuration if needed. Check the [parameters documentation](parameters.md) for equivalent foremanctl parameters.

## Using the Migrated Configuration

Once you've applied the migration:

1. **Deploy using foremanctl**:
   ```bash
   foremanctl deploy
   ```

   The `foremanctl deploy` command automatically loads configuration from `/var/lib/foremanctl/parameters.yaml`.
