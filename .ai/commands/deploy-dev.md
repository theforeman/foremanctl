---
name: deploy-dev
description: >-
  End-to-end development environment setup: creates the virtualenv, starts
  VMs, and deploys Foreman for development and testing.
argument-hint: "[--tuning PROFILE] [--add-feature FEATURE]"
references:
  - DEVELOPMENT.md
---

# Commands - Deploy Development Environment

Set up a complete foremanctl development environment from scratch.

## Input

`$ARGUMENTS` -- optional deployment customizations:
- `--tuning PROFILE` -- resource profile (default: `development`). Options: `default`, `development`, `medium`, `large`, `extra-large`, `extra-extra-large`
- `--add-feature FEATURE` -- additional features to enable (e.g. `hammer`, `remote-execution`)

## Prerequisites

The host machine needs:
- Vagrant 2.2+
- ansible-core 2.16+
- Vagrant Libvirt provider plugin
- Virtualization enabled in BIOS

## Workflow

### 1. Set Up the Python Environment

```bash
./setup-environment
source .venv/bin/activate
```

This creates a virtualenv, installs dependencies from `src/requirements.txt` and `development/requirements.txt`, and builds Ansible collections.

### 2. Start Development VMs

```bash
./forge vms start
```

This provisions Vagrant VMs defined in the `Vagrantfile`:
- `quadlet` (quadlet.example.com) -- Foreman server
- `client` (client.example.com) -- client for registration tests
- `database` (database.example.com) -- external database testing

### 3. Deploy Foreman

```bash
./foremanctl deploy --foreman-initial-admin-password=changeme --tuning development
```

Add features as needed:

```bash
./foremanctl deploy --add-feature hammer
./foremanctl deploy --add-feature remote-execution
```

### 4. Verify Deployment

```bash
./foremanctl features
```

### 5. Run Tests (Optional)

```bash
./forge test
```

## Teardown

```bash
./forge vms stop
```

## Common Issues

| Issue | Solution |
|-------|----------|
| Vagrant Libvirt not found | Install: `vagrant plugin install vagrant-libvirt` |
| VM fails to start | Check virtualization is enabled, run `vagrant destroy` and retry |
| Collection build fails | Delete `build/` directory and re-run `./setup-environment` |
| Deploy hangs | Check VM is reachable: `vagrant ssh quadlet` |

## Important

- The deployment modifies the target VMs. Do not run against production systems.
- The `development` tuning profile uses minimal resources suitable for local development.
- Hammer is not deployed by default -- add it explicitly if needed.
