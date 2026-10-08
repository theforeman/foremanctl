# Serving Foreman Infra Container Images

This guide covers configuring Foreman with the content/container feature to serve the container images for Foreman infrastructure deployment, so other machines can pull them from your server instead of the internet.

## Overview

When deploying Foreman and proxies in environments where we don't want the them to consume container images(for deployment) directly from the internet, we can configure our Foreman server (that has the content/container feature enabled) to serve these images as registry.

- **Proxy deployments** — a proxy can pull its images from its parent Foreman rather than from `quay.io`.
- **Hub and spoke** — a central Foreman serves the images to other Foreman servers it manages.

This is what `foremanctl setup-infra-images` does:

- Creates a Product for the infra container images
- Creates a container repository for each infra image
- Syncs the repositories from the configured upstream registry
- Verifies each repository is published in the container registry catalog(`/v2/_catalog`)
- Prints the registry paths

## Prerequisites

- A Foreman server deployed with the content/container feature (`foremanctl deploy` completed).
- Network access from the server to the upstream registry it syncs from(`https://quay.io` by default).
- Registry credentials **only if** your upstream registry requires authentication. The public `quay.io/foreman` images used by default are public and need no credentials.

## What Gets Synced

Every image that makes up a Foreman infrastructure deployment is published into a product named **`Foreman Infra Container Images`**:

| Repository      | Upstream image              |
| --------------- | --------------------------- |
| `foreman`       | `foreman/foreman`           |
| `foreman-proxy` | `foreman/foreman-proxy`     |
| `candlepin`     | `foreman/candlepin`         |
| `pulp`          | `foreman/pulp`              |
| `postgresql-16` | `sclorg/postgresql-16-c10s` |
| `valkey-8`      | `sclorg/valkey-8-c10s`      |

The whole set is published regardless of what will consume it. A machine pulling from the mirror only fetches the images its own deployment references — a proxy never pulls `foreman` or `candlepin` — so publishing everything costs nothing on the consuming side, and the same product serves proxies and hub-and-spoke servers alike.

Each repository is created as a `docker` content type, synced from the upstream registry, and pinned to the tag that matches the `base_tag` in `src/vars/infra-registry-images.yml`.

> **Downstream / vendor images:** vendors (for example, Red Hat Satellite) ship a `src/vars/vendor/infra-registry-images.yml` file that replaces this image list with their own — typically images synced from `registry.redhat.io`. When that file is present it is loaded automatically, so the repository names, upstream images, tags, and registry may differ from the default.

## Usage

### Basic Usage (public registry)

```bash
foremanctl setup-infra-images
```

This creates the `Foreman Infra Container Images` product in the default organization (`Default Organization`), creates and syncs a repository for every infra image, and prints the resulting registry paths. The same product can serve both proxy deployments and hub-and-spoke Foreman servers.

### Different Organization

```bash
foremanctl setup-infra-images \
  --organization "Acme_Corp"
```

### Authenticated Upstream Registry

Supply upstream registry credentials when the source registry requires authentication (for example, a Red Hat registry service account against `registry.redhat.io` in a downstream/vendor build). Both flags must be given together:

```bash
foremanctl setup-infra-images \
  --registry-username "12345678|myserviceaccount" \
  --registry-password "eyJhbGciOiJSUzUxMiJ9..."
```

The username and password are not persisted between runs.

### Parameters

| Parameter             | Required | Description                                                                 |
| --------------------- | -------- | --------------------------------------------------------------------------- |
| `--organization`      | No       | Organization to create the product in. Defaults to `Default Organization`.  |
| `--registry-username` | No\*     | Username for the upstream registry (e.g. a Red Hat registry service account).|
| `--registry-password` | No\*     | Password for the upstream registry. Omit for public registries. |

\* `--registry-username` and `--registry-password` must be supplied together, or both omitted for public registries such as `quay.io`.

## Command Output

On success the command prints a summary similar to:

```
==============================================
Foreman Infra Container Images Setup Complete
==============================================

Product: Foreman Infra Container Images
Repositories created: 6
  default_organization/foreman_infra_container_images/foreman
  default_organization/foreman_infra_container_images/foreman-proxy
  default_organization/foreman_infra_container_images/candlepin
  default_organization/foreman_infra_container_images/pulp
  default_organization/foreman_infra_container_images/postgresql-16
  default_organization/foreman_infra_container_images/valkey-8

The shared parent -- default_organization/foreman_infra_container_images -- is your
registry location for deployment.
```

The shared parent — `<org_label>/<product_label>` — is the registry path you can configure as registry mirror on the machine that pulls the images.

## Registry Path Format

The published paths follow Katello's default container `registry_name_pattern`:

```
<org_label>/<product_label>/<repository_name>
```

`<org_label>` and `<product_label>` are the lowercased Foreman **labels** (not the display names). For the defaults, `Default Organization` / `Foreman Infra Container Images` resolves to:

```
default_organization/foreman_infra_container_images
```

> **Note:** If your server has a customized `registry_name_pattern`, the paths could differ.

## Manual Verification

The command already asserts that every repository is present in the container registry catalog before it finishes. To inspect the catalog yourself:

```bash
SERVER=foreman.example.com

curl -sk -u USERNAME:PASSWORD \
  https://$SERVER/v2/_catalog | python3 -m json.tool
```

You should see the repositories under the product path, for example:

```
default_organization/foreman_infra_container_images/foreman
default_organization/foreman_infra_container_images/foreman-proxy
default_organization/foreman_infra_container_images/candlepin
default_organization/foreman_infra_container_images/pulp
default_organization/foreman_infra_container_images/postgresql-16
default_organization/foreman_infra_container_images/valkey-8
```

## Using the Published Images

After running `setup-infra-images`, configure the reported registry path as a registry mirror on the machine that will pull the images. That machine — a proxy or another Foreman server — then redirects its image pulls to this server's registry at that path.
