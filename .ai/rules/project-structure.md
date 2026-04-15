---
name: project-structure
description: >-
  Canonical directory layout and structural conventions for the foremanctl
  repository. Reference for all agents when locating or creating files.
applies-to:
  - "*"
---

# Rules - Project Structure

Canonical layout of the foremanctl repository.

## Top-Level Overview

```shell
foremanctl              # Bash wrapper -> obsah (OBSAH_DATA=src)
forge                   # Bash wrapper -> obsah (OBSAH_DATA=development)
setup-environment       # Creates .venv, installs deps, builds collections
Makefile                # dist tarball + collection builds
Vagrantfile             # VM definitions for dev/CI
VERSION                 # Git-derived version string

CONTRIBUTING_AI.md      # AI development guide
DEVELOPMENT.md          # Human development guide
README.md               # Project overview
RELEASE.md              # Release process

.ansible-lint           # Repo-wide ansible-lint config
.packit.yml             # COPR build automation (RHEL 9)

src/                    # Production codebase (foremanctl)
development/            # Development codebase (forge)
tests/                  # pytest/testinfra tests
docs/                   # Documentation
inventories/            # Ansible inventory files
build/                  # Build artifacts (not in git)
.var/                   # Runtime state (not in git)
.ai/                    # AI agent specifications
```

## `src/` -- Production (foremanctl)

```shell
src/
  ansible.cfg                      # Ansible config (roles_path, plugins, callback)
  requirements.txt                 # Python deps (obsah, requests)
  requirements.yml                 # Ansible Galaxy collections
  features.yaml                    # Feature registry

  playbooks/
    deploy/                        # foremanctl deploy
      deploy.yaml
      metadata.obsah.yaml
    checks/                        # foremanctl checks
    features/                      # foremanctl features
    pull-images/                   # foremanctl pull-images
    _certificate_source/           # Shared fragment (not a command)
    _database_mode/                # Shared fragment
    _database_connection/          # Shared fragment
    _tuning/                       # Shared fragment
    _flavor_features/              # Shared fragment

  roles/
    foreman/                       # Foreman application server
    pulp/                          # Pulp content management
    candlepin/                     # Subscription management
    postgresql/                    # Database
    redis/                         # Cache/queue
    httpd/                         # Reverse proxy
    foreman_proxy/                 # Smart Proxy
    hammer/                        # CLI tool
    certificates/                  # Certificate management
    systemd_target/                # Service ordering
    pre_install/                   # Pre-deployment checks and setup
    post_install/                  # Post-deployment tasks
    check_*/                       # Validation roles

  vars/
    defaults.yml                   # Base defaults
    base.yaml                      # Base configuration
    images.yml                     # Container image references
    database.yml                   # Database configuration
    foreman.yml                    # Foreman configuration
    default_certificates.yml       # Default certificate config
    installer_certificates.yml     # Installer certificate config
    flavors/
      katello.yml                  # Katello flavor definition
    tuning/
      default.yml                  # Default resource profile
      development.yml              # Minimal resources for dev
      medium.yml / large.yml / ... # Scaling profiles

  callback_plugins/
    foremanctl.py                  # Custom Ansible callback
  filter_plugins/
    foremanctl.py                  # Custom Jinja2 filters
```

## `development/` -- Development (forge)

```shell
development/
  ansible.cfg                      # Ansible config (merges ../src/roles)
  requirements.txt                 # Dev/test Python deps
  requirements.yml                 # Dev Ansible Galaxy collections

  playbooks/
    vms/                           # forge vms (start/stop VMs)
    deploy-dev/                    # forge deploy-dev
    test/                          # forge test
    smoker/                        # forge smoker
    sos/                           # forge sos
    security/                      # forge security
    lock/                          # forge lock
    _flavor_features/              # Shared fragment

  roles/
    foreman_development/           # Dev Foreman setup
    git_repository/                # Git repo management
    foreman_installer_certs/       # Installer cert generation
```

## `tests/`

```shell
tests/
  conftest.py                      # Shared fixtures
  *_test.py                        # Integration tests (per component)
  unit/                            # Unit tests (no deployment needed)
  fixtures/                        # Test data (certs, manifests)
```

## `inventories/`

```shell
inventories/
  localhost                        # Local deployment (ansible_connection=local)
  local_vagrant                    # Vagrant-managed VMs
  broker.py                        # Dynamic inventory script
```

## Key Relationships

- `foremanctl` sets `OBSAH_DATA=src/` and executes obsah
- `forge` sets `OBSAH_DATA=development/` and executes obsah
- `development/ansible.cfg` includes `../src/roles` in its roles path, so dev playbooks can use production roles
- Collections are built into `build/collections/foremanctl` and `build/collections/forge` separately
- `.var/lib/foremanctl/` stores persistent deployment state and answers
