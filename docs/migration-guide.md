# Migrating from foreman-installer to foremanctl

## Overview

When upgrading from foreman-installer to foremanctl, the `foremanctl migrate` command helps convert your existing configuration to the new format.

This guide explains how to migrate your foreman-installer answer files to foremanctl configuration files.

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

1. **Generate the migrated configuration**:
   ```bash
   foremanctl migrate --output /var/lib/foremanctl/parameters.yaml
   ```

2. **Review the output** for any warnings about unmapped parameters

3. **Use the migrated configuration** with foremanctl:
   ```bash
   foremanctl deploy
   ```
   (foremanctl automatically loads configuration from `/var/lib/foremanctl/parameters.yaml`)

## Command Usage

### Basic Migration

Migrate from the default location (reads the currently active scenario):
```bash
foremanctl migrate --output /var/lib/foremanctl/parameters.yaml
```

### Custom Answer File

Migrate from a specific answer file:
```bash
foremanctl migrate --answer-file /path/to/custom-answers.yaml --output /var/lib/foremanctl/parameters.yaml
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

Once you've generated and reviewed the migrated configuration:

1. **Save it to the foremanctl parameters file**:
   ```bash
   # Either generate directly to the parameters file
   foremanctl migrate --output /var/lib/foremanctl/parameters.yaml

   # Or copy after review
   foremanctl migrate --output /tmp/migrated.yaml
   # Review /tmp/migrated.yaml
   cp /tmp/migrated.yaml /var/lib/foremanctl/parameters.yaml
   ```

2. **Deploy using foremanctl**:
   ```bash
   foremanctl deploy
   ```

   The `foremanctl deploy` command automatically loads configuration from `/var/lib/foremanctl/parameters.yaml`.
