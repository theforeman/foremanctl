---
name: certificate-management
description: >-
  Certificate management in foremanctl: sources, configuration, roles,
  and the relationship between certificate options and deployment behavior.
technologies:
  - openssl
  - ansible
references:
  - docs/certificates.md
  - docs/user/certificates.md
---

# Skill - Certificate Management in foremanctl

foremanctl manages TLS certificates for secure communication between Foreman ecosystem components. Certificates are a critical part of deployment and are configured through the `certificate_source` parameter.

## Certificate Sources

The `--certificate-source` flag (defined in the `_certificate_source` metadata fragment) controls how certificates are provisioned:

### `default`

Self-signed certificates generated during deployment. Suitable for development and testing.

- Certificates are generated using the `community.crypto` Ansible collection.
- A self-signed CA is created, and service certificates are signed by it.
- Configuration in `src/vars/default_certificates.yml`.

### `installer`

Externally provided certificates, typically from an enterprise CA. Required for production.

- The user provides CA certificate, server certificate, and private key.
- foremanctl validates the certificates before use.
- Configuration in `src/vars/installer_certificates.yml`.

## Certificate-Related Roles

### `certificates`

The main certificate management role under `src/roles/certificates/`. Handles:

- CA certificate generation or import
- Service certificate creation
- Certificate distribution to services
- Certificate validation

### `certificate_checks`

Validation role under `src/roles/certificate_checks/`. Includes:

- `files/foreman-certificate-check` -- script for validating certificate chains, expiry, and key matching

## Subject Alternative Names (SANs)

Additional DNS names can be included in certificates via the `--certificate-cname` flag:

```bash
./foremanctl deploy --certificate-cname proxy.example.com --certificate-cname alt.example.com
```

Defined in the deploy metadata as:

```yaml
certificates_cnames:
  help: Additional DNS name to include in Subject Alternative Names for certificates. Can be specified multiple times.
  action: append_unique
  type: FQDN
  parameter: --certificate-cname
```

## Testing Certificates

### Test Fixtures

Certificate test fixtures live in `tests/fixtures/foreman-certificate-check/`:

- `create_cert.sh` -- script to generate test certificates
- `extensions.txt` -- certificate extension configuration
- `certs/` -- sample certificates, keys, and CSRs for testing

### Test File

`tests/certificates_test.py` validates certificate behavior with different sources.

### Running Certificate Tests

```bash
# Test with default certificates
pytest tests/certificates_test.py

# Test with installer certificates
pytest tests/certificates_test.py --certificate-source=installer
```

## Certificate Flow

1. **Deployment starts** -- `certificate_source` parameter is read from CLI or answers file.
2. **Certificate role runs** -- generates or imports certificates based on source.
3. **Certificate checks run** -- validates the certificate chain, expiry, and key matching.
4. **Services receive certificates** -- distributed via Podman secrets to containers that need TLS.
5. **HTTPD configured** -- Apache reverse proxy is configured with the server certificate for TLS termination.

## Related Metadata Fragments

- `_certificate_source` -- defines the `certificate_source` variable with choices `[default, installer]`
- Included by the `deploy` playbook via `include: [_certificate_source]`
