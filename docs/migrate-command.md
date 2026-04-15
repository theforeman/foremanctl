# Migrating from foreman-installer to foremanctl

## Overview

When upgrading from foreman-installer to foremanctl, the `foremanctl migrate` command helps convert your existing configuration to the new format.

This guide explains how to migrate your foreman-installer answer files to foremanctl configuration files.

## Migration Workflow

1. **Generate the migrated configuration**:
   ```bash
   foremanctl migrate --output /etc/foreman/config.yaml
   ```

2. **Review the output** for any warnings about unmapped parameters

3. **Use the migrated configuration** with foremanctl:
   ```bash
   foremanctl deploy
   ```
   (foremanctl automatically loads configuration from `/etc/foreman/config.yaml`)

## Command Usage

### Basic Migration

Migrate from the default location (reads the currently active scenario):
```bash
foremanctl migrate --output /etc/foreman/config.yaml
```

### Custom Answer File

Migrate from a specific answer file:
```bash
foremanctl migrate --answer-file /path/to/custom-answers.yaml --output /etc/foreman/config.yaml
```

### Output to stdout

Preview the migrated configuration without writing a file:
```bash
foremanctl migrate
```

## Command Options

- `--answer-file PATH` - Path to the foreman-installer answer file. If not specified, reads the currently active scenario and extracts the answer file path from it.
- `--output PATH` - Path for the migrated configuration (default: stdout)

> [!NOTE]
> Unlike other `foremanctl` commands, migrate does not persist parameters between runs. Each migration is independent.

## Parameter Mappings

| Old Parameter | New Parameter | Transformation |
|---------------|---------------|----------------|
| `foreman::db_host` | `database_host` | - |
| `foreman::db_port` | `database_port` | - |
| `foreman::db_database` | `foreman_database_name` | - |
| `foreman::db_username` | `foreman_database_user` | - |
| `foreman::db_password` | `foreman_database_password` | - |
| `foreman::db_manage` | `database_mode` | true→"internal", false→"external" |
| `foreman::initial_admin_username` | `foreman_initial_admin_username` | - |
| `foreman::initial_admin_password` | `foreman_initial_admin_password` | - |
| `foreman::server_ssl_cert` | `server_certificate` | - |
| `foreman::server_ssl_key` | `server_key` | - |
| `foreman::server_ssl_ca` | `ca_certificate` | - |

## Example

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
database_mode: internal
foreman_database_name: foreman
foreman_database_password: secret123
foreman_database_user: foreman_user
foreman_initial_admin_password: changeme
foreman_initial_admin_username: admin
```

## Handling Unmapped Parameters

When the migration completes, you may see warnings like:

```
Warning: The following parameters could not be mapped:
  - katello::enable_ostree
  - foreman::some_other_param
```

These parameters need to be manually reviewed and added to the new configuration if needed. Check the [parameters documentation](parameters.md) for equivalent foremanctl parameters.
