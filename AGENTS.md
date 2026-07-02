## Foremanctl

foremanctl is a deployment tool for Foreman and Katello using Podman quadlets and Ansible, wrapping `obsah` for managed containerized deployments.

Two entry points:
- `foremanctl` — production deployment; uses `src/` as its data directory
- `forge` — development and testing; uses `development/` as its data directory

## Build & Test Commands

- Deploy: `./foremanctl deploy --foreman-initial-admin-password=changeme --tuning development`
- Test all: `./forge test` (requires a deployed VM)
- Test file: `python -m pytest tests/foreman_test.py -vv`
- Test single: `python -m pytest tests/foreman_test.py -vv -k test_name`
- Lint src: `cd src; ansible-lint`
- Lint dev: `cd development; ansible-lint`

## Key Conventions

- **obsah discovery**: every playbook directory needs a `metadata.obsah.yaml` — without it obsah won't expose the command; it defines CLI parameters, variable types, validation, and sub-playbook includes
- **Internal playbooks**: prefix with `_` (e.g. `_certificate_source`, `_tuning`) — these are composed into other playbooks, not invoked directly
- **`enabled_features`**: computed as `flavor_features + features`; never set this variable directly
- **Bare pytest won't work**: `./forge test` generates `.tmp/ssh-config` from the Ansible inventory before running pytest; run bare `pytest` only after that file exists
- **New roles**: production roles go in `src/roles/`, development-only roles in `development/roles/`

## Architecture

Production playbooks (`src/playbooks/`): `deploy/`, `checks/`, `features/`, `pull-images/`, plus `_`-prefixed internal playbooks.

Development playbooks (`development/playbooks/`): `vms/`, `test/`, `smoker/`, `deploy-dev/`, and utilities.

Configuration lookup:
- `src/vars/defaults.yml` — base defaults
- `src/vars/flavors/` — base feature sets per deployment flavor (e.g. `katello.yml`)
- `src/vars/tuning/` — resource profiles (development, medium, large, extra-large, extra-extra-large)
- `src/features.yaml` — canonical feature list

AI agent specifications (rules, skills, agent personas) live under `.agents/`.

## Additional Documentation

- [Development](DEVELOPMENT.md) — dev environment setup, virtualenv, dependencies
- [Playbooks and Roles](docs/developer/playbooks-and-roles.md) — playbook structure, naming, metadata
- [How to Add a Feature](docs/developer/how-to-add-a-feature.md) — end-to-end feature development
- [Feature Metadata](docs/developer/feature-metadata.md) — YAML schema for `src/features.yaml`
- [Check Roles](docs/developer/checks.md) — check role catalog and integration patterns
- [Testing](docs/developer/testing.md) — test infrastructure, fixtures, patterns
- [Parameters](docs/user/parameters.md) — installation parameter map; update when adding parameters
Developer docs:
- [Check roles](docs/developer/checks.md) - How to integrate check roles; update as checks are created/modified
- [Container Image Builds](docs/developer/container-image-builds.md) - Info on image naming, registries
- [Deployment Architecture](docs/developer/deployment.md)
- [Development Environment](docs/developer/development-environment.md) - Dev environment setup with Foreman from source
- [How to Add a Feature](docs/developer/how-to-add-a-feature.md) - End-to-end feature development
- [Playbooks and Roles](docs/developer/playbooks-and-roles.md) - Playbook structure, naming, metadata
- [Testing](docs/developer/testing.md) - Additional info on test infrastructure, fixtures, patterns

User docs:
- [Backup](docs/user/backup.md) - How to back up your data
- [Certificates](docs/user/certificates.md) - Overview of certificate sources
- [Parameters](docs/user/parameters.md) - Map of Foreman installation parameters; update as parameters are created/modified
- [Upgrade](docs/user/upgrade.md) - How to upgrade your Foreman server through foremanctl

- [CONTRIBUTING](CONTRIBUTING.md) - How to contribute
- [Development](DEVELOPMENT.md) - Foremanctl development overview
- [IOP](docs/iop.md) - Overview of insights on premise
- [Migration Guide](docs/migration-guide.md) - Migrating from foreman-installer to foremanctl
- [Release](RELEASE.md) - Info on Foremanctl releases
