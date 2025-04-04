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
