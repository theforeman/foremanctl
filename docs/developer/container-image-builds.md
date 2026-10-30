# Container Builds

All container images Foreman builds will live at `quay.io/foreman/$service:$tag`.
Dependent services that we do not build ourselves will have a copy of containers stored in Foreman’s quay.io to allow tagging with the Foreman version.

There will be three flavors of Foreman containers:

  * Vanilla Foreman
  * Foreman + Katello
  * Foreman + all plugins

Stage versions of containers will have stage in the namespace and be published in the Foreman's quay repository:

  * `quay.io/foreman/stage/$service:$tag`

The base image will be `quay.io/centos/centos:stream10`.

## Containerfile Artifacts

Container files will be stored in repositories for each service that mimic packaging.

  * [foreman-oci-images](https://github.com/theforeman/foreman-oci-images)
  * [pulp-oci-images](https://github.com/theforeman/pulp-oci-images)
  * [candlepin-oci-images](https://github.com/theforeman/candlepin-oci-images)

## Container Image Tagging

The tagging rules for release containers images:

  * Project version: X.Y.Z
  * Project version: X.Y
  * Foreman version: foreman-X.Y
  * Foreman version: foreman-X.Y.Z

The tagging rules for nightly container images:

  * nightly
  * Project version: X.Y.Z

## Testing a Packit Pull Request

Use `forge deploy-packit` to build the Foreman image with a Packit pull request installed:

```bash
./forge deploy-packit --pr 100
# Or provide a GitHub pull request URL instead:
./forge deploy-packit --pr-url https://github.com/theforeman/foreman/pull/100
./foremanctl deploy
```

The command targets `quadlet` by default, or the host selected with `--target-host`. It ensures Podman is installed, copies the Containerfile to a temporary directory on that machine, then builds the image as root under the configured Foreman reference (by default `quay.io/foreman/foreman:nightly`). The temporary build context is removed afterward. The Foreman image quadlet created during deployment uses this same reference with `Policy=missing`, so the local patched image is used when available. Run `foremanctl deploy` against the same target.

`--pr` defaults to the `theforeman/foreman` repository; use `--repo-org` and `--repo-name` to select another repository. Alternatively, pass a GitHub pull request URL with `--pr-url`. `--base-image` can override the base image.

