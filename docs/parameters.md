# Installation Parameters

This document covers installation parameters as presented to users, and includes how the puppet-based `foreman-installer` parameters will map to new parameters.

## Design Principles

* Using a single parameter when there are multiple variables that should have the same value
* Aim for minimal configuration values for the user

## Mapping

Parameters are split into either mapped or unmapped groupings per category.

Mapped: Parameters the new installer will have and are mapped to a parameter from the `foreman-installer`.
Unmapped: Parameters from `foreman-installer` that appear in the official [foreman-documentation](https://github.com/theforeman/foreman-documentation) that are unmapped into the new installer.

### Foreman

These are parameters that are related to the install and operation of the Foreman server and plugins.

#### Database

There are multiple use cases from the users perspective that dictate what parameters need to be available for user input.

 * The user has deployed an external database and needs to specify connection details such as host and port.
 * The user wishes to manage passwords externally to the installer and needs to specify rather than use the default randomly generated password.
 * The user has deployed an external database configured with TLS and needs to specify the CA certificate.
 * The user has to customize the database name and user connecting to each of the databases.
 * The user is encountering database pool exhaustion errors and needs to tune the value.

##### Mapped

| Parameter | Description | foreman-installer Parameters |
| ----------| ----------- | ---------------------------- |
| `--database-mode` | Denotes if the database is internally or externally managed | `--foreman-db-manage`<br/> `--katello-candlepin-db-manage`<br/> `--foreman-proxy-content-pulpcore-manage-postgresql` |
| `--database-host` | Location to connect to the database | `--foreman-db-host`<br/> `--katello-candlepin-db-host`<br/> `--foreman-proxy-content-pulpcore-postgresql-host` |
| `--database-port` | Port to connect to the database | `--foreman-db-port`<br/> `--katello-candlepin-db-port`<br/> `--foreman-proxy-content-pulpcore-postgresql-port` |
| `--database-ssl-mode` | SSL verification mode to use | `--foreman-db-sslmode` <br/> `--katello-candlepin-db-ssl-verify` <br/> `--katello-candlepin-db-ssl` <br/> `--foreman-proxy-content-pulpcore-postgresql-ssl`|
| `--database-ssl-ca` | Path to the database CA certificate | `--foreman-db-root-cert` <br/> `--katello-candlepin-db-ssl-ca` <br/> `--foreman-proxy-content-pulpcore-db-ssl-root-ca` |
| `--foreman-database-name` | Name of the Foreman database | `--foreman-db-database` |
| `--foreman-database-user` | Owner of the Foreman database | `--foreman-db-username` |
| `--foreman-database-password` | Password for Foreman database | `--foreman-db-password` |
| `--foreman-database-pool` | Tunes the database pool for Foreman | `--foreman-db-pool` |
| `--candlepin-database-name` | Name of the Candlepin database | `--katello-candlepin-db-name` |
| `--candlepin-database-user` | Owner of the Candlepin database | `--katello-candlepin-db-user` |
| `--candlepin-database-password` | Password for Candlepin database | `--katello-candlepin-db-password` |
| `--pulp-database-name` | Name of the Pulp database | `--foreman-proxy-content-pulpcore-postgresql-db-name` |
| `--pulp-database-user` | Owner of the Pulp database | `--foreman-proxy-content-pulpcore-postgresql-user` |
| `--pulp-database-password` | Password for Pulp database | `--foreman-proxy-content-pulpcore-postgresql-password` |
| `--foreman-initial-admin-username` | Initial username for the admin user | `--foreman-initial-admin-username` |
| `--foreman-initial-admin-password` | Initial password for the admin user | `--foreman-initial-admin-password` |
| `--foreman-puma-workers` | Number of workers for Puma | `--foreman-foreman-service-puma-workers` |
| `--pulp-worker-count` | Number of pulp workers | `--foreman-proxy-content-pulpcore-worker-count` |
| `--tuning` | Sets the tuning profile | `--tuning` |
| `--external-authentication={ipa,ipa_with_api}` | Enable configuration for external authentication via IPA for web UI (or webUI and API for `ipa_with_api`), expects the target machine to [be enrolled into FreeIPA/IDM](https://docs.theforeman.org/3.16/Configuring_User_Authentication/index-katello.html#enrolling-foreman-server-in-freeipa-domain) | `--foreman-ipa-authentication`<br/> `--foreman-ipa-authentication-api` |
| `--external-authentication-pam-service` | PAM service used for host-based access control in IPA | `--foreman-pam-service` |

#### Certs

##### Mapped

| Parameter | Description | foreman-installer Parameter |
| ----------| ----------- | --------------------------- |
| `--certificate-cname` | Allows defining CNAME for default certificates | --certs-cname |

##### Unmapped

| foreman-installer Parameter | Description | Reason |
| --------------------------- | ----------- | ------ |

#### Undetermined

| foreman-installer Parameter | Description | Module | Puppet Parameter | Keep |
| ------------------- | ----------- | ------ | ---------------- |-------------------|
| `--foreman-foreman-service-puma-threads-min` | | foreman | foreman_service_puma_threads_min | `--foreman-puma-threads-min` |
| `--foreman-foreman-service-puma-threads-max` | | foreman | foreman_service_puma_threads_max | `--foreman-puma-threads-max` |
| `--foreman-dynflow-worker-instances` | | foreman | dynflow_worker_instances |
| `--foreman-dynflow-worker-concurrency` | | foreman | dynflow_worker_concurrency |
| `--foreman-loggers` | | foreman | loggers |
| `--foreman-plugin-tasks-cron-line` | | foreman::plugin::tasks | cron_line |
| `--foreman-plugin-tasks-automatic-cleanup` | | foreman::plugin::tasks | automatic_cleanup |
| `--tuning` | Sets the tuning profile | foreman-installer | |
| `--certs-cname` | | certs | cname |
| `--certs-tar` | | certs | tar |
| `--certs-tar-file` | | certs | tar |
| `--certs-server-cert` | | certs | server_cert |
| `--certs-server-key` | | certs | server_key |
| `--certs-server-ca-cert` | | certs | server_ca_cert |
| `--certs-update-server` | Parameter to mark server certs for update | foreman-installer | No |
| `--certs-reset` | Parameter to reset all certificates to default | foreman-installer | No |
| `--foreman-initial-location` | | |
| `--foreman-initial-organization` | | |
| `--foreman-keycloak` | | |
| `--foreman-keycloak-app-name` | | |
| `--foreman-keycloak-realm` | | |
| `--foreman-logging-layout` | | |
| `--foreman-logging-level` | | |
| `--foreman-logging-type` | | |
| `--foreman-oauth-map-users` | | |
| `--foreman-plugin-remote-execution-cockpit-ensure` | | |
| `--foreman-telemetry-prometheus-enabled` | | |
| `--foreman-trusted-proxies` | | |


## Smart Proxy

### Undetermined

| Installer Parameter | Description | Module | Puppet Parameter |
| ------------------- | ----------- | ------ | ---------------- |
| `--foreman-proxy-cname` | Enables DHCP feature in smart-proxy | foreman_proxy | cname |
| `--foreman-proxy-fqdn` | Enables DHCP feature in smart-proxy | foreman_proxy | fqdn |
| `--foreman-proxy-foreman-base-url` | | foreman_proxy | foreman_base_url |
| `--foreman-proxy-oauth-consumer-key` | | foreman_proxy | oauth_consumer_key |
| `--foreman-proxy-oauth-consumer-secret` | | foreman_proxy | oauth_consumer_secret |
| `--foreman-proxy-register-in-foreman` | | foreman_proxy | register_in_foreman |
| `--foreman-proxy-trusted-hosts` | | foreman_proxy | trusted_hosts |
| `--foreman-proxy-dhcp` | Enables DHCP feature in smart-proxy | foreman_proxy | dhcp |
| `--foreman-proxy-dhcp-provider` | | foreman_proxy | dhcp_provider |
| `--foreman-proxy-dhcp-subnets` | | foreman_proxy | dhcp_subnets |
| `--foreman-proxy-dhcp-key-name` | | foreman_proxy | dhcp_key_name |
| `--foreman-proxy-dhcp-key-secret` | | foreman_proxy | dhcp_key_secret |
| `--foreman-proxy-dhcp-ipxefilename` | | foreman_proxy | dhcp_ipxefilename |
| `--foreman-proxy-dhcp-ipxe-bootstrap` | | foreman_proxy | dhcp_ipxe_bootstrap |
| `--foreman-proxy-dhcp-server` | | foreman_proxy | dhcp_server |
| `--foreman-proxy-libvirt-network` | | foreman_proxy | libvirt_network |
| `--foreman-proxy-libvirt-url` | | foreman_proxy | libvirt_url |
| `--foreman-proxy-dns` | | foreman_proxy | dns |
| `--foreman-proxy-dns-managed` | | foreman_proxy | dns_managed |
| `--foreman-proxy-dns-provider` | | foreman_proxy | foreman_proxy::dns_provider |
| `--foreman-proxy-dns-server` | | foreman_proxy | foreman_proxy::dns_server |
| `--foreman-proxy-keyfile` | | foreman_proxy | foreman_proxy::keyfile |
| `--foreman-proxy-plugin-dns-powerdns-rest-api-key` | | foreman_proxy::plugin::dns_powerdns | rest_api_key |
| `--foreman-proxy-plugin-dns-powerdns-rest-url` | | foreman_proxy::plugin::dns_powerdns | rest_url |
| `--foreman-proxy-plugin-dns-route53-aws-access-key` | | foreman_proxy::plugin::dns_route53 | aws_access_key |
| `--foreman-proxy-plugin-dns-route53-aws-secret-key` | | foreman_proxy::plugin::dns_route53 | aws_secret_key |
| `--foreman-proxy-httpboot` | | foreman_proxy | httpboot |
| `--foreman-proxy-tftp` | | foreman_proxy | tftp |
| `--foreman-proxy-tftp-servername` | | foreman_proxy | tftp_servername |
| `--foreman-proxy-tftp-managed` | | foreman_proxy | tftp_managed |
| `--foreman-proxy-tftp-root` | | foreman_proxy | tftp_root |
| `--foreman-proxy-plugin-dhcp-remote-isc-dhcp-config` | | foreman_proxy::plugin::dhcp_remote_isc | config |
| `--foreman-proxy-plugin-dhcp-remote-isc-dhcp-leases` | | foreman_proxy::plugin::dhcp_remote_isc | dhcp_config |
| `--foreman-proxy-plugin-dhcp-remote-isc-key-name` | | foreman_proxy::plugin::dhcp_remote_isc | key_name |
| `--foreman-proxy-plugin-dhcp-remote-isc-key-secret` | | foreman_proxy::plugin::dhcp_remote_isc | key_secret |
| `--foreman-proxy-plugin-dhcp-remote-isc-omapi-port` | | foreman_proxy::plugin::dhcp_remote_isc | omapi_port |
| `--foreman-proxy-plugin-remote-execution-script-mqtt-rate-limit` | | foreman_proxy::plugin::remote_execution_script | mqtt_rate_limit |
| `--foreman-proxy-plugin-remote-execution-script-mqtt-resend-interval` | | foreman_proxy::plugin::remote_execution_script | mqtt_resend_interval |
| `--foreman-proxy-plugin-remote-execution-script-mqtt-ttl` | | foreman_proxy::plugin::remote_execution_script | ttl |
| `--foreman-proxy-plugin-remote-execution-script-remote-working-dir` | | foreman_proxy::plugin::remote_execution_script | remote_working_dir |
| `--foreman-proxy-puppet` | | foreman_proxy | puppet |
| `--foreman-proxy-puppetca` | | foreman_proxy | puppetca |
| `--foreman-proxy-plugin-remote-execution-script-mode` | | foreman_proxy::plugin::remote_execution_script | mode |
| `--foreman-proxy-plugin-openscap-ansible-module` | | foreman_proxy::plugin::openscap | ansible_module |
| `--foreman-proxy-plugin-openscap-puppet-module` | | foreman_proxy::plugin::openscap | puppet_module |
| `--foreman-proxy-bmc` | | | |
| `--foreman-proxy-bmc-default-provider` | | | |
| `--foreman-proxy-content-enable-ostree` | | | |
| `--foreman-proxy-content-pulpcore-additional-import-paths` | | | |
| `--foreman-proxy-http` | | | |
| `--foreman-proxy-log` | | | |
| `--foreman-proxy-log-level` | | | |
| `--foreman-proxy-plugin-ansible-working-dir` | | | |
| `--foreman-proxy-plugin-dhcp-infoblox-dns-view` | | | |
| `--foreman-proxy-plugin-dhcp-infoblox-network-view` | | | |
| `--foreman-proxy-plugin-dhcp-infoblox-password` | | | |
| `--foreman-proxy-plugin-dhcp-infoblox-record-type` | | | |
| `--foreman-proxy-plugin-dhcp-infoblox-username` | | | |
| `--foreman-proxy-plugin-discovery-install-images` | | | |
| `--foreman-proxy-plugin-discovery-source-url` | | | |
| `--foreman-proxy-plugin-dns-infoblox-dns-server` | | | |
| `--foreman-proxy-plugin-dns-infoblox-dns-view` | | | |
| `--foreman-proxy-plugin-dns-infoblox-password` | | | |
| `--foreman-proxy-plugin-dns-infoblox-username` | | | |
| `--foreman-proxy-plugin-remote-execution-script-cockpit-integration` | | | |
| `--foreman-proxy-plugin-remote-execution-script-ssh-kerberos-auth` | | | |
| `--foreman-proxy-realm` | | | |
| `--foreman-proxy-realm-keytab` | | | |
| `--foreman-proxy-realm-principal` | | | |
| `--foreman-proxy-realm-provider` | | | |
| `--foreman-proxy-registration` | | | |
| `--foreman-proxy-registration-url` | | | |
| `--foreman-proxy-templates` | | | |
| `--foreman-proxy-template-url` | | | |
| `--puppet-server` | | puppet | server |
| `--puppet-server-ca` | | puppet | server_ca |
| `--puppet-dns-alt-names` | | puppet | dns_alt_names |
| `--puppet-ca-server` | | puppet | ca_server |
