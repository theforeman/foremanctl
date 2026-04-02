# Foreman deployment using Podman and Ansible

This repository provides tooling for a deployment of Foreman and Katello using Podman quadlets and Ansible.

## Overview

**foremanctl** is a production CLI tool for deploying and managing Foreman and Katello as containerized services managed by systemd through [Podman Quadlets](https://docs.podman.io/en/latest/markdown/podman-quadlet.1.html). It is a wrapper around [Obsah](https://github.com/theforeman/obsah) and runs Ansible playbooks from `src/`.

### Key Technologies

- **[Podman Quadlets](https://docs.podman.io/en/latest/markdown/podman-quadlet.1.html)** - Declarative container-to-systemd service conversion
- **[Ansible](https://docs.ansible.com/)** - Infrastructure automation and deployment orchestration
- **[Obsah](https://github.com/theforeman/obsah)** - Ansible playbook execution engine
- **[pytest](https://pytest.org/)** with [testinfra](https://testinfra.readthedocs.io/) - Testing framework

## forge

**forge** is a development CLI tool for working on foremanctl. Like `foremanctl`, it is a wrapper around [Obsah](https://github.com/theforeman/obsah) but runs playbooks from `development/`. It provides commands for managing Vagrant VMs, running tests, and setting up foreman [development environment](docs/developer/development-environment.md).

> [!NOTE]
> `forge` is also used in CI for tests.

## Packages

### RPM

Snapshot RPM packages of `foremanctl` and its dependencies can be found in the [`@theforeman/foremanctl` copr](https://copr.fedorainfracloud.org/coprs/g/theforeman/foremanctl/)

```bash
dnf copr enable @theforeman/foremanctl rhel-9-x86_64
dnf install foremanctl
```

## Compatibility

### Foreman

Foreman 3.18 (with Katello 4.20, Pulp 3.85 and Candlepin 4.6).

### Ansible

`ansible-core` 2.16

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to get started.

## Releasing a new version

To release a new version of foremanctl, follow the instructions in [RELEASE.md](RELEASE.md).

## Getting Help

- **Issues**: [github.com/theforeman/foremanctl/issues](https://github.com/theforeman/foremanctl/issues)
- **Matrix Chat**: [#theforeman-dev on matrix.org](https://matrix.to/#/#theforeman-dev:matrix.org)
- **Community**: [Foreman Community Forum](https://community.theforeman.org/)
