# Foreman Development Environment

This document describes how to set up and use the Foreman development environment that deploys Foreman source code directly on the VM while using containerized backend services.

## Overview

The development environment provides:
- Git-based Foreman installation (cloned from GitHub)
- Containerized backend services (PostgreSQL, Redis, Candlepin, Pulp, Apache HTTP Server)
- Plugin support with registry system
- Development-specific configurations
- Direct Rails server access for debugging

## Prerequisites

- A running EL9 virtual machine, and inventory that contains knowledge of the VM. For example, using `./forge vms start`.
  - CentOS Stream 9 is recommended and tested
  - Other EL9 variants should work too. Please report if they do not.
- Run `./setup-environment` and activate the virtual environment

## Quick Start

### Using Vagrant VMs (Default)

1. **Start the development environment:**
   ```bash
   ./forge deploy-dev
   ```

2. **Access the environment:**
   - SSH into the VM: `vagrant ssh`
   - Navigate to Foreman directory: `cd /home/vagrant/foreman`
   - Start Rails server: `bundle exec foreman start`

3. **Access URLs:**
   - Foreman UI: `http://$(hostname -f):3000` (development server)
   - Production-style UI: `https://$(hostname -f)` (via Apache proxy)

### Deploying to a Remote Host

You can deploy directly to a remote host using the `--target-host` parameter:

```bash
# Deploy to a specific hostname or IP
./forge deploy-dev --target-host=my-server.example.com

# Deploy to an IP address
./forge deploy-dev --target-host=192.168.1.100
```

### SSH Authentication

When deploying to remote hosts that require SSH password authentication:

```bash
# Using environment variable
ANSIBLE_ASK_PASS=true ./forge deploy-dev --target-host=192.168.1.100
```

## Feature Management

Similarly to production deployments with `foremanctl`, using `forge` there is support for enabling `hammer` and `foreman-proxy` as features. Features can be enabled with `--add-feature=$feature`, which can be used multiple times.

By default `hammer` feature will set up `hammer-cli` and `hammer-cli-foreman`, `foreman-proxy` will set up `smart-proxy` itself. If any plugins are enabled, they're respective hammer or smart-proxy plugins will be set up as well.

All the projects set up as part of the feature are deployed as git checkouts.

## Plugin Management

Plugins are managed through the feature system. The development environment supports two mechanisms for enabling features:

- `--add-feature` enables a feature in its **production form** (gem/package).
- `--add-dev-feature` enables a feature in its **development form** (git checkout).

Feature definitions in `development/features.yaml` extend `src/features.yaml` with development-specific metadata (git repos, settings templates, etc.).

### Default Development Features

- `katello`
- `remote-execution` (and its dependency `dynflow`)

These are always set up from git checkouts.

### Enabling Additional Features

Use `--add-dev-feature` to set up a feature from git for active development:

```bash
# Enable features for development (git checkout)
./forge deploy-dev --add-dev-feature=ansible --add-dev-feature=discovery

# Mix production and development features
./forge deploy-dev --add-feature=puppet --add-dev-feature=ansible
```

Use `--add-feature` to enable a feature in production form without a git checkout.

## Development Workflow

### Initial Setup

After deployment, the environment includes:
- Cloned Foreman repository
- Installed Ruby and Node.js dependencies
- Database migrations and seeding
- Plugin repositories and configurations
- Development-specific settings
- if `hammer` feature was enabled, `hammer-cli` and its plugins
- if `foreman-proxy` feature was enabled
  - `smart-proxy` and its plugins
  - the development smart proxy registered into Foreman

## Architecture

### Service Integration

The development environment integrates:
- **Apache HTTP Server**: Provides HTTPS proxy to the Rails development server
- **Backend Services**: All services (PostgreSQL, Redis, Candlepin, Pulp) run in containers
- **Rails Development Server**: Runs directly on the VM for live debugging and development
- **Pulp Smart Proxy Registration**: Automatically configures Pulp integration during deployment
- **Hammer CLI**: Automatically sets up hammer for development, if `hammer` feature was enabled
- **Smart Proxy**: Automatically set up a smart proxy for development and registers it into Foreman, if `foreman-proxy` feature was enabled

### Certificates

Development certificates are copied to `/home/vagrant/foreman-certs/`:

- `proxy_ca.pem` - CA certificate
- `client_cert.pem` - Client certificate
- `client_key.pem` - Client private key
