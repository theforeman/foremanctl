# Certificate Management

This document describes how certificate generation and management works in foremanctl.

## User Guide

### Certificate Sources

foremanctl supports two certificate sources that determine how certificates are obtained:

**Default Source (`certificate_source: default`)**
- Automatically generates self-signed certificates during deployment
- Creates a complete PKI infrastructure with CA, server, and client certificates
- Recommended for development and testing environments

**Installer Source (`certificate_source: installer`)**
- Uses existing certificates from a previous `foreman-installer` deployment
- Useful for migration scenarios where certificates already exist
- Certificate files must be present at expected foreman-installer paths

### Usage

#### Using Auto-Generated Certificates (Default)

```bash
# Deploy with auto-generated certificates
foremanctl deploy

# Explicitly specify default certificate source
foremanctl deploy --certificate-source=default
```

#### Using Existing Installer Certificates

```bash
# Use certificates from previous foreman-installer
foremanctl deploy --certificate-source=installer
```

### Certificate Locations

After deployment, certificates are available at:

**Default Source:**
- CA Certificate: `/var/lib/foremanctl/certificates/certs/ca.crt`
- Server Certificate: `/var/lib/foremanctl/certificates/certs/<hostname>.crt`
- Client Certificate: `/var/lib/foremanctl/certificates/certs/<hostname>-client.crt`

**Installer Source:**
- CA Certificate: `/root/ssl-build/katello-default-ca.crt`
- Server Certificate: `/root/ssl-build/<hostname>/<hostname>-apache.crt`
- Client Certificate: `/root/ssl-build/<hostname>/<hostname>-foreman-client.crt`

**Note for Rootless Deployments:**
- Default certificates are owned by `foremanctl:foremanctl` user and group
- Installer certificates remain in `/root/ssl-build/` with group ownership and permissions automatically configured during deployment to allow the `foremanctl` user to read them

### Current Limitations

- Only supports single hostname (no multiple DNS names)
- Cannot provide custom certificate files during deployment
- Fixed 20-year certificate validity period
- Limited certificate customization options

---

## Internal Design

### Architecture

The certificate system uses a modular Ansible role-based approach with clear separation between generation, validation, and usage phases.

#### Certificate Role Structure

```
src/roles/certificates/
├── tasks/
│   ├── main.yml          # Entry point - orchestrates CA and certificate generation
│   ├── ca.yml            # CA certificate generation
│   └── issue.yml         # Host certificate issuance
├── defaults/main.yml     # Default configuration variables
└── templates/
    ├── openssl.cnf.j2    # OpenSSL configuration template
    └── serial.j2         # Serial number template
```

#### Certificate Generation Workflow

1. **CA Generation** (when `certificates_ca: true`):
   - Install OpenSSL and create directory structure
   - Generate 4096-bit RSA private key
   - Create self-signed CA certificate (CN: "Foreman Self-signed CA", 20-year validity)

2. **Host Certificate Issuance** (for each hostname in `certificates_hostnames`):
   - Generate 4096-bit RSA private key
   - Create certificate signing request (CSR)
   - Sign certificate with CA (includes serverAuth/clientAuth extensions)
   - Generate both server and client certificates per hostname

#### Variable System

Certificate paths are defined in source-specific variable files:

**Default Source (`src/vars/default_certificates.yml`):**
```yaml
certificates_ca_directory: /var/lib/foremanctl/certificates
ca_certificate: "{{ certificates_ca_directory }}/certs/ca.crt"
server_certificate: "{{ certificates_ca_directory }}/certs/{{ ansible_facts['fqdn'] }}.crt"
client_certificate: "{{ certificates_ca_directory }}/certs/{{ ansible_facts['fqdn'] }}-client.crt"
```

**Installer Source (`src/vars/installer_certificates.yml`):**
```yaml
certificates_ca_directory: /root/ssl-build
ca_certificate: "{{ certificates_ca_directory }}/katello-default-ca.crt"
server_certificate: "{{ certificates_ca_directory }}/{{ ansible_facts['fqdn'] }}/{{ ansible_facts['fqdn'] }}-apache.crt"
client_certificate: "{{ certificates_ca_directory }}/{{ ansible_facts['fqdn'] }}/{{ ansible_facts['fqdn'] }}-foreman-client.crt"
```

#### Integration with Deployment

In `src/playbooks/deploy/deploy.yaml`:

1. **Variable Loading**: Loads certificate variables based on `certificate_source`
2. **Certificate Generation**: Runs `certificates` role when `certificate_source == 'default'`
3. **Certificate Validation**: Runs `certificate_checks` role for all sources
4. **Service Configuration**: Passes certificate paths to dependent roles

#### Validation System

The `certificate_checks` role uses `foreman-certificate-check` binary to validate:
- Certificate file existence and readability
- PEM format validation
- Private key and certificate pairing
- Certificate chain integrity

### Technical Specifications

**Certificate Properties:**
- Key Size: 4096-bit RSA
- Hash Algorithm: SHA256
- Validity Period: 7300 days (20 years)
- Extensions: serverAuth, clientAuth, nsSGC, msSGC

**Directory Structure:**
```
/var/lib/foremanctl/certificates/
├── certs/           # Public certificates
├── private/         # Private keys and passwords
└── requests/        # Certificate signing requests
```

All certificate files and directories are owned by `foremanctl:foremanctl` to support rootless Podman deployments.

**OpenSSL Configuration:**
- Custom configuration template supports SAN extensions
- Single DNS entry per certificate: `subjectAltName = DNS:{{ certificates_hostname }}`
- Uses OpenSSL's `req` and `ca` commands for generation and signing