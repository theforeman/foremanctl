---
name: run-tests
description: >-
  Workflow for running the foremanctl test suite. Checks prerequisites,
  executes tests, and interprets output.
argument-hint: "[test-file-or-pattern] [--database-mode=MODE] [--certificate-source=SOURCE]"
references:
  - docs/developer/testing.md
  - tests/conftest.py
---

# Commands - Run Tests

Run the foremanctl test suite against a deployed environment.

## Input

`$ARGUMENTS` -- optional test target and deployment options:
- empty -> run the full suite via `./forge test`
- `<file>` -> run a specific test file (e.g. `tests/postgresql_test.py`)
- `<file>::<test>` -> run a specific test (e.g. `tests/foreman_test.py::test_foreman_service`)
- `--database-mode=external` -> test against external database
- `--certificate-source=installer` -> test with installer certificates

## Prerequisites

Before running tests, verify:

1. **Deployment exists** -- a Foreman instance must be deployed and running.
2. **SSH config exists** -- `.tmp/ssh-config` must be present. If missing, run `./forge test` once to generate it.
3. **Virtual environment active** -- `.venv` must be activated (`source .venv/bin/activate`).

## Workflow

### 1. Check Prerequisites

```bash
# Verify venv
test -f .venv/bin/activate && echo "venv exists" || echo "Run ./setup-environment first"

# Verify SSH config
test -f .tmp/ssh-config && echo "SSH config exists" || echo "Run ./forge test to generate"
```

### 2. Run Tests

**Full suite:**

```bash
./forge test
```

**Specific file:**

```bash
pytest tests/postgresql_test.py -vv
```

**Specific test:**

```bash
pytest tests/foreman_test.py::test_foreman_service -vv
```

**With deployment options:**

```bash
./forge test --pytest-args="--certificate-source=installer --database-mode=external"
# or directly:
pytest tests/ --database-mode=external --certificate-source=installer -vv
```

### 3. Interpret Results

- **PASSED** -- test assertions succeeded
- **FAILED** -- assertion failed; check the assertion message and the service/API state
- **ERROR** -- test setup/teardown failed; often an SSH connection issue or missing fixture
- **SKIPPED** -- test skipped due to unmet conditions (e.g. feature not deployed)

### 4. Common Failure Patterns

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| SSH connection refused | VM not running | `./forge vms start` |
| `FileNotFoundError: .tmp/ssh-config` | SSH config not generated | `./forge test` once |
| Hammer tests fail | Hammer not deployed | `./foremanctl deploy --add-feature hammer` |
| API timeout | Foreman not fully started | Wait and retry, check `podman ps` on server |
| Certificate errors | Wrong `--certificate-source` | Match test flag to deployment config |

### 5. Smoker Tests

For browser-based smoke tests (separate from pytest):

```bash
./forge smoker
```

## Notes

- Tests are integration tests running against real VMs, not mocks.
- Test execution time depends on the deployment state and test scope.
- `playbooks_test.py` can run without a deployment (it only checks playbook metadata).
