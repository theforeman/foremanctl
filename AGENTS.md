# AI Development Guide

This file provides guidance to AI tools and agents when working with code in this repository. It is intentionally tool-agnostic -- it works with Claude Code, Cursor, GitHub Copilot, and any other AI assistant.

## Project Overview

foremanctl is a deployment tool for Foreman and Katello using Podman quadlets and Ansible. It provides a command-line interface built on top of `obsah` (an Ansible wrapper) for managing containerized Foreman deployments.

The repository contains two main wrapper scripts:

- `foremanctl` - Production deployment and management
- `forge` - Development environment management and testing

Both scripts wrap `obsah`, which provides a structured way to run Ansible playbooks with parameter validation and persistence.

## Supported Platforms

- **Target OS**: CentOS Stream 9, RHEL 9
- **Ansible**: ansible-core 2.16+
- **Python**: 3.9+ (as shipped with CentOS Stream 9)
- **Podman**: As shipped with CentOS Stream 9 / RHEL 9
- **Vagrant**: 2.2+ (for development VMs)
- **Virtualization**: Libvirt with Vagrant Libvirt provider

## AI Specifications

Detailed agent, command, rule, and skill specifications live under `.agents/`. These are tool-agnostic Markdown files with YAML frontmatter that any AI tool can parse or ignore.

### Directory Structure

```shell
.agents/
  agents/          # Specialist agent personas with defined scopes
  rules/           # Coding standards and constraints (all agents must follow)
  skills/          # Domain knowledge references
```

### Agents (`.agents/agents/`)

Focused personas with defined scopes and technology boundaries:

| Agent | Purpose |
|-------|---------|
| `ansible-playbook-agent` | Playbooks and `metadata.obsah.yaml` files |
| `ansible-role-agent` | Roles, tasks, handlers, templates |
| `feature-agent` | End-to-end feature addition workflow |
| `test-agent` | pytest/testinfra tests |
| `lint-agent` | ansible-lint and Python linting |
| `podman-agent` | Podman quadlets, containers, secrets |
| `code-review-agent` | Read-only code review and analysis |

### Commands (`.agents/commands/`)

Reusable workflows invoked by name:

| Command | Purpose |
|---------|---------|
| `add-feature` | Register and configure a new foremanctl feature |
| `run-tests` | Run the test suite with prerequisites check |
| `lint` | Run ansible-lint across both codebases |
| `deploy-dev` | Full development environment setup |
| `add-playbook` | Scaffold a new CLI subcommand |
| `catchup` | Branch activity summary since last contribution |

### Rules (`.agents/rules/`)

Hard constraints all agents must follow:

| Rule | Scope |
|------|-------|
| `ansible-conventions` | Playbook/role naming, FQCN, metadata requirements |
| `podman-secrets` | Secret naming conventions and required labels |
| `testing-conventions` | Test file naming, fixture usage, patterns |
| `safety` | Destructive command blocklist, production awareness |
| `project-structure` | Canonical directory layout reference |

### Skills (`.agents/skills/`)

Domain knowledge references (each has `SKILL.md` and optional `references/`):

| Skill | Domain |
|-------|--------|
| `obsah-metadata` | `metadata.obsah.yaml` schema deep reference |
| `podman-quadlets` | Podman quadlets, images, systemd integration |
| `foreman-ecosystem` | Foreman, Katello, Pulp, Candlepin, Smart Proxy |
| `ansible-collections` | Galaxy collections, installation, FQCN usage |
| `certificate-management` | Certificate sources, roles, and configuration |

## Development Setup

```bash
./setup-environment
source .venv/bin/activate
```

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

### Building

