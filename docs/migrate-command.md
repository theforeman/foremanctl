# Migrate Command

## Overview

The `foremanctl migrate` command converts foreman-installer answer files to the new foremanctl configuration format.

## Usage

### Basic Usage

```bash
# Migrate from default location
foremanctl migrate --output /tmp/new-config.yaml

# Migrate from custom location
foremanctl migrate --answer-file /path/to/answers.yaml --output /tmp/config.yaml

# Migrate from backup
foremanctl migrate --root /backup --output /tmp/config.yaml

# Output to stdout
foremanctl migrate --answer-file /path/to/answers.yaml
```

### Command Options

- `--answer-file PATH` - Path to the foreman-installer answer file (default: `/etc/foreman-installer/scenarios.d/satellite.yaml`)
- `--output PATH` - Path for the migrated configuration (default: stdout)
- `--root PATH` - Root directory for finding the answer file, useful for migrations from backups (default: /)

## How It Works

1. **Reads** the old YAML answer file
2. **Parses** the nested parameter structure (e.g., `foreman::db_host`)
3. **Maps** old parameter names to new names using a mapping table
4. **Transforms** values where needed (e.g., boolean to string)
5. **Writes** the new configuration file
6. **Reports** any unmappable parameters as warnings (does not fail)

## Parameter Mapping

The migration uses a hardcoded mapping table in `src/playbooks/migrate/library/migrate_answers.py`:

```python
PARAMETER_MAP = {
    # Database
    ('foreman', 'db_host'): 'database_host',
    ('foreman', 'db_port'): 'database_port',
    ('foreman', 'db_database'): 'foreman_database_name',
    ('foreman', 'db_username'): 'foreman_database_user',
    ('foreman', 'db_password'): 'foreman_database_password',
    ('foreman', 'db_manage'): ('database_mode', cast_database_mode),

    # Foreman
    ('foreman', 'initial_admin_username'): 'foreman_initial_admin_username',
    ('foreman', 'initial_admin_password'): 'foreman_initial_admin_password',

    # Certificates
    ('foreman', 'server_ssl_cert'): 'server_certificate',
    ('foreman', 'server_ssl_key'): 'server_key',
    ('foreman', 'server_ssl_ca'): 'ca_certificate',

    # TODO: Add more mappings here...
}
```

### Adding New Mappings

To add new parameter mappings:

1. Open `src/playbooks/migrate/library/migrate_answers.py`
2. Add entries to the `PARAMETER_MAP` dictionary
3. Use format: `(old_module, old_param): new_param`
4. For transformations: `(old_module, old_param): (new_param, transform_function)`
5. To ignore a parameter: `(old_module, old_param): 'IGNORE'`

## Example

### Input (Old Format)

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

### Output (New Format)

```yaml
ca_certificate: /etc/pki/tls/certs/ca.crt
database_host: database.example.com
database_mode: internal
database_port: 5432
foreman_database_name: foreman
foreman_database_password: secret123
foreman_database_user: foreman_user
foreman_initial_admin_password: changeme
foreman_initial_admin_username: admin
```

## Testing

Run the unit tests:

```bash
python -m pytest tests/unit/migrate_test.py -v
```

Test with a sample file:

```bash
# Create test file
cat > /tmp/test-answers.yaml <<EOF
foreman:
  db_host: localhost
  db_port: 5432
  db_manage: true
EOF

# Run migration
./foremanctl migrate --answer-file /tmp/test-answers.yaml
```
