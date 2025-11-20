hammer role
===========

Installs and configures [hammer](https://github.com/theforeman/hammer-cli) with plugins.

variables
---------
- `hammer_foreman_server_url`: The URL of the Foreman server to configure (default: `https://{{ ansible_facts['fqdn'] }}`)
- `hammer_ca_certificate`: The CA bundle to verify the connection to Foreman. By default this is empty and Hammer uses the system store. Alternatively you can use `hammer --fetch-ca-cert` to obtain the cert of the configured Foreman server.
- `hammer_packages`: Which plugin packages to install.
- `hammer_kerberos_auth_enabled`: Enable Kerberos/negotiate authentication for Hammer CLI (default: `false`). When enabled, Hammer will use session-based authentication with negotiate auth type, allowing users to authenticate using `kinit`.

usage inside foremanctl
-----------------------
When used as part of `foremanctl`, the variables are set up as following:
- `hammer_foreman_server_url`: The URL of the deployment
- `hammer_ca_certificate`: Set up to match the CA used by Foreman
- `hammer_packages`: Set up to match the plugins enabled in Foreman
