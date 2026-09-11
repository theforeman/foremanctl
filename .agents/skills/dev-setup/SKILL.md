---
name: dev-setup
description: >-
  Interactive foremanctl development environment setup. Set up a Foreman/Katello development environment with abilty to enable plugins.
---

# Foremanctl Dev Setup

Set up a Foreman/Katello development environment via `forge deploy-dev`. Foreman is installed from git and runs directly on the VM as a Rails server. Backend services (PostgreSQL, Valkey, Candlepin, Pulp, HTTPD) run in containers.

**Always use this skill** for foremanctl dev environment tasks — including partial workflows. Do not reimplement steps manually via ad-hoc commands when this skill covers the task.

## Workflow routing

Steps are composable. Ask what the user already has, then run only the matching steps:

| User goal | What they need | Steps to run |
|-----------|----------------|--------------|
| Full environment from scratch | Nothing yet | Steps 1 → 2 → 3 → 4 → (optional 5) |
| VMs already running, deploy Foreman | Vagrant VMs up, inventory exists | Step 3 → 4 → (optional 5) |
| Re-deploy with different plugins | Vagrant VMs up | Step 3 (re-run with new plugin selection) → 4 |
| Add hammer to existing deployment | Deployed environment | Step 5 |
| Verify deployment health | Deployed environment | Step 4 |
| Provision VMs only | Vagrant + libvirt installed | Steps 1 → 2 |

When the user asks for a single step (e.g. "just run tests"), use the matching row above — do not skip the skill.

## Prerequisites

Before starting, verify the following are installed on the local machine:

- **Python 3** — virtualenv and dependencies
- **Ansible 2.14+** — automation runtime
- **Vagrant 2.2+** — VM lifecycle management
- **vagrant-libvirt** — Vagrant plugin for libvirt/KVM backend
- **libvirt** — hypervisor for local VMs
- **Virtualization** — enabled in BIOS/UEFI

