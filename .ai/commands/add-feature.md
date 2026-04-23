---
name: add-feature
description: >-
  Step-by-step workflow for adding a new feature to foremanctl's deployment
  system. Covers feature registration, proxy configuration, and validation.
argument-hint: "<feature-name> [--foreman <plugin_name>] [--proxy <plugin_name>] [--hammer <gem_name>]"
references:
  - docs/developer/how-to-add-a-feature.md
  - docs/developer/feature-metadata.md
  - src/features.yaml
---

# Commands - Add Feature

Add a new feature to foremanctl's deployment system.

## Input

`$ARGUMENTS` -- the feature name and optional component flags:
- `<feature-name>` (required) -- hyphenated name for the feature (e.g. `remote-execution`)
- `--foreman <plugin_name>` -- Foreman plugin gem name (e.g. `foreman_remote_execution`)
- `--proxy <plugin_name>` -- Smart Proxy plugin name without `smart_proxy_` prefix
- `--hammer <gem_name>` -- Hammer CLI gem name without `hammer_cli_` prefix

If flags are omitted, prompt the user for which components the feature extends.

## Workflow

### 1. Gather Information

Before making changes, confirm with the user:
- Which components does the feature extend? (Foreman, Smart Proxy, Hammer, or a combination)
- Does it have dependencies on other features?
- Does the Smart Proxy plugin need additional configuration beyond `:enabled`?
- Does the Smart Proxy plugin need additional setup tasks (SSH keys, extra mounts, etc.)?

### 2. Register the Feature

Add the feature definition to `src/features.yaml`:

```yaml
<feature-name>:
  description: <Description of the feature>
  foreman:
    plugin_name: <foreman_plugin_name>
  foreman_proxy:
    plugin_name: <proxy_plugin_name>
  hammer: <hammer_gem_name>
  dependencies:
    - <dependency-feature>
```

Only include sections for applicable components. If a dependency is not user-facing, also add it with `internal: true`.

### 3. Create Smart Proxy Settings Template (if applicable)

If the feature has a `foreman_proxy` section, create:

```
src/roles/foreman_proxy/templates/settings.d/<plugin_name>.yml.j2
```

Minimal template:

```yaml
---
:enabled: {{ feature_enabled }}
```

Add additional settings in Ruby symbol notation as needed.

### 4. Create Feature Tasks (if applicable)

If the plugin needs setup beyond configuration:

```
src/roles/foreman_proxy/tasks/feature/<plugin_name>.yaml
```

The filename must match `foreman_proxy.plugin_name`. Tasks must notify:
- `Restart Foreman Proxy`
- `Refresh Foreman Proxy`

### 5. Validate

```bash
# Deploy with the new feature
./foremanctl deploy --add-feature=<feature-name>

# Verify it appears as enabled
./foremanctl features

# Run lint
cd src; ansible-lint
```

### 6. Write Tests

Create or update `tests/features_test.py` to verify the feature is functional after deployment.

## Checklist

- [ ] Feature registered in `src/features.yaml`
- [ ] Plugin names follow naming conventions
- [ ] Dependencies registered (with `internal: true` if non-user-facing)
- [ ] Smart Proxy settings template created (if proxy plugin)
- [ ] Feature tasks created (if additional setup needed)
- [ ] Tasks notify correct handlers
- [ ] ansible-lint passes on `src/`
- [ ] Feature deploys and shows as enabled
