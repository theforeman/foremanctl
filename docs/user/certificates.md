# Certificate Management

This document describes how certificate generation and management works in foremanctl.

## User Guide

### How Certificates Work

foremanctl automatically manages certificates for all deployed services. On first deploy, it detects existing certificates or generates new ones:

1. Fresh install — If no installer certificates exist, a self-signed CA and certificates are generated automatically.
2. Existing foreman-installer certificates — If certificates from a previous `foreman-installer` deployment exist at `/root/ssl-build/`, they are automatically adopted and normalized into `/root/certificates/`. All certificates are copied and the original directory is backed up to `/root/ssl-build.bak/` so foremanctl can manage their full lifecycle going forward.

On subsequent deploys, existing certificates at `/root/certificates/` are reused and any new host certificates are issued as needed.

### Usage

#### Auto-Generated Certificates (Default)

```bash
# Deploy with auto-generated certificates
foremanctl deploy
```

No flags are needed — certificates are generated automatically on first deploy.

#### Upgrading from foreman-installer

```bash
# Just deploy — installer certificates at /root/ssl-build/ are auto-detected
foremanctl deploy
```

foremanctl detects the existing certificates, normalizes them into its canonical structure, and manages them going forward. The original CA is preserved so existing client trust is maintained. The original `/root/ssl-build/` directory is backed up to `/root/ssl-build.bak/`.

### CNAME Support

foremanctl supports Subject Alternative Names (SANs) for multi-domain certificates:

```bash
# Generate certificates with multiple DNS names
foremanctl deploy \
  --certificate-cname api.example.com \
  --certificate-cname foreman.example.com \
  --certificate-cname satellite.example.com
```

When CNAMEs are specified, certificates will include all names in the Subject Alternative Name field, allowing the same certificate to be valid for multiple hostnames.

If certificates already exist from a previous deployment, passing `--certificate-cname` will automatically regenerate the server certificate and CSR to include the new CNAMEs. Existing private keys are reused.

To remove all CNAMEs from an existing certificate, use `--reset-certificate-cname`.

On each run the role compares the Subject Alternative Names in the existing server certificate against the desired list (hostname + any `--certificate-cname` values). If they differ, the CSR and certificate are regenerated automatically. This means both adding and removing CNAMEs are handled transparently without manual cleanup.

### Certificate Locations

After deployment, certificates are at:

```
/root/certificates/
├── certs/
│   ├── ca.crt                 # CA certificate
│   ├── server-ca.crt          # Server CA certificate
│   ├── <hostname>.crt         # Server certificate
│   ├── <hostname>-client.crt  # Client certificate
│   └── localhost.crt          # Localhost certificate (for Candlepin)
├── private/
│   ├── ca.key                 # CA private key
│   ├── ca.pwd                 # CA key password
│   ├── <hostname>.key         # Server private key
│   ├── <hostname>-client.key  # Client private key
│   └── localhost.key          # Localhost private key
└── requests/                  # Certificate signing requests
```

## Internal Design

### Architecture

The certificate system uses a modular Ansible role-based approach with auto-detection, normalization, and clear separation between generation, validation, and usage phases.

#### Certificate Role Structure

```
src/roles/certificates/
├── tasks/
│   ├── main.yml               # Entry point — auto-detects source and dispatches
│   ├── setup.yml              # Shared directory/config setup
│   ├── ca.yml                 # CA certificate generation (fresh installs)
│   ├── issue.yml              # Host certificate issuance
│   └── normalize.yml          # Normalizes foreman-installer certs
└── defaults/main.yml          # Default configuration variables
```

#### Auto-Detection Workflow

1. **Check installer path**: If `/root/ssl-build/katello-default-ca.crt` exists, normalize installer certificates into the canonical structure.
2. **Fresh install**: If no installer certificates found, generate a new self-signed CA and certificates.
3. **Issue certificates**: For each hostname in `certificates_hostnames`, issue server and client certificates if they don't already exist.

#### Normalization

Installer certificates are copied from `/root/ssl-build/` into the canonical `/root/certificates/` structure. The original directory is backed up to `/root/ssl-build.bak/`. This means:
- Only one variable file (`src/vars/default_certificates.yml`) is needed
- All downstream roles (httpd, foreman, candlepin, etc.) use the same paths
- The `certificates` role always runs during deployment
- The CA key is preserved, enabling foremanctl to issue new certificates using the original CA

#### Variable System

Certificate paths are defined in `src/vars/default_certificates.yml`:

```yaml
ca_certificate: "{{ certificates_ca_directory }}/certs/ca.crt"
server_certificate: "{{ certificates_ca_directory }}/certs/{{ ansible_facts['fqdn'] }}.crt"
server_ca_certificate: "{{ certificates_ca_directory }}/certs/server-ca.crt"
client_certificate: "{{ certificates_ca_directory }}/certs/{{ ansible_facts['fqdn'] }}-client.crt"
```

#### Integration with Deployment

In `src/playbooks/deploy/deploy.yaml`:

1. **Variable Loading**: Loads `default_certificates.yml` (always the same paths)
2. **Certificate Management**: Runs `certificates` role (auto-detects, normalizes, and generates as needed)
3. **Certificate Validation**: Runs `certificate_checks` role
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
- Server extensions: serverAuth
- Client extensions: clientAuth

**Certificate Generation:**
- Uses `community.crypto` Ansible modules for all certificate operations
- SAN entries automatically derived from hostname and `certificates_cnames` variable
- CNAMEs configured via `certificates_cnames` variable (list of additional DNS names)