Follow [instructions](https://github.com/theforeman/forklift/blob/master/docs/vagrant.md) to install Vagrant and libvirt.

Check with:
```bash
command -v python3 && command -v vagrant && vagrant plugin list | grep -q vagrant-libvirt && echo "All prerequisites met"
```

## Step 1 — Set up environment

Set up the Python virtualenv and build Ansible collections.

Run from the project root:

```bash
./setup-environment
source .venv/bin/activate
```

Validate that `build/collections/foremanctl` and `build/collections/forge` directories exist. Report Python and Ansible versions.

`./setup-environment` is idempotent — safe to re-run if `.venv` already exists.

## Step 2 — Provision VMs

Provision Vagrant VMs (quadlet + client) via libvirt.

Check that `vagrant` is in PATH and `vagrant-libvirt` plugin is installed (`vagrant plugin list | grep vagrant-libvirt`). Show `vagrant status`.

```bash
source .venv/bin/activate
./forge vms start
```

Validate that `inventories/local_vagrant` was generated — show its contents.

**Troubleshooting:**
- **vagrant-libvirt not found** — install with `vagrant plugin install vagrant-libvirt`
- **libvirt permission denied** — ensure the user is in the `libvirt` group
- **No inventory generated** — check `./forge vms start` output for provisioning errors

## Step 3 — Deploy dev environment

Deploy Foreman and all supporting services to the target VM.

**Plugins** — each selected plugin is git-cloned into its own directory under the deployment dir (`/home/<dev-user>/`, e.g. `/home/vagrant/katello/`, `/home/vagrant/foreman_remote_execution/`). Plugins are local path gems — source edits are picked up immediately by the Rails server. Ask the user to select using `AskUserQuestion` with `multiSelect: true`:

- `foreman_remote_execution` — Remote Execution
- `foreman_ansible` — Ansible integration
- `foreman_rh_cloud` — Red Hat Cloud
- `foreman_discovery` — Bare-metal host discovery
- `foreman_openscap` — OpenSCAP security audits
- `foreman_bootdisk` — Boot disk provisioning
- `foreman_theme_satellite` — Satellite theme
- `foreman_tasks` — Task management
- `foreman_webhooks` — Webhook notifications
- `foreman_templates` — Template sync
- `foreman_leapp` — RHEL in-place upgrades (Leapp)
- `foreman_puppet` — Puppet integration

Default plugins (always included): `katello`, `foreman_remote_execution`. Make this clear in the question.

**Features** — enable additional infrastructure services. Ask if the user wants any:

- `hammer` — Foreman CLI (git checkout of hammer-cli + plugins)
- `foreman-proxy` — Smart Proxy (git checkout, registered into Foreman)

Then ask (skip if user provides no input):
- **GitHub username** — for additional git remotes on checkouts
- **Target host** — defaults to `quadlet` VM; set to hostname/IP for any other host
- **Development user** — defaults to `vagrant`; set when the target host uses a different user
- **Manage repos** — defaults to `true`; set to `false` to skip git cloning (useful when repos are already checked out)

Build the `./forge deploy-dev` command:
- Each plugin: `--foreman-development-enabled-plugin <name>`
- Each feature: `--add-feature <name>`
- GitHub user: `--foreman-development-github-username <user>`
- Target host: `--target-host <host>`
- Dev user: `--foreman-development-user <user>`
- Manage repos: `--manage-repos false`

**SSH authentication** — when `--target-host` is set (non-Vagrant), test SSH key auth before deploying:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=5 <user>@<host> "echo OK" 2>/dev/null
```

- If this succeeds, key-based auth works — no password needed.
- If this fails, the host requires password authentication. Show the full command prefixed with `ANSIBLE_ASK_PASS=true` and tell the user to run it themselves using the `!` prefix so the interactive password prompt works within this session. Do NOT attempt to run `ANSIBLE_ASK_PASS=true` commands directly — the password prompt requires an interactive terminal.

Example:
```
! source .venv/bin/activate && ANSIBLE_ASK_PASS=true ./forge deploy-dev [args...]
```

## Step 4 — Verify deployment

Verify SSH access, container health, systemd services, and Foreman API on the deployed host.

Determine the host and SSH details: if Vagrant was used, extract from `inventories/local_vagrant`; if `--target-host` was used, use that value directly.

```bash
python3 -c "
import yaml
with open('inventories/local_vagrant') as f:
    inv = yaml.safe_load(f)
host = inv['all']['hosts']['quadlet']
print(host.get('ansible_host', ''))
print(host.get('ansible_ssh_private_key_file', ''))
"
```

Run these checks and report results:

1. **SSH**: `ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 <user>@<host> "echo OK"`
2. **Containers**: `ssh ... "sudo podman ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"`
3. **Systemd**: `ssh ... "systemctl list-units --type=service --state=running --no-pager | grep -E '(foreman|pulp|candlepin|httpd|postgres|valkey)'"`
4. **Foreman API**: `curl -sk http://<host>:3000/api/v2/ping`

If Foreman is not reachable (deploy-dev stops the service after initial setup), start it:
```
ssh <user>@<host> "sudo systemctl start foreman-development"
```

**Troubleshooting:**
- **SSH connection refused** — VM may still be booting; wait and retry.
- **Containers not running** — check `sudo podman ps -a` for exited containers and `journalctl -u quadlet-*` for errors.
- **Foreman not ready** — webpack compilation can take 60-120s. Check `tail -50 /tmp/foreman.log` on the VM.
- **API returns 401** — credentials may differ from the default `admin:changeme`. Verify with `curl -sk -u admin:changeme http://<host>:3000/api/v2/status`.

## Step 5 — Add features to existing deployment (optional)

Re-run deploy-dev with `--add-feature` to add `hammer` or `foreman-proxy` after initial deployment:

```bash
source .venv/bin/activate
./forge deploy-dev --add-feature hammer --add-feature foreman-proxy
```

## Tear down

Stop and destroy the Vagrant VMs. Only run when the user explicitly asks to tear down:

```bash
source .venv/bin/activate
./forge vms stop
```

## Error handling

If any step fails, ask the user whether to continue to the next step or stop. Do not silently skip failures.

## Notes

- Always activate the virtualenv (`source .venv/bin/activate`) before running `./forge` or `./foremanctl` commands.
- The development user defaults to `vagrant`. For other hosts, set with `--foreman-development-user`.
