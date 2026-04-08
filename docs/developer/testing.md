# Testing

This guide covers the test infrastructure, how to run tests, and how to write new ones.

## Overview

Tests live under `tests/` and use [pytest](https://pytest.org/) with [testinfra](https://testinfra.readthedocs.io/). Most tests are integration tests that SSH into deployed VMs and assert against real services.

## Test infrastructure

### Machines

Integration tests run against Vagrant VMs defined in the [`Vagrantfile`](../../Vagrantfile):

| VM | Hostname | Purpose |
| --- | --- | --- |
| `quadlet` | `quadlet.example.com` | Foreman server — containers, quadlets, all services |
| `client` | `client.example.com` | Client-side tests — Host registration, REX |
| `database` | `database.example.com` | Used for testing external postgreSQL |

### How tests connect

`./forge test` runs the [`development/playbooks/test/test.yaml`](../../development/playbooks/test/test.yaml) playbook, which:

1. Installs test dependencies on `quadlet` (e.g. `nmap`).
2. Generates `.tmp/ssh-config` from the Ansible inventory — one SSH host block per VM.
3. Runs `pytest` from the repository root.

Testinfra fixtures in `tests/conftest.py` open Paramiko sessions through that SSH config, so `server`, `client`, and `database` are live hosts, not local stubs.

### CI

GitHub Actions mirrors the same workflow: start VMs, deploy, run tests. The [`.github/workflows/test.yml`](../../.github/workflows/test.yml) matrix covers combinations of certificate source, database mode, security profile, and base box.

## Running tests

A working deployment is required before running tests.

```bash
./forge test
```

Run a specific file or test:

```bash
pytest tests/postgresql_test.py
pytest tests/foreman_test.py::test_foreman_service
```

> [!NOTE]
> Running `pytest` directly requires `.tmp/ssh-config` to exist. Run `./forge test` at least once to generate it.

Pass options to match your deployment:

```bash
./forge test --pytest-args="--certificate-source=installer --database-mode=external"

# or directly:
pytest tests/ --database-mode=external
pytest tests/ --certificate-source=installer
```

> [!NOTE]
> `./forge test` runs the full suite. Tests that depend on optional features (e.g. hammer) will fail unless those features are deployed.

### Smoker

`./forge smoker` runs the [forklift smoker](https://github.com/theforeman/forklift) role against the Foreman HTTPS endpoint. It is a separate browser-based smoke test, not part of the pytest suite.

## Fixtures

All shared fixtures are defined in `tests/conftest.py`.

### Hosts

| Fixture | Description |
| --- | --- |
| `server` | Testinfra host for the Foreman server (`quadlet`) |
| `client` | Testinfra host for the client VM |
| `database` | Testinfra host for the database — same as `server` when `database_mode=internal` |

### API

| Fixture | Description |
| --- | --- |
| `foremanapi` | Authenticated [Apypie](https://github.com/Apipie/apypie) client (`admin` / `changeme`) |

### Resource lifecycle

These fixtures create a resource before the test and delete it afterward:

| Fixture | Resource |
| --- | --- |
| `organization` | Foreman organization |
| `product` | Katello product |
| `yum_repository` | Synced YUM repository |
| `file_repository` | Synced file repository |
| `container_repository` | Synced container repository |
| `lifecycle_environment` | Katello lifecycle environment |
| `content_view` | Katello content view |
| `activation_key` | Activation key |
| `client_environment` | Full client setup (activation key + content view + synced repo) |

### Helpers

| Fixture | Description |
| --- | --- |
| `server_fqdn` / `client_fqdn` | `quadlet.example.com` / `client.example.com` |
| `certificates` | Certificate paths (varies by `--certificate-source`) |
| `ssh_config` | Parsed SSH config for the server |
| `fixture_dir` | Path to `tests/fixtures/` |

## Writing tests

### Service test

Check that a systemd unit is running and its port is reachable:

For example:

```python
def test_service_running(server):
    assert server.service("redis").is_running


def test_service_port(server):
    assert server.addr("localhost").port(6379).is_reachable
```

### API test

The `foremanapi` fixture is an [apypie](https://github.com/Apipie/apypie) `ForemanApi` client that connects to the deployed Foreman instance(authenticated as `admin`/`changeme`). It maps directly to the Foreman REST API — each method takes a resource name that corresponds to an API endpoint:

Here are few examples:
A typical test that reads a setting:

```python
def test_delivery_method_setting(foremanapi):
    settings = foremanapi.list("settings", search="name=delivery_method")
    assert settings[0]["value"] == "smtp"
```

A test that triggers a sync and verifies content was published:

```python
def test_yum_repository(yum_repository, foremanapi, ssh_config):
    foremanapi.resource_action("repositories", "sync", {"id": yum_repository["id"]})
    repo_url = _repo_url(yum_repository, ssh_config)
    assert requests.get(f"{repo_url}/Packages/b/bear-4.1-1.noarch.rpm", verify=False)
```

### Resource lifecycle test

Resource fixtures (`organization`, `product`, `yum_repository`, etc.) call `foremanapi.create()` in setup and `foremanapi.delete()` in teardown, so your test only needs to use them:

```python
def test_organization(organization):
    assert organization
```

### Running commands on a host

Use `server.run()` or `database.run()` to execute shell commands on the VM:

```python
def test_postgresql_databases(database):
    result = database.run("podman exec postgresql psql -U postgres -c '\\l'")
    assert "foreman" in result.stdout
```

### Parametrized tests

Use `@pytest.mark.parametrize` when the same assertion applies to multiple inputs:

```python
@pytest.mark.parametrize("instance", ["orchestrator", "worker", "worker-hosts-queue"])
def test_dynflow_service_instances(server, instance):
    assert server.service(f"dynflow-sidekiq@{instance}").is_running
```

## Where to add new tests

| What you're testing | File |
| --- | --- |
| A new service (container or systemd unit) | `tests/<service>_test.py` |
| Foreman API behavior | `tests/foreman_api_test.py` (or a new file for larger areas) |
| Client registration or content workflows | `tests/client_test.py` |
| CLI flags, playbooks, or feature management | `tests/features_test.py` or `tests/playbooks_test.py` |
| A standalone script (no deployment needed) | `tests/unit/<name>_test.py` |

When adding a new file, follow the conventions of the nearest existing test file.
