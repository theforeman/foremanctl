# pulp_cli role

Installs the Pulp CLI RPM on the host and configures client-certificate
authentication for root-only troubleshooting.

## Variables

- `pulp_cli_url`: Pulp server URL (defaults to `https://{{ ansible_facts['fqdn'] }}`).
- `pulp_cli_client_certificate`: Required path to the existing client certificate.
- `pulp_cli_client_key`: Required path to the existing client private key.
- `pulp_cli_ca_certificate`: Optional path to the server CA bundle. When supplied,
  it is copied into the host trust store and `update-ca-trust extract` is run.
- `pulp_cli_packages`: RPM packages to install (defaults to `[pulp-cli]`).
- `pulp_cli_manage_repository`: Manage a temporary upstream repository (defaults
  to `true`). Set to `false` when the deployment repositories provide the CLI;
  the role then removes its repository file and installs from the normal repositories.
- `pulp_cli_repository_url`: Temporary repository URL. Defaults to the upstream
  pulpcore nightly repository for the host's EL major version and architecture.

The temporary repository is disabled by default and enabled only for the CLI
installation transaction. GPG checking is disabled for this temporary repository
because its advertised signing-key URL currently returns HTTP 404. This does not
change GPG checking for other repositories. Remove this temporary source once the
supported deployment repositories provide the CLI and its dependencies.

## Configuration

Foremanctl supplies the deployment URL and existing certificate paths through
`src/vars/base.yaml`. The role manages `/etc/pulp/cli.toml` with TLS verification
enabled. No private keys are copied, and their root-only permissions are preserved.

Root can add persistent overrides in `/root/.config/pulp/cli.toml`. This file is
not managed by the role, so local customization survives subsequent deployments.

See [Pulp CLI troubleshooting](../../../docs/user/troubleshooting.md#pulp-cli)
for usage and security considerations.
