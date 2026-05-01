---
name: podman-quadlets
description: >-
  How Podman quadlets work in foremanctl: container, volume, and network
  definitions as systemd-native units, image management, and the relationship
  between quadlet files and Ansible roles.
technologies:
  - podman
  - systemd
  - ansible
references:
  - docs/developer/container-image-builds.md
  - docs/developer/deployment.md
  - src/vars/images.yml
---

# Skill - Podman Quadlets in foremanctl

foremanctl deploys Foreman and Katello as containerized services managed by systemd through Podman quadlets.

## What Are Quadlets?

Podman quadlets provide a declarative way to define containers, volumes, and networks as systemd unit-like files. The Podman systemd generator automatically converts these files into actual systemd services at boot time (or on `systemctl daemon-reload`).

### Quadlet File Types

| Extension | Purpose |
|-----------|---------|
| `.container` | Container definitions (image, env, volumes, ports, secrets) |
| `.volume` | Named volume definitions |
| `.network` | Network definitions |

### Quadlet Location

Quadlet files are placed in systemd unit directories (typically `/etc/containers/systemd/`) and processed by the Podman systemd generator.

## Container Images

All image references are centralized in `src/vars/images.yml`:

```yaml
container_tag_stream: "3.18"

# Foreman ecosystem images (quay.io/foreman/*)
foreman_container_image: quay.io/foreman/foreman
foreman_container_tag: "{{ container_tag_stream }}"

candlepin_container_image: quay.io/foreman/candlepin
candlepin_container_tag: "foreman-{{ container_tag_stream }}"

foreman_proxy_container_image: quay.io/foreman/foreman-proxy
foreman_proxy_container_tag: "{{ container_tag_stream }}"

pulp_container_image: quay.io/foreman/pulp
pulp_container_tag: "foreman-{{ container_tag_stream }}"

# Infrastructure images (quay.io/sclorg/*)
postgresql_container_image: quay.io/sclorg/postgresql-13-c9s
postgresql_container_tag: "latest"

redis_container_image: quay.io/sclorg/redis-6-c9s
redis_container_tag: "latest"
```

### Image Groups

Images are grouped for selective pulling:

- `images` -- core Foreman stack (foreman, candlepin, pulp, redis)
- `database_images` -- PostgreSQL (separate for external database scenarios)
- `foreman_proxy_images` -- Smart Proxy (separate because it's a feature)

### Image Naming Convention

Foreman ecosystem images follow: `quay.io/foreman/<service>:<tag>`

Tags follow two patterns:
- Direct version: `3.18` (foreman, foreman-proxy)
- Prefixed version: `foreman-3.18` (candlepin, pulp)

Infrastructure images use upstream SCL containers from `quay.io/sclorg/`.

## Services and Roles

Each containerized service has a corresponding Ansible role that manages its quadlet files, configuration, and lifecycle:

| Service | Role | Image | Ports |
|---------|------|-------|-------|
| Foreman | `foreman` | `quay.io/foreman/foreman` | 3000 (Puma) |
| Candlepin | `candlepin` | `quay.io/foreman/candlepin` | 8443 |
| Pulp | `pulp` | `quay.io/foreman/pulp` | 24816 (API), workers |
| PostgreSQL | `postgresql` | `quay.io/sclorg/postgresql-13-c9s` | 5432 |
| Redis | `redis` | `quay.io/sclorg/redis-6-c9s` | 6379 |
| Apache HTTPD | `httpd` | (host-installed) | 80, 443 |
| Smart Proxy | `foreman_proxy` | `quay.io/foreman/foreman-proxy` | 8000, 9090 |

## systemd Integration

foremanctl uses a `systemd_target` role to manage service ordering. Services are grouped under a systemd target that controls startup and shutdown order, ensuring dependencies (like PostgreSQL) start before dependent services (like Foreman).

## Configuration via Secrets

Container configuration is mounted from Podman secrets, not host files. See the `podman-secrets` rule for naming conventions.

### Registry Authentication

All services share a registry auth file at `/etc/foreman/registry-auth.json`, referenced per-service as `<service>_registry_auth_file` variables in `images.yml`.

## Pulling Images

The `pull-images` playbook (`foremanctl pull-images`) pre-pulls container images before deployment:

```bash
./foremanctl pull-images
```

This is useful for air-gapped or slow-network environments where you want to cache images before deploying.

## Key Ansible Collection

Container operations use the `containers.podman` Ansible collection (version >= 1.16.4), which provides:

- `containers.podman.podman_container` -- manage containers
- `containers.podman.podman_secret` -- manage secrets
- `containers.podman.podman_volume` -- manage volumes
- `containers.podman.podman_network` -- manage networks
- `containers.podman.podman_image` -- manage images
