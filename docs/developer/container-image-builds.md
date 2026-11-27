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
# Provide a GitHub pull request URL:
./forge deploy-packit --pr-url https://github.com/theforeman/foreman/pull/100
# Or provide the pr and optionally repo-org and repo-name parts:
./forge deploy-packit --pr 100 --repo-org theforeman --repo-name foreman

# Don't forget to stop the services on the target, if they were running before:
systemctl stop foreman.target

./foremanctl deploy
```

The command targets `quadlet` by default, or the host selected with `--target-host`. It ensures Podman is installed, copies the Containerfile to a temporary directory on that machine, then builds the image as root under the configured Foreman reference (by default `quay.io/foreman/foreman:nightly`). The temporary build context is removed afterward. The Foreman image quadlet created during deployment uses this same reference with `Policy=missing`, so the local patched image is used when available. Run `foremanctl deploy` against the same target.

`--pr` defaults to the `theforeman/foreman` repository; use `--repo-org` and `--repo-name` to select another repository. Alternatively, pass a GitHub pull request URL with `--pr-url`. `--base-image` can override the base image without changing the output image reference.

For Smart Proxy or its plugins, select `--component foreman-proxy`:

```bash
# Defaults to the theforeman/smart-proxy repository:
./forge deploy-packit --component foreman-proxy --pr 100
# The existing repository overrides also work for proxy plugins and forks:
./forge deploy-packit --component foreman-proxy \
  --pr 100 --repo-org theforeman --repo-name smart_proxy_ansible
# Or provide a PR URL:
./forge deploy-packit --component foreman-proxy \
  --pr-url https://github.com/theforeman/smart-proxy/pull/100
```

The component selects both the base and output image from the configured image name and tag (`foreman_proxy_container_image` and `foreman_proxy_container_tag` for Foreman Proxy). The image's original container user is preserved. Foreman remains the default component.

The component does not select the target host. For a standalone proxy, add `--target-host proxy` and deploy with `foremanctl deploy-proxy`; for the proxy on the Foreman server, use the default `quadlet` target and `foremanctl deploy --add-feature foreman-proxy`.

In CI, run `forge deploy-packit` after `foremanctl pull-images` and before deployment on each host that needs the PR. `pull-images` forces registry pulls and would replace an image built earlier. Each host builds its own image in root's Podman store; deployment uses it with `Policy=missing`.

### Combining PRs from multiple repositories

Use the same command for one or many PRs, from one or several repositories:

```bash
./forge deploy-packit \
  --foreman-pr-url https://github.com/theforeman/foreman/pull/100 \
  --foreman-pr-url https://github.com/theforeman/foreman_ansible/pull/200 \
  --proxy-pr-url https://github.com/theforeman/smart-proxy/pull/300 \
  --proxy-pr-url https://github.com/theforeman/smart_proxy_ansible/pull/400
```

Each component's Packit repositories are enabled before its packages are upgraded in one RPM transaction. The build fails if any selected repository has no packages. Existing `--pr-url` invocations remain supported; grouped component options let one invocation prepare both images.

Combining PR builds combines changes across distinct packages. Two builds of the same package do not merge their source changes; use a PR branch containing the combined changes for that package.

Without `--deploy`, builds can reuse the current local base image, including previous PR changes. Add `--deploy` for a fresh base and automatic deployment, as below. PR repositories need successful EL10 builds and plugin RPMs must already be installed in the base image.

### Building and deploying in one command

Use the same Packit commands for one PR or multiple PRs, from one repository or several. Without `--deploy`, they only build images. Add `--deploy` to pull fresh component bases, build every requested image, and run the normal deployment in the same Ansible execution.

For a server and its local proxy:

```bash
./forge deploy-packit --deploy \
  --foreman-pr-url https://github.com/theforeman/foreman/pull/100 \
  --foreman-pr-url https://github.com/theforeman/foreman_ansible/pull/200 \
  --proxy-pr-url https://github.com/theforeman/smart-proxy/pull/300 \
  --proxy-pr-url https://github.com/theforeman/smart_proxy_ansible/pull/400 \
  --add-feature foreman-proxy --add-feature ansible \
  --initial-admin-password changeme --tuning development
```

For a standalone proxy:

```bash
./forge deploy-proxy-packit --deploy \
  --proxy-pr-url https://github.com/theforeman/smart-proxy/pull/300 \
  --proxy-pr-url https://github.com/theforeman/smart_proxy_ansible/pull/400 \
  --auth-bundle /absolute/path/proxy.example.com.tar.gz \
  --foreman-fqdn foreman.example.com --flavor foreman-proxy-content
```

Omit URLs to test fewer PRs; omit `--deploy` to prepare images without changing services. Existing `--pr`, `--pr-url`, `--component`, and repository options remain supported and use the same underlying builder. Use `--foreman-pr-url` and `--proxy-pr-url` to group both components explicitly. Native deployment options are imported from the production metadata, so no quoted argument string or separate parser is involved.

The commands require existing, reachable VMs in inventory with package repositories configured. They work on a fresh VM with no Foreman deployment, and can replace an existing deployment. For a standalone proxy, generate its auth bundle on the Foreman server first. Server deployment targets `quadlet`; standalone proxy deployment targets `proxy`. An explicit `--target-host` remains available for build-only use; deployment must use the matching inventory host.

Image builds finish before an existing `foreman.target` is stopped. A failed build leaves running services alone and prevents deployment. On a fresh target, the stop step is skipped. Other runtime images are obtained by the production deployment as needed. Saved deployment settings and reset options follow the existing production CLI semantics; specify the appropriate `--flavor` when switching deployment types using the same state directory.

Server deployments testing proxy images need `--add-feature foreman-proxy`. Plugin packages must already be installed in their base images, and plugin features must be enabled as usual. Every PR needs a successful EL10 Packit build. This online image-building workflow does not support air-gapped deployment.

This interface requires obsah's explicit metadata-file imports ([obsah PR #153](https://github.com/theforeman/obsah/pull/153)). Until that support is released, `src/requirements.txt` temporarily pins the tested obsah commit. Run `./setup-environment` to install it before using these commands or running the development-tool tests. If your virtualenv already contains released obsah 1.12, run `pip install --force-reinstall --no-deps -r src/requirements.txt` inside it, since pip can retain the existing package with the same version. Replace the pin with a released minimum version before merging this follow-up.
