# Foreman Development Environment

This document describes how to set up and use the Foreman development environment that deploys Foreman source code directly on the VM while using containerized backend services.

## Overview

The development environment provides:
- Git-based Foreman installation (cloned from GitHub)
- Containerized backend services (PostgreSQL, Valkey, Candlepin, Pulp, Apache HTTP Server)
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

### Defining New Hosts

You can define custom hosts in boxes.yaml:

```
---
# User-local box definitions (this file is gitignored)
# Each entry becomes a vagrant box. Available settings:
#   box:       base box (default: centos/stream9)
#   memory:    RAM in MB (default: 3072)
#   cpus:      CPU count (default: 1)
#   disk_size: disk in GB (default: 50)

katello-production:
  memory: 12288
  cpus: 4
  disk_size: 50
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

## Custom Container Images

### Using Official Pulp Containers

The Foreman development environment uses official Pulp containers from [pulp-oci-images](https://github.com/theforeman/pulp-oci-images) which include all necessary plugins including `pulp-smart-proxy` by default.

The official containers provide:
- All Katello-supported Pulp plugins (ansible, container, deb, ostree, rpm, python, smart_proxy)
- Proper service wrapper scripts and configuration

### Building Custom Pulp Containers

For development scenarios requiring specific Pulp plugin versions or compatibility fixes, you can build custom Pulp container images using the [`pulp-development` project](https://github.com/theforeman/pulp-oci-images/tree/main/images/pulp-development) in pulp-oci-images.

To pin specific versions, edit `images/pulp-development/requirements.txt` in the cloned repository (see the [pulp-oci-images README](https://github.com/theforeman/pulp-oci-images#development) for details):

```bash
git clone https://github.com/theforeman/pulp-oci-images.git
cd pulp-oci-images

# Optionally pin versions in images/pulp-development/requirements.txt
# e.g., change "pulpcore" to "pulpcore==3.105.1"

PROJECT=pulp-development make build
```

Deploy using the custom Pulp container image:

```bash
./forge deploy-dev \
    --target-host=my-dev-box \
    --extra-vars pulp_container_image="quay.io/foreman/pulp-development" \
    --extra-vars pulp_container_tag="latest" \
    --add-feature=foreman-proxy
```
## Plugin Management

### Enabled Plugins (Default)

- `katello`
- `foreman_remote_execution`

### Plugin Registry

The system includes a plugin registry with predefined configurations:
- `katello` - Katello subscription management
- `foreman_remote_execution` - Remote execution plugin
- `foreman_ansible` - Ansible integration
- `foreman_rh_cloud` - Red Hat Cloud integration
- `foreman_discovery` - Host discovery
- `foreman_openscap` - OpenSCAP compliance
- `foreman_bootdisk` - Boot disk creation
- `foreman_openscap` - Foreman plug-in for displaying OpenSCAP audit reports
- `foreman_theme_satellite` - Branding for Satellite
- `foreman_tasks` - Tasks management engine and plugin for Foreman
- `foreman_webhooks` - Call external webhooks from Foreman
- `foreman_templates` - A plugin for Foreman to sync provisioning templates from an external source
- `foreman_leapp` - A plugin that allows to run inplace upgrades for RHEL hosts in Foreman using Leapp tool.
- `foreman_puppet` - A plugin that adds Puppet External node classification functionality to Foreman.

### Enabling Additional Plugins

#### At Deployment Time

Use the `--foreman-development-enabled-plugin` parameter (can be used multiple times):

```bash
# Enable specific plugins
./forge deploy-dev start --foreman-development-enabled-plugin katello --foreman-development-enabled-plugin foreman_ansible --foreman-development-enabled-plugin foreman_discovery

# Enable single plugin
./forge deploy-dev start --foreman-development-enabled-plugin katello

# Enable all available plugins
./forge deploy-dev start --foreman-development-enabled-plugin katello --foreman-development-enabled-plugin foreman_remote_execution --foreman-development-enabled-plugin foreman_ansible --foreman-development-enabled-plugin foreman_rh_cloud --foreman-development-enabled-plugin foreman_discovery --foreman-development-enabled-plugin foreman_openscap --foreman-development-enabled-plugin foreman_bootdisk
```

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

### Upgrading from source

This section is intended for users with foremanctl source cloned onto the same machine where foreman is being deployed on.

In a source install, git branches control versioning instead of RPM packages. Stable branches (e.g. `2.y-stable`) track a specific Foreman Y-stream, while the `master` branch tracks nightly changes (most recent).

Run all the steps as the root user in the foremanctl source directory unless otherwise specified.

1. Pull the latest changes using `git pull`.
2. Begin the upgrade by stopping all Foreman processes by running `systemctl stop foreman.target`.
3. Switch to the preferred target branch:
    - Switch to a stable Y-stream: `git fetch origin && git checkout origin/X.y-stable`
    - Switch to nightly: `git fetch origin && git checkout origin/master`
4. Run upgrade tasks by re-deploying foremanctl with your customized deploy command: `foremanctl deploy [...]`. Please see [Parameters](parameters.md) for available deploy options.

This final deploy command will pull new images and run all upgrade jobs required by Foreman, its dependencies, and your configured plugins. Expect this deploy to take longer than typical deploys.


## Architecture

### Service Integration

The development environment integrates:
- **Apache HTTP Server**: Provides HTTPS proxy to the Rails development server
- **Backend Services**: All services (PostgreSQL, Valkey, Candlepin, Pulp) run in containers
- **Rails Development Server**: Runs directly on the VM for live debugging and development
- **Pulp Smart Proxy Registration**: Automatically configures Pulp integration during deployment
- **Hammer CLI**: Automatically sets up hammer for development, if `hammer` feature was enabled
- **Smart Proxy**: Automatically set up a smart proxy for development and registers it into Foreman, if `foreman-proxy` feature was enabled

### Certificates

Development certificates are copied to `/home/vagrant/foreman-certs/`:

- `proxy_ca.pem` - CA certificate
- `client_cert.pem` - Client certificate
- `client_key.pem` - Client private key
