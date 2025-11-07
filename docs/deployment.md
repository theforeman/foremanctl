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

### Features and Flavors

To allow deployments with different sets of functionality enabled, the deployment utility supports features and flavors.

- A feature is an abstract representation of "the deployed system can now do X", usually implemented by enabling a Foreman/Pulp/Hammer plugin (or a collection of these).
- A flavor is a set of features that are enabled by default and can not be disabled. This is to allow common deployment types like "vanilla foreman", "katello", "satellite" and similar.

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

## External Database Support

The deployment utility supports connecting to an external PostgreSQL database instead of deploying a local database container. This allows for shared database infrastructure, managed database services, or dedicated database servers.

### Prerequisites

Before configuring external database support, ensure the following requirements are met:

#### Database Server Requirements
- PostgreSQL server accessible from the application server
- Required databases: `foreman`, `candlepin`, and `pulp`
- Database users with appropriate permissions for database creation and table management
- Network connectivity on the configured database port (default: 5432)

### External Database Configuration Parameters

The external database configuration is managed entirely through `foremanctl` command line parameters:

#### Global Database Parameters
- `--database-mode`: Set to `external` for external database deployment
- `--database-host`: Database server hostname or IP address
- `--database-port`: Database server port (default: 5432)
- `--database-ssl-mode`: SSL connection mode
  - Options: `disable`, `allow`, `prefer`, `require`, `verify-ca`, `verify-full`
  - Default: `disable`
- `--database-ssl-ca`: Path to SSL CA certificate file (required for `verify-ca` and `verify-full` modes)

#### Per-Service Database Configuration
Each service (Foreman, Candlepin, Pulp) can be configured with separate database credentials:

**Foreman Database:**
- `--foreman-database-name`: Database name (default: `foreman`)
- `--foreman-database-user`: Database user (default: `foreman`)
- `--foreman-database-password`: Database password

**Candlepin Database:**
- `--candlepin-database-name`: Database name (default: `candlepin`)
- `--candlepin-database-user`: Database user (default: `candlepin`)
- `--candlepin-database-password`: Database password

**Pulp Database:**
- `--pulp-database-name`: Database name (default: `pulp`)
- `--pulp-database-user`: Database user (default: `pulp`)
- `--pulp-database-password`: Database password

### Configuration Workflow

#### 1. Database Server Preparation

```bash
CREATE USER "foreman" WITH PASSWORD 'Foreman_Password';
CREATE DATABASE foreman OWNER foreman;
CREATE USER "candlepin" WITH PASSWORD 'Candlepin_Password';
CREATE DATABASE candlepin OWNER candlepin;
CREATE USER "pulp" WITH PASSWORD 'Pulpcore_Password';
CREATE DATABASE pulpcore OWNER pulp;
```

#### 2. Basic External Database Deployment

For a basic external database setup with default settings:

```bash
./foremanctl deploy \
  --database-mode=external \
  --database-host=database.example.com \
  --foreman-database-password=secure_foreman_password \
  --candlepin-database-password=secure_candlepin_password \
  --pulp-database-password=secure_pulp_password
```

#### 3. Advanced External Database Deployment

For production deployments with custom credentials and SSL:

```bash
./foremanctl deploy \
  --database-mode=external \
  --database-host=database.example.com \
  --database-port=5432 \
  --database-ssl-mode=require \
  --database-ssl-ca=/etc/ssl/certs/ca-cert.pem \
  --foreman-database-user=foreman_prod \
  --foreman-database-password=secure_foreman_password \
  --candlepin-database-user=candlepin_prod \
  --candlepin-database-password=secure_candlepin_password \
  --pulp-database-user=pulp_prod \
  --pulp-database-password=secure_pulp_password
```

#### 4. SSL-Enabled External Database

For secure connections with certificate verification:

```bash
./foremanctl deploy \
  --database-mode=external \
  --database-host=database.example.com \
  --database-ssl-mode=verify-full \
  --database-ssl-ca=/path/to/ca-certificate.pem
  --foreman-database-password=secure_foreman_password \
  --candlepin-database-password=secure_candlepin_password \
  --pulp-database-password=secure_pulp_password
```
