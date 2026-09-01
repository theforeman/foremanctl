# Proxy Image Serving Setup

This guide covers configuring Katello to serve container images for
proxy deployments.

## Overview

When deploying proxies in environments where we don't want the proxy to consume container images(for proxy deployment) directly from internet, we can configure our foreman server to serve these images as registry.

This is what the `foremanctl setup-proxy-images` does:

- Creates a Product for the proxy container images
- Creates a container repository for each required image
- Syncs the repositories from the configured upstream registry
- Verifies each repository is published in the container registry catalog
  (`/v2/_catalog`)
- Prints the registry paths

## Prerequisites

- A deployed and running Foreman/Katello server (`foremanctl deploy` completed).
- Network access from the server to the upstream registry it syncs from
  (`https://quay.io` by default).
- Registry credentials **only if** your upstream registry requires authentication. The public `quay.io/foreman` images used by default are public and need no credentials.

## What Gets Synced

By default the command syncs the public upstream Foreman images from `https://quay.io` into a product named **`Proxy Container Images`**:

| Repository     | Upstream image                |
| -------------- | ----------------------------- | 
| `foreman-proxy`| `foreman/foreman-proxy`       |
| `pulp`         | `foreman/pulp`                |
| `postgresql-16`| `sclorg/postgresql-16-c10s`   |
| `valkey-8`     | `sclorg/valkey-8-c10s`        |

Each repository is created as a `docker` content type, synced from the upstream
registry, and pinned to the tag that matches the `base_tag` in `proxy-registry-images.yaml`

> **Downstream / vendor images:** vendors (for example, Red Hat Satellite) ship a `src/vars/vendor/proxy-registry-images.yml` file that replaces this image set with their own — typically images synced from `registry.redhat.io`. When that file is present it is loaded automatically, so the product, repository names, upstream images, tags, and registry may differ from the default.

## Usage

### Basic Usage (public images)

```bash
foremanctl setup-proxy-images
```

This creates the `Proxy Container Images` product in the default organization
(`Default Organization`), creates and syncs all repositories, and prints the
resulting registry paths.

### Different Organization

```bash
foremanctl setup-proxy-images \
  --organization "Acme_Corp"
```

### Authenticated Upstream Registry

Supply upstream registry credentials when the source registry requires authentication (for example, a Red Hat registry service account against
`registry.redhat.io` in a downstream/vendor build). Both flags must be given
together:

```bash
foremanctl setup-proxy-images \
  --registry-username "12345678|myserviceaccount" \
  --registry-password "eyJhbGciOiJSUzUxMiJ9..."
```

The password is not persisted between runs.

### Parameters

| Parameter             | Required | Description                                                                 |
| --------------------- | -------- | --------------------------------------------------------------------------- |
| `--organization`      | No       | Organization to create the product in. Defaults to `Default Organization`.  |
| `--registry-username` | No\*     | Username for the upstream registry (e.g. a Red Hat registry service account).|
| `--registry-password` | No\*     | Password for the upstream registry. Omit for anonymous registries. |

\* `--registry-username` and `--registry-password` must be supplied together, or
   both omitted for public registries such as `quay.io`.

## Command Output

On success the command prints a summary similar to:

```
==============================================
Proxy Container Images Setup Complete
==============================================

Product: Proxy Container Images
Repositories created: 4
  default_organization/proxy_container_images/foreman-proxy
  default_organization/proxy_container_images/pulp
  default_organization/proxy_container_images/postgresql-16
  default_organization/proxy_container_images/valkey-8

The shared parent -- default_organization/proxy_container_images -- is your
registry location for deployment.
```

The shared parent — `<org_label>/<product_label>` — is the registry path you can configure as registry mirror
when deploying the proxy.

## Registry Path Format

The published paths follow Katello's default container `registry_name_pattern`:

```
<org_label>/<product_label>/<repository_name>
```

`<org_label>` and `<product_label>` are the lowercased Foreman **labels** (not
the display names). For the defaults, `Default Organization` /
`Proxy Container Images` resolves to:

```
default_organization/proxy_container_images
```

> **Note:** If your server has a customized `registry_name_pattern`, the paths could differ.

## Manual Verification

The command already asserts that every repository is present in the container
registry catalog before it finishes. To inspect the catalog yourself:

```bash
SERVER=foreman.example.com

curl -sk -u USERNAME:PASSWORD \
  https://$SERVER/v2/_catalog | python3 -m json.tool
```

You should see the repositories under the product path, for example:

```
default_organization/proxy_container_images/foreman-proxy
default_organization/proxy_container_images/pulp
default_organization/proxy_container_images/postgresql-16
default_organization/proxy_container_images/valkey-8
```

## Using with Proxy Deployment

After running `setup-proxy-images`, configure the reported registry path as registry mirror when deploying
the proxy. The proxy is configured to redirect its image pulls to the parent
server's registry at this path.
