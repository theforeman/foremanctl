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
  --foreman-initial-admin-password=changeme
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
  --pulp-database-password=secure_pulp_password \
```

#### 4. SSL-Enabled External Database

For secure connections with certificate verification:

```bash
./foremanctl deploy \
  --database-mode=external \
  --database-host=database.example.com \
  --database-ssl-mode=verify-full \
  --database-ssl-ca=/path/to/ca-certificate.pem \
  --foreman-initial-admin-password=changeme
```
