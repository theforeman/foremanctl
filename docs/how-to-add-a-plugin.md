# How to Add a Plugin/Feature

This guide covers what you need to do to add a plugin/feature to foremanctl, using Remote Execution (REX) as a running example.

## Overview

A feature in foremanctl extends the functionality of Foreman, Smart Proxy, and Hammer CLI by installing and configuring the relevant plugin packages in each. The foremanctl tool automatically resolves dependencies, installs packages, and deploys configuration based on what you define in `src/features.yaml`.

## Prerequisites

Before adding a plugin, you should:

- Know which services your plugin extends -- does it add a Foreman plugin, a Smart Proxy plugin, a Hammer CLI plugin, or some combination?
- Know what configuration the plugin needs (settings files, credentials, extra mounts, etc.)
- Be aware that Smart Proxy plugins only take effect when `foreman-proxy` is an enabled feature, and Hammer plugins only when `hammer` is enabled. Depending on the deployment's flavor, these may already be included -- see [Deployment Design](deployment.md) for details.

### Feature Components

A feature can belong to three components:

1. **Foreman plugin** - Installed into the Foreman container
2. **Smart Proxy plugin** - Installed into foreman-proxy container
3. **Hammer CLI plugin** - Installed on host machine(as we currently don't ship hammer in container)

## Step 1: Register the Plugin

All plugins must be registered in the central feature registry.

**File:** `src/features.yaml`

Add your plugin definition to this file:

Example:- Remote Execution Feature

```yaml
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

See [Feature Metadata Reference](feature-metadata.md) for the full list of properties.

### Naming

Names must match what upstream expects:

- `foreman.plugin_name` -- the plugin/gem name for foreman (e.g. `foreman_remote_execution`)
- `foreman_proxy.plugin_name` -- the plugin/gem name for smart-proxy without `smart_proxy_` prefix (e.g. `smart_proxy_remote_execution_ssh`)
- `hammer` -- the suffix for the RPM package (e.g. `foreman_remote_execution` → `hammer-cli-plugin-foreman_remote_execution`)

### Dependencies

Use `dependencies` to pull in other features automatically. Mark dependency-only features with `internal: true` to hide them from users:

```yaml
dynflow:
  internal: true
  foreman_proxy:
    plugin_name: dynflow
```

## Step 2: Configure the Foreman Proxy Plugin (if needed)

If the feature has no `foreman_proxy` section, skip to Step 3.

Every Smart Proxy plugin needs a **settings template**. If the plugin also requires host-side setup (generating credentials, mounting extra files), you add an **additional tasks file**. Both are keyed by `foreman_proxy.plugin_name`.

### Settings Template (required for Smart Proxy plugins)

Create a Jinja2 template at:

```
src/roles/foreman_proxy/templates/settings.d/<plugin_name>.yml.j2
```

The filename must exactly match `foreman_proxy.plugin_name`. The template must start with `:enabled: {{ feature_enabled }}` -- the system sets this to `"true"` or `"false"` automatically. Add any plugin-specific settings after that using Ruby symbol notation (`:key: value`).


Example:- REX needs additional settings:

```yaml
---
:enabled: {{ feature_enabled }}
:ssh_identity_key_file: '~/.ssh/id_rsa_foreman_proxy'
:local_working_dir: '/var/tmp'
:remote_working_dir: '/var/tmp'
:socket_working_dir: '/var/tmp'
:mode: ssh
```

### Additional Tasks (optional)

If the plugin needs host-side setup beyond the settings file, create a task file at:

```
src/roles/foreman_proxy/tasks/feature/<plugin_name>.yaml
```

The filename must exactly match `foreman_proxy.plugin_name` with `.yaml` extension. These tasks only run when the feature is enabled. If the file doesn't exist, nothing happens.

For example, REX needs SSH keys generated and mounted into the container -- see [`remote_execution_ssh.yaml`](../src/roles/foreman_proxy/tasks/feature/remote_execution_ssh.yaml).

Configuration Tasks must notify `Restart Foreman Proxy` and `Refresh Foreman Proxy` handlers when making changes to configs or secrets.

## Step 3: Deploy

```bash
./foremanctl deploy --add-feature={feature-name}
```

### Feature Validation

```bash
./foremanctl features
```

Here you should be able to see your feature as enabled

**Foreman-only** (no template or tasks needed):

```yaml
google:
  description: Google Compute Engine plugin for Foreman
  foreman:
    plugin_name: foreman_google
  hammer: foreman_google
```

**Smart Proxy-only** (template needed, no tasks):

```yaml
logs:
  description: Logs feature for Smart Proxy
  foreman_proxy:
    plugin_name: logs
```

With a minimal template at `src/roles/foreman_proxy/templates/settings.d/logs.yml.j2`:

```yaml
---
:enabled: {{ feature_enabled }}
```

## File Layout

```
src/
├── features.yaml                                        # Feature registry
└── roles/foreman_proxy/
    ├── templates/settings.d/<plugin_name>.yml.j2        # Smart Proxy settings
    └── tasks/feature/<plugin_name>.yaml                 # Setup tasks (optional)
```
