# Checks
Foremanctl contains several "check_*" roles which are used to assist playbooks in confirming the Foreman server is configured properly. Each check is implemented as an independent Ansible role, allowing playbooks to run specific checks or groups of checks as needed.

Please update this file as check usage evolves.

## Check Descriptions
### check_database_connection
- **Description**: Validates PostgreSQL connectivity for external Foreman and Candlepin databases using configured credentials and SSL settings.
- **Fail state**: Fails if database connection cannot be established.
- **Rationale**: Database access is required for many foremanctl operations; external databases must be reachable using the provided credentials.

### check_duplicate_permissions
- **Description**: Queries the Foreman database for duplicate entries in the permissions table.
- **Fail state**: Fails if duplicate permissions are detected.
- **Rationale**: A validation was incorrectly removed which prevented users from creating duplicate Foreman permissions, causing upgrade failure. This check will need to be included until https://projects.theforeman.org/issues/38465 is addressed.

### check_features
- **Description**: Ensures that all foremanctl features requested (via the `--feature` flag) are valid.
- **Fail state**: Fails when requested features are not recognized by foremanctl.
- **Rationale**: This check handles input sanitization for `--feature`.

### check_foreman_api
- **Description**: Pings Foreman API (/api/v2/ping) to verify it responds. Verifies foreman_tasks service status is 'ok' when Katello/content feature is enabled.
- **Fail state**: Fails if ping fails or service status is not 'ok'.
- **Rationale**: An API connection is necessary for most Foreman operations. This check ensures there are no firewall or address issues.

### check_foreman_tasks
- **Description**: Queries Foreman tasks for paused, errored tasks.
- **Fail state**: Fails if any errored tasks are found.
- **Rationale**: Errored Foreman tasks indicate issues which need to be addressed by the user. This can be anything from a typo to systemic issues. Consulting https://community.theforeman.org may provide insight.
- **Skipping**: This role can be skipped in `foremanctl health` by passing the `--skip-check-foreman-tasks` flag. Use only for operations where a failed Foreman task is expected or unavoidable.

### check_host_facts_count
- **Description**: Ensures all hosts' facts counts are below a maximum threshold.
- **Fail state**: Fails if facts count exceeds threshold for any host.
- **Rationale**: Very high host facts count causes slow facts processing. See: https://access.redhat.com/solutions/4163891 for more information.

### check_hostname
- **Description**: Validates FQDN is not 'localhost' or 'localhost.localdomain', contains at least one dot, and has no underscores.
- **Fail state**: Fails if FQDN conditions are not met.
- **Rationale**: Foreman requires a properly-configured server FQDN. This check ensures server hostname was modified from the default and approximates a valid FQDN.

### check_podman_network_backend
- **Description**: Verifies the Podman network backend is `netavark`.
- **Fail state**: Fails if the network backend is anything other than `netavark`.
- **Rationale**: Foremanctl requires netavark as the Podman network backend. Using a different backend such as CNI can cause container networking failures. This is a documented installation prerequisite.

### check_services
- **Description**: Reports the status of all non-recurring services in the foreman.target systemd dependency tree.
- **Fail state**: Fails if any services are inactive.
- **Rationale**: Failed or stalled foreman services indicate an issue with the server. The user should check Foreman logs to find and address the problem. Inactive foreman services may indicate a systemctl configuration problem.

### check_subuid_subgid
- **Description**: Verifies `/etc/subuid` and `/etc/subgid` have entries for the current user, which is required for rootless Podman on the Foreman server.
- **Fail state**: Fails if these conditions are not met.
- **Rationale**: Any Podman container operation run from a non-privileged user (pull, run, secret management) requires configuring subordinate user and group IDs. This check is unused at the moment but supports future work setting up Podman under a non-root user.

### check_system_requirements
- **Description**: This check validates the Foreman system meets minimum hardware requirements determined by the user's tuning profile.
- **Fail state**: Fails if these conditions are not met or if the tuning profile cannot be loaded.
- **Rationale**: A system which does not meet minimum hardware specs may stall or fail due to Foreman resource usage.

## Skipping checks

Users may wish to skip certain checks on some playbooks, usually to work around a known issue on particularly sensitive checks. For example `health.yaml` (`foremanctl health`) includes a pattern for skipping `check_foreman_tasks`, as errored Foreman tasks which have not yet been cleared will fail the playbook.

When allowing the user to skip a check, ensure it provides tangible value greater than the consequences of user misuse. For example, allowing the user to skip `check_system_requirements` might seem harmless, but could likely lead to situations in which usage of the parameter becomes a silent default; changes in Foreman minimum system requirements would not be enforced. Be sure to document why a skip is required in the check descriptions section above.

Add skip parameters following this template:
```
<playbook_name>_skip_<check_role_name>_param:
  help: |
    Identify the purpose of the skipped check.
    Inform the user how to repair Foreman to pass this check (or point them in the right direction).
    Indicate why the user would need this check and warn against overuse.
  parameter: --skip-<check-role-name>
  action: store_true
  persist: false
```
