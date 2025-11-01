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

- A running virtual machine, and inventory that contains knowledge of the VM. For example, using `./forge vms start`.
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
   - Direct Rails server: `http://localhost:3000` (when running locally)

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

### Enabling Additional Plugins

#### At Deployment Time

Use the `--foreman-development-enabled-plugins` parameter with a comma-separated list:

```bash
# Enable specific plugins
./forge deploy-dev start --foreman-development-enabled-plugins="katello,foreman_ansible,foreman_discovery"

# Enable single plugin
./forge deploy-dev start --foreman-development-enabled-plugins="katello"

# Enable all available plugins
./forge deploy-dev start --foreman-development-enabled-plugins="katello,foreman_remote_execution,foreman_ansible,foreman_rh_cloud,foreman_discovery,foreman_openscap,foreman_bootdisk"
```

## Development Workflow

### Initial Setup

After deployment, the environment includes:
- Cloned Foreman repository
- Installed Ruby and Node.js dependencies
- Database migrations and seeding
- Plugin repositories and configurations
- Development-specific settings

## Architecture

### Service Integration

The development environment integrates:
- **Apache HTTP Server**: Provides HTTPS proxy to the Rails development server
- **Backend Services**: All services (PostgreSQL, Redis, Candlepin, Pulp) run in containers
- **Rails Development Server**: Runs directly on the VM for live debugging and development
- **Pulp Smart Proxy Registration**: Automatically configures Pulp integration during deployment

### Certificates

Development certificates are copied to `/home/vagrant/foreman-certs/`:
- `proxy_ca.pem` - CA certificate
- `client_cert.pem` - Client certificate
- `client_key.pem` - Client private key

## Customization

### Changing Git Repository/Branch

```yaml
foreman_development_git_repo: "https://github.com/myorg/foreman.git"
foreman_development_git_revision: "my-feature-branch"
```

### Enabling Different Plugins

```yaml
foreman_development_enabled_plugins:
  - katello
  - foreman_ansible
  - foreman_discovery
```

### Database Configuration

```yaml
foreman_development_database_name: "my_foreman_dev"
foreman_development_database_password: "custom_password"
```

### Rails Server Settings

```yaml
foreman_development_rails_port: 4000
foreman_development_rails_command: "rails server -p 4000"
```

### Development URL Configuration

```yaml
foreman_development_url: "http://{{ ansible_fqdn }}:{{ foreman_development_rails_port }}"
```

This variable centralizes URL configuration for the development environment and is used throughout the deployment for consistency.
