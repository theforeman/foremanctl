# Foremanctl User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Configuration Options](#configuration-options)
6. [Common Use Cases](#common-use-cases)
7. [Certificate Management](#certificate-management)
8. [External Database](#external-database)
9. [External Authentication](#external-authentication)
10. [Troubleshooting](#troubleshooting)
11. [Upgrades](#upgrades)
12. [Uninstallation](#uninstallation)

---

## Introduction

Foremanctl is a modern deployment tool for Foreman and Katello that uses Podman containers and Ansible automation. It provides a simplified, containerized deployment experience for Foreman infrastructure management.

### What is Foreman?
Foreman is a complete lifecycle management tool for physical and virtual servers. It provides provisioning, configuration management, and monitoring capabilities.

### What is Katello?
Katello is a plugin for Foreman that adds content management capabilities, including repository synchronization, content views, and subscription management.

### Key Features
- **Container-based deployment**: All services run in Podman containers
- **Systemd integration**: Uses Podman quadlets for service management
- **Modular features**: Enable only the features you need
- **External database support**: Connect to existing PostgreSQL databases
- **External authentication**: Integrate with FreeIPA/IDM or Active Directory
- **Tuning profiles**: Optimize for different workload sizes

### Supported Versions
- **Foreman**: 3.18
- **Katello**: 4.20
- **Pulp**: 3.85
- **Candlepin**: 4.6
- **OS**: EL9 (CentOS Stream 9, RHEL 9, etc.)

---

## System Requirements

### Hardware Requirements

**Minimum Configuration (Development/Testing):**
- CPU: 4 cores
- RAM: 8 GB
- Disk: 50 GB free space

**Recommended Configuration (Production):**
- CPU: 8+ cores
- RAM: 16+ GB
- Disk: 100+ GB free space (more for content storage)

### Software Requirements

**Operating System:**
- Enterprise Linux 9 (EL9):
  - CentOS Stream 9 (recommended and tested)
  - RHEL 9
  - Rocky Linux 9
  - AlmaLinux 9

**Required Packages:**
- Podman (container runtime)
- systemd (service management)
- ansible-core 2.14+ (automation engine)

**Network Requirements:**
- Fully qualified domain name (FQDN) configured
- Hostname resolution working correctly
- Internet access for downloading container images (or access to a private registry)

### Firewall Ports

The following ports need to be accessible:

| Port  | Protocol | Service              | Purpose                    |
|-------|----------|----------------------|----------------------------|
| 80    | TCP      | HTTP                 | HTTP access to Foreman     |
| 443   | TCP      | HTTPS                | HTTPS access to Foreman    |
| 5432  | TCP      | PostgreSQL           | Database (if external)     |
| 8140  | TCP      | Puppet               | Puppet agent communication |
| 9090  | TCP      | Smart Proxy          | Smart Proxy API            |

---

## Installation

### Step 1: Configure Package Repository

Add the foremanctl COPR repository:

```bash
# For EL9 systems
sudo dnf copr enable @theforeman/foremanctl rhel-9-x86_64
```

### Step 2: Install Foremanctl

```bash
sudo dnf install foremanctl
```

This will install:
- `foremanctl` - The main deployment tool
- Ansible and required collections
- Container image definitions
- Configuration templates

### Step 3: Verify Installation

```bash
foremanctl --help
```

You should see the help output listing available commands and options.

---

## Quick Start

### Basic Deployment (Development/Testing)

Deploy Foreman with Katello using default settings:

```bash
sudo foremanctl deploy \
  --foreman-initial-admin-password=changeme \
  --tuning development
```

This command will:
1. Pull required container images
2. Generate self-signed certificates
3. Deploy PostgreSQL, Redis, Candlepin, Pulp, and Foreman
4. Configure and start all services
5. Create initial admin user

**Deployment time:** Approximately 10-20 minutes depending on network speed.

### Access Foreman

After deployment completes:

1. Open a web browser
2. Navigate to: `https://<your-hostname>`
3. Login with:
   - Username: `admin`
   - Password: `changeme` (or whatever you specified)

### Verify Services

Check that all services are running:

```bash
# Check overall system target
sudo systemctl status foreman.target

# Check individual services
sudo systemctl status foreman-candlepin.service
sudo systemctl status foreman-postgresql.service
sudo systemctl status foreman-pulpcore-api.service
sudo systemctl status foreman-pulpcore-content.service
sudo systemctl status foreman-pulpcore-worker@*.service
sudo systemctl status foreman-redis.service
sudo systemctl status foreman.service
sudo systemctl status foreman-httpd.service
```

---

## Configuration Options

### Deployment Parameters

Foremanctl accepts parameters to customize your deployment. Parameters are passed on the command line using `--parameter-name=value` format.

#### Essential Parameters

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `--foreman-initial-admin-username` | Initial admin username | `admin` | `--foreman-initial-admin-username=administrator` |
| `--foreman-initial-admin-password` | Initial admin password | (required) | `--foreman-initial-admin-password=SecurePass123` |
| `--tuning` | Performance tuning profile | `default` | `--tuning=development` or `--tuning=medium` |
| `--certificate-source` | Certificate source | `default` | `--certificate-source=default` or `installer` |
| `--certificate-cname` | Additional DNS names | (none) | `--certificate-cname=foreman.example.com` |

#### Tuning Profiles

Available tuning profiles optimize resource usage for different deployment sizes:

- **`development`**: Minimal resources, suitable for testing
  - Puma workers: 2
  - Pulp workers: 2
  - Minimal memory footprint

- **`default`**: Balanced configuration
  - Puma workers: 4
  - Pulp workers: 4
  - Standard production settings

- **`medium`**: Higher capacity
  - Puma workers: 8
  - Pulp workers: 8
  - Suitable for larger deployments

- **`large`**: Maximum performance
  - Puma workers: 16
  - Pulp workers: 16
  - High-capacity production environments

Example:
```bash
sudo foremanctl deploy \
  --foreman-initial-admin-password=changeme \
  --tuning=medium
```

#### Advanced Tuning

You can override specific tuning parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--foreman-puma-workers` | Number of Puma workers | (depends on tuning) |
| `--pulp-worker-count` | Number of Pulp workers | (depends on tuning) |
| `--foreman-database-pool` | Database connection pool size | (auto-calculated) |

### Features

Foremanctl uses a modular feature system. Enable additional features with `--add-feature`:

#### Base Features

- **`foreman`**: Main Foreman server (always enabled)
- **`katello`**: Content management (enabled by default)
- **`hammer`**: CLI tool
- **`foreman-proxy`**: Smart Proxy for remote systems

#### Plugin Features

- **`remote_execution`**: Remote command execution (enabled by default)
- **`ansible`**: Ansible integration
- **`rh_cloud`**: Red Hat Cloud connector
- **`discovery`**: Bare-metal discovery
- **`openscap`**: Security compliance scanning
- **`bootdisk`**: Boot disk creation

#### Content Plugins

- **`content/rpm`**: RPM content management (enabled by default)
- **`content/container`**: Container image management (enabled by default)

Example - Enable Hammer CLI:
```bash
sudo foremanctl deploy \
  --foreman-initial-admin-password=changeme \
  --add-feature=hammer
```

Example - Enable multiple features:
```bash
sudo foremanctl deploy \
  --foreman-initial-admin-password=changeme \
  --add-feature=hammer \
  --add-feature=ansible \
  --add-feature=discovery
```

---

## Common Use Cases

### 1. Production Deployment with Custom Settings

```bash
sudo foremanctl deploy \
  --foreman-initial-admin-username=sysadmin \
  --foreman-initial-admin-password=StrongPassword123! \
  --tuning=medium \
  --certificate-cname=foreman.mycompany.com \
  --certificate-cname=satellite.mycompany.com
```

### 2. Minimal Development Environment

```bash
sudo foremanctl deploy \
  --foreman-initial-admin-password=changeme \
  --tuning=development
```

### 3. Deployment with Hammer CLI

```bash
sudo foremanctl deploy \
  --foreman-initial-admin-password=changeme \
  --add-feature=hammer
```

After deployment, use Hammer:
```bash
hammer --username admin --password changeme organization list
```

### 4. Deployment with External Authentication

```bash
# First, enroll system in FreeIPA/IDM
# Then deploy with IPA authentication
sudo foremanctl deploy \
  --foreman-initial-admin-password=changeme \
  --external-authentication=ipa
```

### 5. Deployment with External Database

See [External Database](#external-database) section for detailed instructions.

### 6. Production Deployment with All Features

```bash
sudo foremanctl deploy \
  --foreman-initial-admin-password=SecurePassword123! \
  --tuning=large \
  --add-feature=hammer \
  --add-feature=ansible \
  --add-feature=remote_execution \
  --add-feature=discovery \
  --certificate-cname=foreman.prod.example.com
```

---

## Certificate Management

Foremanctl manages SSL/TLS certificates for secure communication between services.

### Default Certificates (Self-Signed)

By default, foremanctl generates self-signed certificates:

```bash
sudo foremanctl deploy --foreman-initial-admin-password=changeme
```

**Certificate locations:**
- CA Certificate: `/root/certificates/certs/ca.crt`
- Server Certificate: `/root/certificates/certs/<hostname>.crt`
- Server Key: `/root/certificates/private/<hostname>.key`
- Client Certificate: `/root/certificates/certs/<hostname>-client.crt`

### Certificate Properties
- **Key Size**: 4096-bit RSA
- **Validity**: 20 years
- **Hash Algorithm**: SHA256

### Multiple DNS Names (CNAMEs)

Add alternative DNS names to certificates:

```bash
sudo foremanctl deploy \
  --foreman-initial-admin-password=changeme \
  --certificate-cname=foreman.example.com \
  --certificate-cname=satellite.example.com \
  --certificate-cname=api.example.com
```

All specified names will be included in the Subject Alternative Name (SAN) field.

### Using Installer Certificates

If migrating from foreman-installer, use existing certificates:

```bash
sudo foremanctl deploy \
  --foreman-initial-admin-password=changeme \
  --certificate-source=installer
```

**Required certificate locations:**
- CA: `/root/ssl-build/katello-default-ca.crt`
- Server Cert: `/root/ssl-build/<hostname>/<hostname>-apache.crt`
- Server Key: `/root/ssl-build/<hostname>/<hostname>-apache.key`

### Viewing Certificates

```bash
# View CA certificate
sudo openssl x509 -in /root/certificates/certs/ca.crt -text -noout

# View server certificate
sudo openssl x509 -in /root/certificates/certs/$(hostname -f).crt -text -noout
```

---

## External Database

Foremanctl supports connecting to an external PostgreSQL database instead of deploying a local database container.

### Prerequisites

1. **PostgreSQL Server** (version 13+)
2. **Network connectivity** to the database server
3. **Three databases created**:
   - `foreman`
   - `candlepin`
   - `pulp`
4. **Database users with permissions**

### Step 1: Prepare Database Server

On your PostgreSQL server, create databases and users:

```sql
-- Create users
CREATE USER foreman WITH PASSWORD 'foreman_secure_password';
CREATE USER candlepin WITH PASSWORD 'candlepin_secure_password';
CREATE USER pulp WITH PASSWORD 'pulp_secure_password';

-- Create databases
CREATE DATABASE foreman OWNER foreman;
CREATE DATABASE candlepin OWNER candlepin;
CREATE DATABASE pulp OWNER pulp;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE foreman TO foreman;
GRANT ALL PRIVILEGES ON DATABASE candlepin TO candlepin;
GRANT ALL PRIVILEGES ON DATABASE pulp TO pulp;
```

Configure PostgreSQL to accept connections from the Foreman server:

```bash
# Edit pg_hba.conf
# Add line (adjust IP/network as needed):
host    all    all    192.168.1.0/24    scram-sha-256
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### Step 2: Deploy with External Database

#### Basic External Database

```bash
sudo foremanctl deploy \
  --foreman-initial-admin-password=changeme \
  --database-mode=external \
  --database-host=db.example.com \
  --foreman-database-password=foreman_secure_password \
  --candlepin-database-password=candlepin_secure_password \
  --pulp-database-password=pulp_secure_password
```

#### External Database with Custom Port

```bash
sudo foremanctl deploy \
  --foreman-initial-admin-password=changeme \
  --database-mode=external \
  --database-host=db.example.com \
  --database-port=5433 \
  --foreman-database-password=foreman_secure_password \
  --candlepin-database-password=candlepin_secure_password \
  --pulp-database-password=pulp_secure_password
```

#### External Database with SSL

```bash
sudo foremanctl deploy \
  --foreman-initial-admin-password=changeme \
  --database-mode=external \
  --database-host=db.example.com \
  --database-ssl-mode=require \
  --database-ssl-ca=/path/to/ca-certificate.pem \
  --foreman-database-password=foreman_secure_password \
  --candlepin-database-password=candlepin_secure_password \
  --pulp-database-password=pulp_secure_password
```

**SSL Modes:**
- `disable`: No SSL
- `allow`: Try SSL, fall back to non-SSL
- `prefer`: Prefer SSL (default for most clients)
- `require`: Require SSL, but don't verify CA
- `verify-ca`: Require SSL and verify CA certificate
- `verify-full`: Require SSL, verify CA and hostname

#### External Database with Custom Names

```bash
sudo foremanctl deploy \
  --foreman-initial-admin-password=changeme \
  --database-mode=external \
  --database-host=db.example.com \
  --foreman-database-name=foreman_prod \
  --foreman-database-user=foreman_app \
  --foreman-database-password=foreman_secure_password \
  --candlepin-database-name=candlepin_prod \
  --candlepin-database-user=candlepin_app \
  --candlepin-database-password=candlepin_secure_password \
  --pulp-database-name=pulp_prod \
  --pulp-database-user=pulp_app \
  --pulp-database-password=pulp_secure_password
```

### External Database Parameters Reference

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--database-mode` | `internal` or `external` | `internal` |
| `--database-host` | Database server hostname/IP | `localhost` |
| `--database-port` | Database server port | `5432` |
| `--database-ssl-mode` | SSL connection mode | `disable` |
| `--database-ssl-ca` | Path to SSL CA certificate | - |
| `--foreman-database-name` | Foreman database name | `foreman` |
| `--foreman-database-user` | Foreman database user | `foreman` |
| `--foreman-database-password` | Foreman database password | (required) |
| `--candlepin-database-name` | Candlepin database name | `candlepin` |
| `--candlepin-database-user` | Candlepin database user | `candlepin` |
| `--candlepin-database-password` | Candlepin database password | (required) |
| `--pulp-database-name` | Pulp database name | `pulp` |
| `--pulp-database-user` | Pulp database user | `pulp` |
| `--pulp-database-password` | Pulp database password | (required) |

---

## External Authentication

Foremanctl supports integration with FreeIPA/IDM or Active Directory for Kerberos-based authentication.

### Prerequisites

1. **Enrolled system**: The Foreman server must be enrolled in FreeIPA/IDM or Active Directory
2. **Keytab**: Kerberos service principal keytab must be available
3. **DNS**: Proper DNS configuration

### Enrollment in FreeIPA

Before deploying Foreman, enroll the system:

```bash
# Install IPA client
sudo dnf install ipa-client

# Enroll system
sudo ipa-client-install --domain=example.com --realm=EXAMPLE.COM
```

### Deploy with External Authentication

#### WebUI Authentication Only

```bash
sudo foremanctl deploy \
  --foreman-initial-admin-password=changeme \
  --external-authentication=ipa
```

This enables Kerberos authentication for the web UI only.

#### WebUI and API Authentication

```bash
sudo foremanctl deploy \
  --foreman-initial-admin-password=changeme \
  --external-authentication=ipa_with_api
```

This enables Kerberos authentication for:
- Web UI
- API
- Hammer CLI (if hammer feature is enabled)

#### Custom PAM Service

Use a specific FreeIPA HBAC service:

```bash
sudo foremanctl deploy \
  --foreman-initial-admin-password=changeme \
  --external-authentication=ipa_with_api \
  --external-authentication-pam-service=foreman-prod
```

### Using Hammer with Kerberos

When `--external-authentication=ipa_with_api` is configured and hammer is enabled:

```bash
# Obtain Kerberos ticket
kinit user@EXAMPLE.COM

# Use hammer without password
hammer organization list
```

### External Authentication Parameters

| Parameter | Description | Options | Default |
|-----------|-------------|---------|---------|
| `--external-authentication` | Enable external auth | `ipa`, `ipa_with_api` | (disabled) |
| `--external-authentication-pam-service` | PAM service name | (custom name) | `foreman` |

---

## Troubleshooting

### General Troubleshooting Steps

1. **Check service status:**
   ```bash
   sudo systemctl status foreman.target
   ```

2. **Check individual service logs:**
   ```bash
   sudo journalctl -u foreman.service -f
   sudo journalctl -u foreman-pulpcore-api.service -f
   sudo journalctl -u foreman-candlepin.service -f
   ```

3. **Check Ansible deployment logs:**
   ```bash
   sudo cat /var/lib/foremanctl/foremanctl.log
   ```

4. **Verify containers are running:**
   ```bash
   sudo podman ps
   ```

### Common Issues

#### Issue: Deployment fails with "hostname not found"

**Cause**: System hostname is not properly configured.

**Solution:**
```bash
# Set hostname
sudo hostnamectl set-hostname foreman.example.com

# Verify FQDN
hostname -f

# Ensure /etc/hosts has proper entry
echo "192.168.1.100 foreman.example.com foreman" | sudo tee -a /etc/hosts

# Re-run deployment
sudo foremanctl deploy --foreman-initial-admin-password=changeme
```

#### Issue: Cannot access Foreman web UI

**Cause**: Firewall blocking ports or services not started.

**Solution:**
```bash
# Check if httpd service is running
sudo systemctl status foreman-httpd.service

# Open firewall ports
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

# Check if you can connect locally
curl -k https://localhost
```

#### Issue: Database connection errors

**Cause**: Database not accessible or credentials incorrect.

**Solution:**
```bash
# For internal database, check PostgreSQL service
sudo systemctl status foreman-postgresql.service

# For external database, test connectivity
psql -h db.example.com -U foreman -d foreman -c "SELECT 1;"

# Check database configuration in secrets
sudo podman secret inspect --showsecret foreman-database-yml
```

#### Issue: Services fail to start after reboot

**Cause**: Systemd target not enabled.

**Solution:**
```bash
# Enable foreman target
sudo systemctl enable foreman.target

# Start all services
sudo systemctl start foreman.target
```

#### Issue: Pulp workers not starting

**Cause**: Resource constraints or database issues.

**Solution:**
```bash
# Check worker logs
sudo journalctl -u foreman-pulpcore-worker@1.service -f

# Restart workers
sudo systemctl restart foreman-pulpcore-worker@*.service

# Check resource usage
free -h
df -h
```

#### Issue: Certificate errors in browser

**Cause**: Self-signed certificates not trusted by browser.

**Solution:**
- Accept the certificate exception in your browser, OR
- Import the CA certificate into your browser/system trust store:

```bash
# Copy CA cert to your local machine
sudo cat /root/certificates/certs/ca.crt

# On your local machine (varies by OS):
# - Linux: Copy to /etc/pki/ca-trust/source/anchors/ and run update-ca-trust
# - macOS: Import into Keychain Access
# - Windows: Import via Certificate Manager
```

### Getting Help

**View all available parameters:**
```bash
foremanctl deploy --help
```

**Check configuration:**
```bash
# List podman secrets
sudo podman secret ls

# View a specific configuration
sudo podman secret inspect --showsecret foreman-settings-yaml
```

**Service configuration files:**
Configuration files are stored as podman secrets. To view:
```bash
# List all secrets
sudo podman secret ls

# View specific secret
sudo podman secret inspect --showsecret <secret-name>
```

---

## Upgrades

Foremanctl supports upgrading to newer versions of Foreman and its components.

### Upgrade Process

**Step 1: Stop Services**

Before upgrading, stop all Foreman services:

```bash
sudo systemctl stop foreman.target
```

**Step 2: Update Foremanctl Package**

```bash
sudo dnf upgrade foremanctl
```

**Step 3: Verify Image Versions** (if needed)

Check that the image versions in `/usr/share/foremanctl/src/vars/images.yml` match your target version.

**Step 4: Deploy Updated Containers**

Run deployment again (parameters are persisted from previous deployment):

```bash
sudo foremanctl deploy
```

This will:
- Pull new container images
- Update configurations
- Restart services with new versions

**Step 5: Clean Up Old Images** (optional)

```bash
sudo podman image prune --all
```

### Upgrade Notes

- **Parameter persistence**: Foremanctl remembers parameters from previous deployments
- **Downtime**: Plan for approximately 15-30 minutes of downtime
- **Database migrations**: Will run automatically during deployment
- **Testing**: Test upgrades in a development environment first

---

## Uninstallation

### Stop and Remove Services

**Step 1: Stop all services:**
```bash
sudo systemctl stop foreman.target
```

**Step 2: Disable services:**
```bash
sudo systemctl disable foreman.target
sudo systemctl disable foreman-*.service
```

**Step 3: Remove containers:**
```bash
sudo podman rm -f $(sudo podman ps -aq)
```

**Step 4: Remove container images:**
```bash
sudo podman rmi -f $(sudo podman images -q)
```

**Step 5: Remove secrets:**
```bash
# List secrets
sudo podman secret ls | grep foreman

# Remove all foreman-related secrets
sudo podman secret ls --format "{{.Name}}" | grep foreman | xargs -r sudo podman secret rm
```

**Step 6: Remove systemd files:**
```bash
sudo rm -rf /etc/containers/systemd/foreman*
sudo systemctl daemon-reload
```

**Step 7: Remove data directories** (WARNING: This deletes all data):
```bash
sudo rm -rf /var/lib/foreman
sudo rm -rf /var/lib/pulp
sudo rm -rf /var/lib/candlepin
sudo rm -rf /root/certificates
```

**Step 8: Uninstall package:**
```bash
sudo dnf remove foremanctl
```

### Data Backup Before Uninstallation

If you want to preserve data for later restoration:

```bash
# Backup databases (if using internal database)
sudo podman exec foreman-postgresql pg_dumpall -U postgres > /backup/foreman-db-backup.sql

# Backup Pulp content
sudo tar czf /backup/pulp-content.tar.gz /var/lib/pulp

# Backup certificates
sudo tar czf /backup/foreman-certs.tar.gz /root/certificates
```

---

## Additional Resources

### Documentation
- **Foreman Documentation**: https://theforeman.org/documentation.html
- **Katello Documentation**: https://theforeman.org/plugins/katello/
- **Podman Documentation**: https://docs.podman.io/

### Support
- **Issue Tracker**: https://github.com/theforeman/foremanctl/issues
- **Community Forums**: https://community.theforeman.org/
- **IRC**: #theforeman on Libera.Chat

### Development
- **Source Code**: https://github.com/theforeman/foremanctl
- **Contributing**: See DEVELOPMENT.md in the repository

---

## Quick Reference

### Essential Commands

```bash
# Deploy Foreman
sudo foremanctl deploy --foreman-initial-admin-password=changeme

# Check service status
sudo systemctl status foreman.target

# View logs
sudo journalctl -u foreman.service -f

# Stop all services
sudo systemctl stop foreman.target

# Start all services
sudo systemctl start foreman.target

# Restart all services
sudo systemctl restart foreman.target

# List running containers
sudo podman ps

# View configuration secrets
sudo podman secret ls

# Upgrade
sudo dnf upgrade foremanctl && sudo foremanctl deploy
```

### Default Locations

- **Logs**: `/var/lib/foremanctl/foremanctl.log` (deployment), `journalctl` (services)
- **Certificates**: `/root/certificates/`
- **Data**: `/var/lib/foreman`, `/var/lib/pulp`, `/var/lib/candlepin`
- **Systemd units**: `/etc/containers/systemd/`
- **Configuration**: Stored as Podman secrets

---

**Version**: Foremanctl for Foreman 3.18
**Last Updated**: 2026-03-23
