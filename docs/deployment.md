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

### Features and Profiles

To allow deployments with different sets of functionality enabled, the deployment utility supports features and profiles.

- A feature is an abstract representation of "the deployed system can now do X", usually implemented by enabling a Foreman/Pulp/Hammer plugin (or a collection of these). 
- A profile is a set of features that are enabled by default and can not be disabled. This is to allow common deployment types like "vanilla foreman", "katello", "satellite" and similar.

Additionally to the functionality offered by plugins, we define the following "base" features:
- `foreman` to deploy the main Rails app and make the deployment a "Server"
- `foreman-proxy` to deploy the Foreman Proxy code
- `hammer` to deploy the base CLI

These base features control which plugins are enabled when a feature is requested.
- `foreman` + `remote_execution` = `foreman_remote_execution`
- `foreman-proxy` + `remote_execution` = `smart_proxy_remote_execution_ssh`
- `hammer` + `remote_execution` = `hammer_cli_foreman_remote_execution`

A deployment can have multiple base features enabled.

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
