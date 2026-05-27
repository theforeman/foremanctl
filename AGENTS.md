## Foremanctl

foremanctl is a deployment tool for Foreman and Katello using Podman quadlets and Ansible. It provides a command-line interface built on top of `obsah` (an Ansible wrapper) for managing containerized Foreman deployments.

The repository contains two main wrapper scripts:

- `foremanctl` - Production deployment and management
- `forge` - Development environment management and testing

Both scripts wrap `obsah`, which provides a structured way to run Ansible playbooks with parameter validation and persistence.

## AI Specifications

Detailed agent, command, rule, and skill specifications live under `.agents/`. These are tool-agnostic Markdown files with YAML frontmatter that any AI tool can parse or ignore.

### Directory Structure

```shell
.agents/
  agents/          # Specialist agent personas with defined scopes
  rules/           # Coding standards and constraints (all agents must follow)
  skills/          # Domain knowledge references
```

### Workflow Chains

These pipelines connect skills into end-to-end workflows. Individual skill files don't describe these relationships.

TODO

## Development Setup

See [Development Guide](DEVELOPMENT.md) for the instructions.

This creates a virtualenv and installs all dependencies including ansible-core 2.16+.

## Common Commands

### Development Environment

```bash
# Start development VM
./forge vms start

# Deploy Foreman in development mode
./foremanctl deploy --foreman-initial-admin-password=changeme --tuning development

# Stop development VM
./forge vms stop
```

### Testing

```bash
# Run all tests (requires a deployed environment)
./forge test

# Run smoker tests
./forge smoker

# Run specific test file
python -m pytest tests/foreman_test.py -vv

# Run tests with specific configuration
python -m pytest --certificate-source=installer --database-mode=external
```

Tests use pytest with testinfra and connect to VMs via SSH. The test playbook (`development/playbooks/test/test.yaml`) generates `.tmp/ssh-config` from the Ansible inventory before running pytest.

See [docs/developer/testing.md](docs/developer/testing.md) for the full testing guide.

### Linting

```bash
# Run ansible-lint (configured in .ansible-lint)
cd src; ansible-lint
cd development; ansible-lint
```

## Architecture

### obsah Integration

Both `foremanctl` and `forge` are bash wrappers that set environment variables and execute `obsah`.

The key difference:

- `foremanctl`: Uses `src/` as data directory, targets production deployment
- `forge`: Uses `development/` as data directory, includes development-specific playbooks

obsah playbooks are discovered via `metadata.obsah.yaml` files which define:

- Command-line parameters and validation
- Help text
- Variable definitions with choices and types
- Included sub-playbooks

See [docs/developer/playbooks-and-roles.md](docs/developer/playbooks-and-roles.md) for the full playbook and role guide.

### Playbook Organization

**Production playbooks** (`src/playbooks/`):

- `deploy/` - Main deployment playbook
- `checks/` - System requirement checks
- `features/` - Feature management
- `pull-images/` - Container image pulling
- Prefixed with `_` - Internal/included playbooks (e.g., `_certificate_source`, `_database_mode`, `_tuning`, `_flavor_features`)

**Development playbooks** (`development/playbooks/`):

- `vms/` - VM lifecycle management
- `test/` - Test execution
- `smoker/` - Smoker test execution
- `deploy-dev/` - Development deployment variations
- `security/`, `sos/`, `lock/` - Utilities

### Roles

Roles in `src/roles/` correspond to services and deployment stages:

- Service roles: `foreman`, `pulp`, `candlepin`, `postgresql`, `redis`, `httpd`
- Feature roles: `hammer`, `foreman_proxy`
- Infrastructure: `certificates`, `systemd_target`
- Lifecycle: `pre_install`, `post_install`
- Checks: `check_*` roles; see [documentation](docs/developer/checks.md) for more info

### Configuration System

Configuration is managed through:

1. **Vars files** (`src/vars/`):
   - `defaults.yml` - Base defaults
   - `flavors/` - Deployment flavors (currently only `katello.yml`)
   - `tuning/` - Resource profiles (default, development, medium, large, extra-large, extra-extra-large)
   - `images.yml` - Container image references
   - `database.yml`, `foreman.yml` - Service-specific configuration

2. **Podman secrets**: See the `Service Configuration` section in the `DEPLOYMENT.md` file.

### Custom Plugins

- `src/callback_plugins/foremanctl.py` - Ansible callback plugin for foremanctl-specific output
- `src/filter_plugins/foremanctl.py` - Custom Jinja2 filters

### Features and Flavors

Features are modular capabilities that can be enabled. See [docs/developer/how-to-add-a-feature.md](docs/developer/how-to-add-a-feature.md) for the complete feature development guide.

For the list of current features, read the `src/features.yaml` file.

Flavors define the base feature set, see the flavor files in the `src/vars/flavors` directory.

The `enabled_features` variable is computed as: `flavor_features + features`

### Deployment Variables

## Testing Architecture

Tests use pytest with testinfra for infrastructure testing. Key fixtures in `tests/conftest.py`:

- `server_hostname`, `server_fqdn` - Default to `quadlet` / `quadlet.example.com`
- `client_hostname`, `client_fqdn` - Default to `client` / `client.example.com`
- `certificates` - Certificate configuration based on `--certificate-source`
- SSH configuration generated from Ansible inventory at `.tmp/ssh-config`

Test files follow the pattern `tests/<component>_test.py` and use testinfra's server fixture to execute commands and check system state.

## Additional Documentation

Developer docs:
- [Check roles](docs/developer/checks.md) - How to integrate check roles; update as checks are created/modified
- [Container Image Builds](docs/developer/container-image-builds.md) - Info on image naming, registries
- [Deployment Architecture](docs/developer/deployment.md)
- [Development Environment](docs/developer/development-environment.md) - Dev environment setup with Foreman from source
- [How to Add a Feature](docs/developer/how-to-add-a-feature.md) - End-to-end feature development
- [Playbooks and Roles](docs/developer/playbooks-and-roles.md) - Playbook structure, naming, metadata
- [Testing](docs/developer/testing.md) - Additional info on test infrastructure, fixtures, patterns

User docs:
- [Certificates](docs/user/certificates.md) - Overview of certificate sources
- [Parameters](docs/user/parameters.md) - Map of Foreman installation parameters; update as parameters are created/modified

- [CONTRIBUTING](CONTRIBUTING.md) - How to contribute
- [Development](DEVELOPMENT.md) - Foremanctl development overview
- [IOP](docs/iop.md) - Overview of insights on premise
- [Migration Guide](docs/migration-guide.md) - Migrating from foreman-installer to foremanctl
- [Release](RELEASE.md) - Info on Foremanctl releases