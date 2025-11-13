# Deployment Design

## Deployment Paths

### Happy Path

The deployment utility should aim to support a minimal happy path for default deployment.

  1. Configure packaging repository
  2. Install `foremanctl` package
  3. Run deployment utility

### Advanced Path

The deployment utility should support advanced deployment paths that allow users to optimize and manage the procedure in more detail.
For example, pre-pulling images to reduce the core deployment utility runtime.

  1. Configure package repository
  2. Install `foremanctl` package
  3. Pull images
  4. Generate certificates
  5. Execute pre-requisite checks
  6. Run deployment utility
  7. Post deploy checks

### Authenticated Registry Handling

In the non-default case where the image sources are supplied from an authenticated location users will need to inject a login step.
For example, users might be consuming a custom build of the Foreman image.

In this case, the happy path becomes:

  1. Configure package repository
  2. Install `foremanctl` package
  3. Run deployment utility and provide registry username and token

The advanced path breaks down to:

  1. Configure package repository
  2. Install `foremanctl` package
  3. Login to registry with podman
  3. Pull images
  4. Generate certificates
  5. Execute pre-requisite checks
  6. Run deployment utility
  7. Post deploy checks

## Deployer Stages

The deployment utility will have internal execution stages.
Some of the stages will be made available to the user to run independently.

  1. Accept input parameters
  2. Validate input parameters
  3. Execute pre-requisite checks
    a. system requirements
    b. tuning requirements
    c. certificate requirements
  4. Place `.container` files
  5. Create podman secrets
  6. Reload systemd
  7. (re)start services
  8. Execute post deployment checks
  9. Post deployment message

## Configuration Handling

When defining how a service will handle configuration there are best practices in design that should be followed.
The best practices are listed in preferential order.

  1. Use native environment variables
  2. Rely on envsubst with default config files in the container
  3. Mount config file from secrets

## Existing deployment handling

When the user provides parameters to alter the deployment, the deployment utility stores these and re-uses them on the next run, even if the user did not pass in the parameter again.

## Container changes (Upgrades)

When the running containers change because the stream was changed in the configuration, the deployment utility will pull the new images and use the new images when starting services.

As there is currently no way for the deployment utility to verify which image version is used by a running service, the user is advised to stop all services before performing an upgrade.

The upgrade process is:

  1. Update `foremanctl`: `dnf upgrade foremanctl`
  :exclamation: Ensure `/usr/share/foremanctl/src/vars/images.yml` contains the right target version while `foremanctl` is not yet properly aligned with Foreman releases.
  2. Stop services: `systemctl stop foreman.target`
  3. Deploy updated containers: `foremanctl deploy`
  4. Optional: Prune old container images: `podman image prune --all`
