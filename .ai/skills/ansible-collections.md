---
name: ansible-collections
description: >-
  Ansible Galaxy collections used by foremanctl, how they are installed
  and managed, and the build/collections layout.
technologies:
  - ansible
references:
  - src/requirements.yml
  - development/requirements.yml
  - Makefile
---

# Skill - Ansible Collections in foremanctl

foremanctl uses Ansible Galaxy collections for Podman management, cryptography, PostgreSQL, and Foreman API operations. Collections are installed locally per tool to avoid conflicts with system-wide installations.

## Production Collections (`src/requirements.yml`)

```yaml
collections:
  - community.postgresql
  - community.crypto
  - community.general
  - ansible.posix
  - name: containers.podman
    version: ">=1.16.4"
  - name: theforeman.foreman
    version: ">=5.9.0"
```

### Collection Purposes

| Collection | Purpose |
|------------|---------|
| `community.postgresql` | PostgreSQL user, database, and extension management |
| `community.crypto` | Certificate generation, private keys, CSRs |
| `community.general` | General-purpose modules (ini_file, json_query, etc.) |
| `ansible.posix` | POSIX-specific modules (sysctl, mount, selinux) |
| `containers.podman` | Podman container, secret, volume, network, image management |
| `theforeman.foreman` | Foreman API operations (resources, settings, content) |

## Development Collections (`development/requirements.yml`)

The development collection set includes the production collections plus:

- `theforeman.operations` -- operational tooling
- Git-based collections from `forklift` for Vagrant/VM management

## Collection Installation

### Via setup-environment

```bash
./setup-environment
```

This runs `pip install` for Python deps and then `make build/collections/foremanctl build/collections/forge` to install Galaxy collections.

### Via Makefile

```bash
# Install production collections
make build/collections/foremanctl

# Install development collections
make build/collections/forge
```

### Lock File

The Makefile prefers `src/requirements-lock.yml` over `src/requirements.yml` if it exists. The lock file pins exact versions for reproducible builds. If no lock file is present, the floating versions in `requirements.yml` are used.

```makefile
REQUIREMENTS_YML := $(firstword $(wildcard src/requirements-lock.yml src/requirements.yml))
```

## Collection Paths

Collections are installed into separate directories per tool and isolated from system paths:

| Tool | Collection Path | Set By |
|------|----------------|--------|
| `foremanctl` | `build/collections/foremanctl` | `ANSIBLE_COLLECTIONS_PATH` in `foremanctl` script |
| `forge` | `build/collections/forge` | `ANSIBLE_COLLECTIONS_PATH` in `forge` script |

Both scripts set `ANSIBLE_COLLECTIONS_SCAN_SYS_PATH=false` to prevent using system-installed collections.

## Using Collections in Roles

Always use fully qualified collection names (FQCN) in tasks:

```yaml
# Correct
- name: Create Podman secret
  containers.podman.podman_secret:
    name: foreman-settings-yaml
    data: "{{ settings_content }}"

# Incorrect
- name: Create Podman secret
  podman_secret:
    name: foreman-settings-yaml
    data: "{{ settings_content }}"
```

## Build Artifacts

The `make dist` target creates a distribution tarball that includes:

1. Git archive of the repository
2. Vendored collections from `build/collections/foremanctl`
3. Collection test directories are excluded from the tarball

```makefile
$(NAME)-$(VERSION).tar.gz: build/collections/foremanctl
    git archive --prefix $(NAME)-$(VERSION)/ --output $(NAME)-$(VERSION).tar HEAD
    tar --append --file $(NAME)-$(VERSION).tar \
        --transform='s#^#$(NAME)-$(VERSION)/#' \
        --exclude='build/collections/foremanctl/ansible_collections/*/*/tests/*' \
        build/collections/foremanctl
    gzip $(NAME)-$(VERSION).tar
```

This ensures the distributed package is self-contained and does not require Galaxy access at install time.
