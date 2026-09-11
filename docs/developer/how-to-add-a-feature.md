# How to Add a Feature

This guide covers what you need to do to add a feature to foremanctl, using Remote Execution (REX) as a running example.

## What is a feature?

A feature in foremanctl extends the functionality the deployment by installing and configuring the additional components. The foremanctl tool automatically resolves dependencies, installs packages, and deploys configuration based on what you define in `src/features.yaml`.

## Prerequisites

Before adding a feature, you should:

- Know which components your plugin extends (does it add a Foreman plugin, a Smart Proxy plugin, a Hammer CLI plugin, or some combination?)
- Know what configuration the plugin needs (settings files, credentials, extra mounts, etc.)
- Be aware that Smart Proxy plugins only take effect when `foreman-proxy` is an enabled feature, and Hammer plugins only when `hammer` is enabled. Depending on the deployment's flavor, these may already be included, see [Deployment Design](deployment.md) for details.

## Step 1: Register the Feature

A feature can belong to three components:

1. **Foreman plugin** — installed into the Foreman container
2. **Smart Proxy plugin** — installed into the foreman-proxy container
3. **Hammer CLI plugin** — installed on the host machine (Hammer is not containerized)

All features must be registered in the central feature registry.

**Feature Registry:** `src/features.yaml`

Add your feature definition to above file:

Example: Remote Execution Feature

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

Plugin names must match what the ecosystem expects:

- `foreman.plugin_name` -- the plugin/gem name for foreman (e.g. `foreman_remote_execution`)
- `foreman_proxy.plugin_name` -- the smart proxy plugin/gem name without `smart_proxy_` prefix (e.g. `remote_execution_ssh`)
- `hammer` -- plugin/gem name without the `hammer_cli_` prefix (e.g. `hammer_cli_foreman_remote_execution` → `foreman_remote_execution`)

### Dependencies

Use `dependencies` to pull in dependencies automatically(which are required for a feature to work). Mark these non-user facing dependencies with `internal: true` to hide them from users:

```yaml
dynflow:
  internal: true
  foreman_proxy:
    plugin_name: dynflow
```

### Conflicts

Use `conflicts` to declare that two features are mutually exclusive and cannot both be enabled in the same deployment. Conflicts must be declared on both sides:

```yaml
cloud-connector:
  description: Cloud Connector for Red Hat Hybrid Cloud Console
  dependencies:
    - rh-cloud
  conflicts:
    - iop

iop:
  description: iop services
  dependencies:
    - rh-cloud
  conflicts:
    - cloud-connector
```

When a user tries to enable both conflicting features, the deploy will fail early with an error identifying the conflict.

## Step 2: Configure the Foreman Proxy Plugin (if needed)

If the feature has no `foreman_proxy` section, skip to Step 3.

Every Smart Proxy plugin needs a settings template. If the plugin also requires custom setup/configurations (generating credentials, mounting extra files), you add an additional tasks file. Both are keyed by `foreman_proxy.plugin_name`.

### Settings Template (required for Smart Proxy plugins)

Create a Jinja2 template at:

```
src/roles/foreman_proxy/templates/settings.d/<plugin_name>.yml.j2
```

The filename must exactly match `foreman_proxy.plugin_name`. The template must start with `:enabled: {{ feature_enabled }}` -- the system sets this to `"true"` or `"false"` automatically. Add any plugin-specific settings after that using Ruby symbol notation (`:key: value`).


Example: REX needs additional settings:

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

If the plugin needs addtional setup beyond the settings file, create a feature specific task file at:

```
src/roles/foreman_proxy/tasks/feature/<plugin_name>.yaml
```

The filename must exactly match `foreman_proxy.plugin_name` with `.yaml` extension. These tasks only run when the feature is enabled. If the file doesn't exist, nothing happens.

For example, REX needs SSH keys generated and mounted into the container, see [`remote_execution_ssh.yaml`](../src/roles/foreman_proxy/tasks/feature/remote_execution_ssh.yaml).

Configuration Tasks must notify `Restart Foreman Proxy` and `Refresh Foreman Proxy` handlers when making changes to configs or secrets.

### Ansible feature: volume and secret bindings

The Ansible feature is a useful example of a Smart Proxy plugin that needs both a
configuration secret and additional container mounts. It is registered in
[`src/features.yaml`](../../src/features.yaml) with the proxy plugin name
`ansible`. It also depends on Remote Execution, so enabling `ansible` implicitly 
enables `remote-execution` feature as well.

When the feature is enabled, the proxy role creates the following files and
mounts:

| Host-side object | Container path | Binding | Purpose |
| --- | --- | --- | --- |
| Podman secret `foreman-proxy-ansible-yml` | `/etc/foreman-proxy/settings.d/ansible.yml` | `Secret=...,type=mount` | Enables the Smart Proxy Ansible plugin and points it at its working directory and environment file. |
| Podman secret `foreman-proxy-ansible-env` | `/etc/foreman-proxy/ansible.env` | `Secret=...,type=mount` | Supplies the environment used when the proxy runs Ansible. |
| `/var/lib/foreman-proxy/ansible` | `/etc/ansible` | `Volume=...:ro,Z,U` | Makes roles, collections, and `ansible.cfg` available inside the proxy container. |

The host-side Ansible directory is initialized with these entries:

```text
/var/lib/foreman-proxy/ansible/
├── ansible.cfg       # created empty if it does not already exist
├── collections/
└── roles/
```

The generated volume binding is:

```ini
[Container]
Volume=/var/lib/foreman-proxy/ansible:/etc/ansible:ro,Z,U
```

The volume is read-only from the container (`ro`). `Z` gives the bind mount a
private SELinux label, and `U` adjusts ownership of the source content for the
container's user namespace. The container therefore reads the host directory
at `/etc/ansible`, while operators tasks use the persistent host path
under `/var/lib/foreman-proxy/ansible`.

The two secrets are mounted as files, not exposed as Podman environment
variables. The Ansible settings file contains:

```yaml
:enabled: true
:ansible_dir: /usr/share/foreman-proxy
:ansible_environment_file: /etc/foreman-proxy/ansible.env
```

The environment file configures the Ansible roles and collections search paths
under `/etc/ansible` and `/usr/share`, and sets the Foreman URL and certificate
paths. The Foreman Proxy base container mounts those certificate files as its
own secrets; the Ansible environment file refers to those existing mounts rather
than creating copies of the certificates.

The bindings are implemented as Quadlet drop-ins in
`/etc/containers/systemd/foreman-proxy.container.d/`:

- `ansible.conf` mounts the plugin settings secret.
- `ansible-env.conf` mounts the Ansible environment secret.
- `ansible-volumes.conf` adds the `/var/lib/foreman-proxy/ansible` volume.

After these drop-ins are written, foremanctl reloads systemd and restarts the
Foreman Proxy. Changes also trigger a Smart Proxy refresh in Foreman. The
additional Ansible tasks run only while the feature is enabled; the generic
feature configuration task still writes a disabled settings secret when the
feature is disabled.

## Step 3: Deploy

```bash
./foremanctl deploy --add-feature={feature-name}
```

### Feature Validation

```bash
./foremanctl features
```

Here you should be able to see your feature as enabled

**Foreman-only** (no settings template or additional tasks needed):

```yaml
google:
  description: Google Compute Engine plugin for Foreman
  foreman:
    plugin_name: foreman_google
  hammer: foreman_google
```

**Smart Proxy-only** (setting template needed, no additional tasks):

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
    └── tasks/feature/<plugin_name>.yaml                 # Additional tasks (optional)
```
