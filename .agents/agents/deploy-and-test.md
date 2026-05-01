---
name: deploy-and-test
description: >-
  Full lifecycle validation agent. Starts VMs, deploys Foreman, runs tests,
  and attempts to fix code failures up to 2 times before reporting back.
references:
  - docs/developer/testing.md
  - development/playbooks/test/test.yaml
  - development/playbooks/vms/vms.yaml
---

# Agent - Deploy and Test

Autonomous validation agent that runs the full foremanctl lifecycle: environment setup, deployment, testing, and up to 2 fix-and-retry cycles on failure.

## When to Use

Spawn this agent after implementing code changes that affect deployment or services. It validates the changes end-to-end in an isolated environment.

## Workflow

### Phase 1: Environment Setup

Start the development VMs and deploy Foreman.

```bash
./forge vms start
```

Wait for VMs to be ready, then deploy:

```bash
/foremanctl deploy --foreman-initial-admin-password=changeme --initial-organization="Foreman CI" --initial-location="Internet" --tuning development
```

If deployment fails, go to Phase 3 (fix loop) — a deploy failure counts as the first attempt.

### Phase 2: Test Execution

Run the full test suite:

```bash
./forge test
```

Parse the pytest output. If all tests pass, go to Phase 4 (report). If tests fail, go to Phase 3.

### Phase 3: Fix Loop

Attempt to fix failures, up to 2 total attempts. Each attempt:

1. **Analyze** — read the failure output. Identify which tests failed and the root cause (assertion error, service not running, missing file, configuration issue, etc.).
2. **Classify** — determine if the failure is a code issue or an infrastructure issue.
   - **Infrastructure issue** (VM connectivity, Vagrant error, network timeout, disk space): stop and report. Do not attempt to fix.
   - **Code issue** (wrong config, missing task, template error, incorrect variable): proceed to fix.
3. **Diagnose** — read the relevant source files (roles, templates, vars, playbooks) to understand what went wrong.
4. **Fix** — apply a targeted change to the source code. Only modify files directly related to the failure.
5. **Re-deploy** — if the fix changed any deployment code (roles, playbooks, vars, templates), re-run deployment:
   ```bash
   ./foremanctl deploy
   ```
6. **Re-test** — run the test suite again:
   ```bash
   ./forge test
   ```
7. If tests pass, go to Phase 4. If tests still fail and attempts remain, repeat from step 1.

### Phase 4: Report

Produce a structured report:

```markdown
## Deploy and Test Results

### Environment
- VMs: started/failed
- Deploy: success/failed (attempt N)

### Tests
- Passed: N
- Failed: M
- Skipped: K

### Fixes Applied
<!-- For each fix attempt -->
- Attempt N: <description of what was changed and why>
  - Files modified: <list>
  - Result: pass/fail

### Remaining Failures
<!-- If any tests still fail after 2 attempts -->
- test_name: <error summary>
```

## Constraints

- Only modify files that are directly causing test or deploy failures.
- Do not refactor, clean up, or change unrelated code.
- Do not modify test files to make them pass -- fix the source code instead.
- If a failure is an infrastructure issue (VM, network, Vagrant, disk), stop and report. Do not attempt to fix.
- Each deploy cycle takes several minutes. Budget time accordingly.
- Maximum 2 fix attempts. After 2 failed attempts, report and stop.

## Environment Details

- VMs are managed by Vagrant (see `Vagrantfile`).
- Tests use pytest with testinfra, connecting via SSH to VMs.
- SSH config is generated at `.tmp/ssh-config` by the test playbook.
- Default test credentials: `admin` / `changeme`.
- Test fixtures and options are defined in `tests/conftest.py`.
