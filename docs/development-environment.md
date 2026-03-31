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

## Custom Container Images

### Building Custom Pulp Containers

For development scenarios requiring specific Pulp plugin versions or compatibility fixes, you can build custom Pulp container images using the provided `development/custom-pulp-containerfile`.

This approach was particularly useful during the Django 4 to 5 upgrade, where version constraints between pulpcore and plugins needed careful management.

#### Building the Container

```bash
# Build custom Pulp container with specific plugin versions
podman build -f development/custom-pulp-containerfile -t quay.io/yourusername/pulp:custom .

# Push to registry for deployment
podman push quay.io/yourusername/pulp:custom
```

#### Customizing Pulp Plugin Versions

Edit `development/custom-pulp-containerfile` to specify the plugin versions you need:

```dockerfile
# Install specific plugin versions
# Edit these versions as needed for your environment
RUN pip install --upgrade pip && \
    pip install \
        pulpcore==3.105.1 \
        pulp-ansible==0.29.6 \
        pulp-container==2.27.3 \
        pulp-rpm==3.35.2 \
        pulp-ostree==2.6.0 \
        pulp-python==3.27.0 \
        pulp-deb==3.8.1 \
        pulp-smart-proxy
```

The containerfile also contains commented lines for increaseing the maximum Pulpcore version.
This is helpful for when pulp_smart_proxy isn't yet tested with a newer version of Pulpcore.

#### Deploying with Custom Pulp Images

Use the custom Pulp container image during deployment:

```bash
./forge deploy-dev \
    --target-host=my-dev-box \
    --extra-vars pulp_container_image="quay.io/yourusername/pulp" \
    --extra-vars pulp_container_tag="custom" \
    --add-feature=foreman-proxy
```

### Customizing PostgreSQL Version

You can override the default PostgreSQL version, which is useful when testing database compatibility changes:

```bash
# Deploy with PostgreSQL 16 (explicit)
./forge deploy-dev \
    --target-host=my-dev-box \
    --extra-vars postgresql_container_image="quay.io/sclorg/postgresql-16-c9s" \
    --extra-vars postgresql_container_tag="latest"
```

#### Complete Custom Deployment Example

Combining custom Pulp and PostgreSQL images:

```bash
# Deploy with custom Pulp image and specific PostgreSQL version
./forge deploy-dev \
    --target-host=katello-dev-newer-pulp \
    --extra-vars pulp_container_tag="custom" \
    --extra-vars pulp_container_image="quay.io/yourusername/pulp" \
    --extra-vars postgresql_container_image="quay.io/sclorg/postgresql-16-c9s" \
    --extra-vars postgresql_container_tag="latest" \
    --add-feature=foreman-proxy
```

This approach allows testing compatibility between different versions of backend services during major framework upgrades or when integrating newer plugin versions.

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