```bash
# Build distribution tarball
make dist

# Build collections (automatically happens as part of dist)
make build/collections/foremanctl
make build/collections/forge
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
- Checks: `check_hostname`, `check_database_connection`, `check_system_requirements`, `check_subuid_subgid`
- Lifecycle: `pre_install`, `post_install`

### Configuration System

Configuration is managed through:

1. **Vars files** (`src/vars/`):
   - `defaults.yml` - Base defaults
   - `flavors/` - Deployment flavors (currently only `katello.yml`)
   - `tuning/` - Resource profiles (default, development, medium, large, extra-large, extra-extra-large)
   - `images.yml` - Container image references
   - `database.yml`, `foreman.yml` - Service-specific configuration

2. **Podman secrets**: Configuration files and credentials are stored as Podman secrets following naming conventions:
   - Config files: `<role_namespace>-<filename>-<extension>` or `<role_namespace>-<app>-<filename>-<extension>`
   - Strings: `<role_namespace>-<descriptive_name>` or `<role_namespace>-<app>-<descriptive_name>`
   - All secrets include labels: `filename`, `app`

View secrets with:

```bash
podman secret ls
podman secret inspect --showsecret --format "{{.SecretData}}" <secret-name>
```

### Custom Plugins

- `src/callback_plugins/foremanctl.py` - Ansible callback plugin for foremanctl-specific output
- `src/filter_plugins/foremanctl.py` - Custom Jinja2 filters

### Features and Flavors

Features are modular capabilities that can be enabled. See [docs/developer/how-to-add-a-feature.md](docs/developer/how-to-add-a-feature.md) for the complete feature development guide.

Current features:

- `hammer` - CLI tool
- `foreman-proxy` - Smart proxy functionality
- `remote-execution` - Remote execution via SSH
- `google` - Google Compute Engine integration
- `azure-rm` - Azure Resource Manager integration
- `katello` - Content and subscription management

Flavors define the base feature set:

- `katello` - Currently the only flavor (Foreman 3.18 + Katello 4.20 + Pulp 3.85 + Candlepin 4.6)

The `enabled_features` variable is computed as: `flavor_features + features`

### Deployment Variables

Key deployment parameters:

- `certificate_source` - Where certificates come from (`default`, `installer`)
- `database_mode` - Database deployment (`internal`, `external`)
- `tuning` - Resource allocation profile
- `flavor` - Base feature set
- `foreman_initial_admin_username/password` - Initial admin credentials
- `foreman_puma_workers` - Puma worker count
- `pulp_worker_count` - Pulp worker count (defaults to min(8, CPU cores))

## Testing Architecture

Tests use pytest with testinfra for infrastructure testing. Key fixtures in `tests/conftest.py`:

- `server_hostname`, `server_fqdn` - Default to `quadlet` / `quadlet.example.com`
- `client_hostname`, `client_fqdn` - Default to `client` / `client.example.com`
- `certificates` - Certificate configuration based on `--certificate-source`
- SSH configuration generated from Ansible inventory at `.tmp/ssh-config`

Test files follow the pattern `tests/<component>_test.py` and use testinfra's server fixture to execute commands and check system state.

## Build System

The Makefile handles:

- Building the distribution tarball (includes git archive + collections)
- Installing Ansible collections into `build/collections/foremanctl` and `build/collections/forge`
- Collections are installed from `src/requirements-lock.yml` (preferred) or `src/requirements.yml`

## Inventories

Three inventory configurations:

- `localhost` - Local deployment
- `local_vagrant` - Vagrant-managed local VMs
- `broker.py` - Dynamic inventory script

## Developer Documentation

Additional developer guides (from PR [#435](https://github.com/theforeman/foremanctl/pull/435)):

- [How to Add a Feature](docs/developer/how-to-add-a-feature.md) -- end-to-end feature development
- [Playbooks and Roles](docs/developer/playbooks-and-roles.md) -- playbook structure, naming, metadata
- [Testing](docs/developer/testing.md) -- test infrastructure, fixtures, patterns
- [Deployment Design](docs/developer/deployment.md) -- deployment architecture
- [Container Image Builds](docs/developer/container-image-builds.md) -- image naming, registries
- [Development Environment](docs/developer/development-environment.md) -- dev setup with git Foreman

## Git Workflow

Main branch: `master`
