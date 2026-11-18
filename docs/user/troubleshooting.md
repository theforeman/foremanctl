# Troubleshooting

## Pulp CLI

The optional `pulp-cli` feature installs the `pulp` command directly on the host.
It is enabled by default in the Satellite flavor. For other server deployments:

```console
./foremanctl deploy --add-feature pulp-cli
```

The feature requires Pulp and automatically enables that dependency. The CLI is
intended for troubleshooting; prefer Hammer or the Foreman API for normal content
management. Direct modifications through Pulp can leave Foreman and Pulp out of sync.

### Usage

The CLI is intended for root-only troubleshooting. Run these commands as root
on the deployed server:

```console
pulp status
pulp rpm repository list --limit 10
pulp task list --limit 10
```

The CLI uses the deployment's existing client certificate and private key.
Foremanctl keeps the key's root-only permissions, trusts the server CA in the host
trust store, and enables TLS verification.

### Configuration and root overrides

Foremanctl manages `/etc/pulp/cli.toml` on the host:

```toml
[cli]
base_url = "https://satellite.example.com"
cert = "/var/lib/foremanctl/certs/certs/satellite.example.com-client.crt"
key = "/var/lib/foremanctl/certs/private/satellite.example.com-client.key"
verify_ssl = true
```

Foremanctl replaces this file during deployment. To preserve local customization,
root can add overrides in `/root/.config/pulp/cli.toml`, which foremanctl does not
manage.

For example, this changes only the output format and preserves the generated
connection and authentication settings:

```toml
[cli]
format = "yaml"
```

Command-line options take precedence over configuration files:

```console
pulp --format json status
```

### Package source

For now, foremanctl creates a temporary `foremanctl-pulp-cli` DNF repository using
`https://yum.theforeman.org/pulpcore/nightly/el<major-version>/$basearch/`.
The repository is disabled by default and enabled only during CLI installation,
so routine host updates do not use it. The installation transaction can also
install required CLI dependencies from this repository.

This is a temporary nightly package source with GPG checking disabled because a
usable signing key is not published at the repository's advertised key URL.
Connected deployments need access to this URL; disconnected deployments must
make the CLI and its dependencies available through a local mirror instead.
The role's `pulp_cli_manage_repository` and `pulp_cli_repository_url` variables
control this temporary source. Once the CLI and its dependencies are available
in the normal Satellite repositories, the temporary source can be removed.

### Connection problems

- Check the generated URL and certificate paths in `/etc/pulp/cli.toml`.
- Check `/root/.config/pulp/cli.toml` if the CLI connects to an unexpected server.
- Confirm the client certificate and key exist and are accessible to root.
- For TLS failures, check the server certificate and CA chain. Foremanctl installs
  the server CA at `/etc/pki/ca-trust/source/anchors/foremanctl-pulp-cli.crt` and
  refreshes the host trust store. Do not work around certificate failures by
  disabling verification.
