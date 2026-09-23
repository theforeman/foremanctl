---
name: dev-setup
description: >-
  Interactive foremanctl development environment setup. Set up a Foreman/Katello development environment with abilty to enable plugins.
---

# Foremanctl Dev Setup

Set up a Foreman/Katello development environment via `forge deploy-dev`. See the [development environment overview](../../../docs/developer/development-environment.md#overview) for the architecture and service layout.

**Always use this skill** for foremanctl dev environment tasks — including partial workflows. Do not reimplement steps manually via ad-hoc commands when this skill covers the task.

## Workflow routing

Steps are composable. Ask what the user already has, then run only the matching steps:

| User goal | What they need | Steps to run |
|-----------|----------------|--------------|
| Full environment from scratch | Nothing yet | Steps 1 → 2 → 3 → 4 → (optional 5) |
| VMs already running, deploy Foreman | Vagrant VMs up, inventory exists | Step 3 → 4 → (optional 5) |
| Re-deploy with different plugins | Vagrant VMs up | Step 3 (re-run with new plugin selection) → 4 |
| Add features to existing deployment | Deployed environment | Step 5 |
| Verify deployment health | Deployed environment | Step 4 |
| Provision VMs only | Vagrant + libvirt installed | Steps 1 → 2 |

When the user asks for a single step (e.g. "verify my deployment"), use the matching row above — do not skip the skill.

## Prerequisites

Before starting, follow the [development prerequisites](../../../DEVELOPMENT.md#requirements).

For Vagrant and libvirt installation, see the [Vagrant and libvirt instructions](https://github.com/theforeman/forklift/blob/master/docs/vagrant.md).

## Step 1 — Set up environment

Follow the [development environment prerequisites and setup instructions](../../../DEVELOPMENT.md#development-environment-setup). Run `./setup-environment` from the project root and activate `.venv`; the setup script is idempotent and safe to re-run.

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

**Plugins** — follow the [plugin management documentation](../../../docs/developer/development-environment.md#plugin-management) for the available plugins and their behavior. Ask the user which plugins to enable, allowing multiple selections. The default plugins are `katello` and `foreman_remote_execution`.

**Features** — enable additional infrastructure services. Follow the [feature management documentation](../../../docs/developer/development-environment.md#feature-management) for the available features and their behavior. Ask if the user wants `hammer` or `foreman-proxy`.

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
ssh -o BatchMode=yes -o ConnectTimeout=5 <user>@<host> "echo OK"
```

- If this succeeds, key-based auth works — no password needed.
- If this fails, preserve and show the SSH diagnostic; do not assume that password authentication is required. Suggest `ANSIBLE_ASK_PASS=true` only when the diagnostic clearly indicates that password authentication is applicable. Tell the user to run the full command themselves using the `!` prefix so the interactive password prompt works within this session. Otherwise, ask the user to correct the SSH connection issue before deployment. Do NOT attempt to run `ANSIBLE_ASK_PASS=true` commands directly — the password prompt requires an interactive terminal.

Example:
```
! ANSIBLE_ASK_PASS=true ./forge deploy-dev [args...]
```

## Step 4 — Verify deployment

If deployment completed successfully, confirm that the Foreman API responds on the deployed host. Report the result.

Only perform container, systemd, or log checks if deployment failed or the API does not respond. See the [deployment verification instructions](../../../docs/developer/development-environment.md#verifying-the-deployment) for troubleshooting.

## Step 5 — Add features to existing deployment (optional)

Re-run deploy-dev with `--add-feature` to add `hammer` or `foreman-proxy` after initial deployment:

```bash
./forge deploy-dev --add-feature hammer --add-feature foreman-proxy
```

## Tear down

Stop and destroy the Vagrant VMs. Only run when the user explicitly asks to tear down:

```bash
./forge vms stop
```

## Error handling

If any step fails, ask the user whether to continue to the next step or stop. Do not silently skip failures.

## Notes

- Always activate the virtualenv (`source .venv/bin/activate`) before running `./forge` or `./foremanctl` commands.
- The development user defaults to `vagrant`. For other hosts, set with `--foreman-development-user`.
