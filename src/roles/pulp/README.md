Pulp Role
=========

Deploys and manages [Pulp](https://pulpproject.org/) as Podman quadlets.

Variables
---------
- `pulp_container_image`: Container image to use for Pulp (default: `quay.io/foreman/pulp`)
- `pulp_container_tag`: Container image tag (default: `"3.73"`)
- `pulp_registry_auth_file`: Path to the registry authentication file (default: `/etc/foreman/registry-auth.json`)
- `pulp_worker_count`: Number of Pulp workers (default: min of 8 or CPU count)
- `pulp_content_origin`: URL for the Pulp content service (default: `http://{{ fqdn }}:24816`)
- `pulp_pulp_url`: URL for the Pulp API service (default: `http://{{ fqdn }}:24817`)
- `pulp_cli_package`: Package providing the Pulp CLI (default: `python3.12-pulp-cli`)
- `pulp_cli_base_url`: Pulp API URL used by the CLI (default: `https://{{ fqdn }}`)
- `pulp_cli_ca_certificate`: CA bundle trusted by the CLI (default: `pulp_foreman_ca_certificate`)
- `pulp_cli_client_certificate`: Client certificate used by the CLI (default: `client_certificate`)
- `pulp_cli_client_key`: Client key used by the CLI (default: `client_key`)
- `pulp_volumes`: Volume mounts for Pulp containers (default: `/var/lib/pulp:/var/lib/pulp`)
- `pulp_enable_analytics`: Enable Pulp analytics (default: `false`)
- `pulp_import_paths`: Paths Pulp can use for content imports (default: `[/var/lib/pulp/sync_imports, /var/lib/pulp/imports]`)
- `pulp_export_paths`: Paths Pulp can use for content exports (default: `[/var/lib/pulp/exports]`)
- `pulp_plugins`: Additional Pulp plugins to enable (default: `[pulp_container, pulp_rpm]`)
- `pulp_database_name`: Name of the Pulp database (default: `pulp`)
- `pulp_database_user`: Database user (default: `pulp`)
- `pulp_database_host`: Database host (default: `postgresql` on `foreman-core-network`; overridden by `database_host` in deploy playbooks)
- `pulp_database_port`: Database port (default: `5432`)
- `pulp_database_password`: Database password (required, no default)
- `pulp_database_ssl_mode`: Database SSL mode (default: `disabled`)
- `pulp_database_ssl_ca`: Path to the database SSL CA certificate on the control node (default: empty)

Usage Inside foremanctl
-----------------------
When used as part of `foremanctl`, the variables are setup as the following
- `pulp_worker_count`: `--pulp-worker-count`
- `pulp_log_level`: `--pulp-log-level`
- `pulp_import_paths`: `--content-import-path` (may be specified multiple times)
- `pulp_export_paths`: `--content-export-path` (may be specified multiple times)
