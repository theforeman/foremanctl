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

For a complete build and deployment in one command, use `forge deploy-packit-stack` as described below. Use the individual commands in this section when you want to prepare images without deploying them yet.

Repeat `--pr-url` to combine core and plugin PRs for the selected component. All supplied Packit repositories are enabled before packages are upgraded in one DNF transaction, so dependencies between the PR builds can be resolved together. Single-PR commands using `--pr` or `--pr-url` continue to work.

For example, to test changes across Foreman, Smart Proxy, and their Ansible plugins (replace these example PR numbers with your own):

```bash
# Pull base images before building any PR images.
./foremanctl pull-images --add-feature foreman-proxy

# Foreman core and its Ansible plugin in one image build.
./forge deploy-packit \
  --pr-url https://github.com/theforeman/foreman/pull/100 \
  --pr-url https://github.com/theforeman/foreman_ansible/pull/200

# Smart Proxy core and its Ansible plugin in a separate image build.
./forge deploy-packit --component foreman-proxy \
  --pr-url https://github.com/theforeman/smart-proxy/pull/300 \
  --pr-url https://github.com/theforeman/smart_proxy_ansible/pull/400
```

Then run your normal `foremanctl deploy` command with the required features and `forge test`. If services were already running, stop `foreman.target` on the target host before deploying so the containers are recreated with the new images.

Foreman and Foreman Proxy use separate images and require separate invocations. For a standalone proxy, add `--target-host proxy` to the proxy build command and use `foremanctl deploy-proxy`. Build on each host that needs those changes; images are not transferred between hosts automatically.

Each PR needs a successful RHEL 10 Packit build. The image build fails if any selected PR repository has no available packages. Plugin packages must already be installed in the selected base image: the build upgrades existing packages rather than installing new plugins. Only packages available from the selected PR repositories are requested for upgrade, while other enabled repositories remain available to resolve dependencies.

Use full URLs for all PRs in a combined build; `--pr-url` cannot be combined with `--pr`, `--repo-org`, or `--repo-name`. Each URL may specify a different organization or repository. Repeated identical URLs are ignored.

Running `foremanctl pull-images` after building replaces the local PR images with registry images. Run it before the sequence above, or to reset the images before testing a different combination.

### Building and deploying in one command

Use `forge deploy-packit-stack` to build and deploy a complete combination of PRs. The VMs and their package repositories must already be configured, as for a normal `foremanctl deploy` or `deploy-proxy` run.

For a Foreman server with its local proxy:

```bash
./forge deploy-packit-stack \
  --foreman-pr-url https://github.com/theforeman/foreman/pull/100 \
  --foreman-pr-url https://github.com/theforeman/foreman_ansible/pull/200 \
  --proxy-pr-url https://github.com/theforeman/smart-proxy/pull/300 \
  --proxy-pr-url https://github.com/theforeman/smart_proxy_ansible/pull/400 \
  --deploy-args='--initial-admin-password changeme --tuning development --add-feature ansible'
```

Repeat either PR option to combine core and plugin builds in one RPM transaction per component. Only one component needs PRs; omit the other component's options when testing only server or proxy changes. Supplying proxy PRs for a server automatically adds the `foreman-proxy` feature.

For a standalone proxy, first generate an auth bundle on its Foreman server as usual, then run:

```bash
./forge deploy-packit-stack --deployment proxy \
  --proxy-pr-url https://github.com/theforeman/smart-proxy/pull/300 \
  --proxy-pr-url https://github.com/theforeman/smart_proxy_ansible/pull/400 \
  --deploy-args='--auth-bundle /absolute/path/proxy.example.com.tar.gz --foreman-fqdn foreman.example.com'
```

The server workflow targets `quadlet` and calls `foremanctl deploy`. The standalone proxy workflow targets `proxy` and calls `foremanctl deploy-proxy`; it accepts only proxy PRs. Each selects the matching default flavor (`katello` or `foreman-proxy-content`), with an explicit `--flavor` in `--deploy-args` taking precedence.

Pass existing deployment options through `--deploy-args`. Quoted values are preserved, for example `--deploy-args='--initial-organization "My organization" --tuning development'`. The command validates the options against the existing deployment CLI before changing any hosts, and normal persisted deployment parameters continue to apply.

For each selected component, the workflow pulls a fresh base image and builds the requested PRs. Other runtime images are pulled by the normal deployment as needed. After all builds succeed, it stops an existing `foreman.target` and deploys the local images. A failed build stops the workflow before services are stopped or deployment is attempted. Deployment failures are returned to the caller with the deployment output.

No separate `pull-images` or service-stop command is needed. The image builds require registry access and successful EL10 Packit builds; air-gapped deployment is not supported by this workflow. As with `deploy-packit`, plugin RPMs must already be installed in their base image, and the required plugin features must be enabled with deployment options.
