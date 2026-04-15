---
name: foreman-ecosystem
description: >-
  Overview of the Foreman ecosystem components deployed by foremanctl:
  Foreman, Katello, Pulp, Candlepin, Smart Proxy, and Hammer. Covers
  features, flavors, and the plugin system.
technologies:
  - foreman
  - katello
  - pulp
  - candlepin
references:
  - docs/developer/how-to-add-a-feature.md
  - docs/developer/feature-metadata.md
  - docs/developer/deployment.md
---

# Skill - Foreman Ecosystem

foremanctl deploys and manages the Foreman ecosystem -- a suite of open-source tools for lifecycle management of physical and virtual servers.

## Core Components

### Foreman

The central application server for provisioning, configuration management, and monitoring. Runs as a Ruby on Rails application (Puma) in a container.

- Image: `quay.io/foreman/foreman:3.18`
- Current version: Foreman 3.18

### Katello

Content and subscription management plugin for Foreman. Manages RPM repositories, Deb repositories, container registries, and subscription/entitlement tracking.

- Integrated into the Foreman container as a plugin
- Current version: Katello 4.20

### Pulp

Content management platform that handles repository synchronization, content storage, and publication. Runs as separate worker and API containers.

- Image: `quay.io/foreman/pulp:foreman-3.18`
- Current version: Pulp 3.85

### Candlepin

Subscription management service for entitlement tracking and certificate generation. Runs as a Java application in its own container.

- Image: `quay.io/foreman/candlepin:foreman-3.18`
- Current version: Candlepin 4.6

### Smart Proxy (Foreman Proxy)

Distributed agent that handles operations on managed infrastructure: DHCP, DNS, TFTP, Puppet, Remote Execution, etc. Runs as its own container.

- Image: `quay.io/foreman/foreman-proxy:3.18`
- Enabled as a feature (`foreman-proxy`)

### Hammer

Command-line interface for interacting with the Foreman API. Unlike other components, Hammer runs directly on the host (not containerized).

- Enabled as a feature (`hammer`)

## Supporting Services

### PostgreSQL

Database backend for Foreman, Katello, Candlepin, and Pulp.

- Image: `quay.io/sclorg/postgresql-13-c9s`
- Can be internal (containerized) or external

### Redis

In-memory cache and queue backend used by Foreman and Pulp.

- Image: `quay.io/sclorg/redis-6-c9s`

### Apache HTTPD

Reverse proxy that terminates TLS and routes requests to Foreman, Pulp, and Candlepin containers.

- Installed on the host (not containerized)

## Features and Flavors

### Flavors

A flavor defines the base set of features for a deployment. Currently only one flavor exists:

- `katello` -- includes Foreman + Katello + Pulp + Candlepin (defined in `src/vars/flavors/katello.yml`)

### Features

Features are modular capabilities that extend the base deployment:

```yaml
# src/features.yaml
remote-execution:
  description: Remote Execution plugin for Foreman
  foreman:
    plugin_name: foreman_remote_execution
  foreman_proxy:
    plugin_name: remote_execution_ssh
  hammer: foreman_remote_execution
  dependencies:
    - dynflow
```

A feature can extend up to three components:
1. **Foreman** -- plugin installed in the Foreman container
2. **Smart Proxy** -- plugin installed in the foreman-proxy container
3. **Hammer** -- CLI plugin installed on the host

### Feature Resolution

```
enabled_features = flavor_features + user_features
```

Features are enabled via CLI:

```bash
./foremanctl deploy --add-feature remote-execution
./foremanctl deploy --remove-feature remote-execution
./foremanctl features  # List enabled features
```

### Internal Features

Features marked `internal: true` are dependencies that are not exposed to users:

```yaml
dynflow:
  internal: true
  foreman_proxy:
    plugin_name: dynflow
```

## Platform Support

- **Target OS**: CentOS Stream 9, RHEL 9
- **Ansible**: ansible-core 2.16+
- **Python**: 3.9+ (CentOS Stream 9 default)
- **Podman**: As shipped with CentOS Stream 9 / RHEL 9

## Tuning Profiles

Resource allocation is controlled by tuning profiles in `src/vars/tuning/`:

| Profile | Use Case |
|---------|----------|
| `default` | Standard production |
| `development` | Minimal resources for local dev |
| `medium` | Medium-scale production |
| `large` | Large-scale production |
| `extra-large` | Enterprise scale |
| `extra-extra-large` | Maximum scale |

Tuning profiles control Puma workers, Pulp worker count, memory limits, and other resource parameters.
