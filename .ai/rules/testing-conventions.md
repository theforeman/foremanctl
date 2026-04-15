---
name: testing-conventions
description: >-
  Testing conventions for pytest/testinfra tests in foremanctl. All agents
  writing or modifying tests must follow these rules.
applies-to:
  - tests/
references:
  - docs/developer/testing.md
---

# Rules - Testing Conventions

These rules apply to all test code in foremanctl.

## File Naming

- Integration test files: `tests/<component>_test.py` (e.g. `tests/postgresql_test.py`, `tests/foreman_api_test.py`)
- Unit test files: `tests/unit/<name>_test.py`
- The `_test.py` suffix is required for pytest discovery.

## Test Organization

| What you're testing | Where to put it |
|---------------------|-----------------|
| A new service (container or systemd unit) | `tests/<service>_test.py` |
| Foreman API behavior | `tests/foreman_api_test.py` |
| Client registration or content workflows | `tests/client_test.py` |
| CLI flags, playbooks, or feature management | `tests/features_test.py` or `tests/playbooks_test.py` |
| A standalone script (no deployment needed) | `tests/unit/<name>_test.py` |

## Fixture Usage

- ALWAYS check `tests/conftest.py` for existing fixtures before creating new ones.
- Use `server`, `client`, `database` fixtures for host access -- never create SSH connections manually.
- Use `foremanapi` for Foreman REST API operations.
- Use resource lifecycle fixtures (`organization`, `product`, `yum_repository`, etc.) for test data that needs setup and teardown.

## Test Patterns

- One concern per test function.
- Use `@pytest.mark.parametrize` when the same assertion applies to multiple inputs (e.g. multiple service instances).
- Test function names must be descriptive: `test_redis_service_running`, not `test_1`.
- Use `server.run()` for executing commands on VMs, not subprocess or os.system.

## Assertions

- Use plain `assert` statements (pytest-style), not `unittest` assertion methods.
- Include helpful assertion messages for non-obvious checks.
- For service tests, check both `is_running` and port reachability.

## Prerequisites

- Integration tests require a running deployment. Do NOT attempt to deploy from within tests.
- `.tmp/ssh-config` must exist before running integration tests.
- `playbooks_test.py` is the exception -- it runs without a deployment (metadata validation only).

## Do NOT

- Do not create mocks for infrastructure tests -- they run against real VMs.
- Do not hardcode hostnames -- use the `server_fqdn`, `client_fqdn` fixtures.
- Do not hardcode credentials -- use the `foremanapi` fixture which handles authentication.
- Do not import from production code (`src/`) in tests -- tests interact via SSH and API only.
