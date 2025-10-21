# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Foremanctl is a Foreman and Katello deployment tool using Podman quadlets and Ansible. It supports Foreman 3.16, Katello 4.18, Pulp 3.73, and Candlepin 4.6, targeting ansible-core 2.14 as present in CentOS Stream 9.

## Development Environment Setup

Initialize the development environment:
```bash
./setup-environment
source .venv/bin/activate
```

This creates a Python virtual environment and installs dependencies from `src/requirements.txt` and `development/requirements.txt`, then builds Ansible collections for both production (`foremanctl`) and development (`forge`) use.

## Core Architecture

### CLI Tools
- `./foremanctl` - Production deployment tool using obsah with production Ansible collections
- `./forge` - Development/testing tool using obsah with development Ansible collections

Both tools are bash wrappers around the `obsah` CLI tool that set environment variables:
- `OBSAH_NAME` - Tool identifier
- `OBSAH_DATA` - Ansible data directory (`src` for foremanctl, `development` for forge)
- `OBSAH_INVENTORY` - Ansible inventory path
- `OBSAH_STATE` - State persistence directory
- `ANSIBLE_COLLECTIONS_PATH` - Path to built collections

### Directory Structure
- `src/` - Production Ansible roles, playbooks, and configurations
- `development/` - Development-specific Ansible configurations
- `tests/` - pytest-based test suite with testinfra integration
- `inventories/` - Ansible inventory configurations
- `build/collections/` - Built Ansible collections (generated)

### Ansible Roles
Key roles in `src/roles/`:
- `certificates` - Certificate management and issuance
- `foreman` - Foreman application deployment
- `candlepin` - Candlepin subscription management
- `pulp` - Pulp content management
- `postgresql` - Database setup
- `httpd` - Web server configuration
- `redis` - Redis cache configuration
- `hammer` - Hammer CLI setup

## Common Development Tasks

### VM-based Development and Testing
```bash
# Start development environment
./forge vms start

# Deploy Foreman with default settings
./foremanctl deploy --foreman-initial-admin-password=changeme

# Setup hammer CLI (optional)
./forge setup-repositories
./foremanctl setup-hammer

# Run all tests
./forge test

# Stop environment
./forge vms stop
```

### Building and Collections
```bash
# Build production collections
make build/collections/foremanctl

# Build development collections
make build/collections/forge

# Create distribution tarball
make dist
```

### Testing
Tests use pytest with testinfra for infrastructure testing and apypie for Foreman API testing. Test configuration is in `tests/conftest.py` with fixtures for:
- Server and client connection via Vagrant SSH
- Foreman API client with authentication
- Certificate management (default vs installer certificates)
- Katello entities (organizations, products, repositories, content views, etc.)

Run individual test files:
```bash
# Run specific test module
pytest tests/foreman_test.py

# Run with specific certificate source
pytest --certificate-source=installer tests/
```

## Configuration Management

### Service Configuration
Services use Podman secrets for configuration files, following naming conventions:
- Config files: `<role_namespace>-<filename>-<extension>`
- Strings: `<role_namespace>-<descriptive_name>`
- With app context: `<role_namespace>-<app>-<filename>-<extension>`

View configurations:
```bash
# List all secrets
podman secret ls

# View specific secret
podman secret inspect --showsecret --format "{{.SecretData}}" <secret-name>
```

### Ansible Collections
Production requirements in `src/requirements.yml`:
- `community.postgresql` - PostgreSQL management
- `community.crypto` - Certificate management
- `ansible.posix` - POSIX utilities
- `containers.podman` - Podman container management
- `theforeman.foreman` - Foreman-specific modules

Development requirements in `development/requirements.yml` include additional collections for testing and VM management.

## Package Management

RPM packages available via COPR:
```bash
dnf copr enable @theforeman/foremanctl rhel-9-x86_64
dnf install foremanctl
```

## Important Notes

- Uses Vagrant with libvirt provider for VM-based development
- All Ansible configuration managed through obsah CLI wrapper
- State persistence handled automatically via `OBSAH_STATE` directory
- Test fixtures create temporary Katello entities that are cleaned up automatically
- Certificate management supports both default and installer-provided certificates