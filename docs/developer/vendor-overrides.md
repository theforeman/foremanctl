# Vendor overrides

As a downstream consumer of `foremanctl` you might want to diverge from defaults `foremanctl` offers.
Here's how.

## Parameters

If you want to override parameters, ship a playbook definition that overrides the parameter you want and add it to the `includes` of the command you want to alter.

Example:
`src/playbooks/_vendor_overrides/deploy/metadata.obsah.yaml`:
```yaml
---
variables:
  flavor:
    choices:
      - satellite
```

`src/playbooks/deploy/metadata.obsah.yaml`:
```yaml
…
include:
  …
  - _vendor_overrides/deploy
```

## Features

Changes to features can be done by providing a (partial) feature definition in a YAML file in `src/features.d` (probably shipped as `/usr/share/foremanctl/src/features.d`).

### Adding features

If you want to add a new feature, ship its definition in a file inside `src/features.d`.

Example:
```yaml
cookies:
  description: Delicious enterprise cookies
  foreman:
    plugin_name: foreman_cookies
```

### Removing features

If you want to hide a previously defined feature (fully removing is not possible), set it to `internal: true` in a file inside `src/features.d`.

Example:
```yaml
content/ostree:
  internal: true
```

### Changing features

If you want to update any part of a previously defined feature, provide the changes in a file inside `src/features.d`.

Example:
```yaml
iop:
  description: Lightspeed
```

## Images

See [Image Management](deployment.md#image-management) in the Deployment documentation.
