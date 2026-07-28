# Fixture Anti-patterns and Fixes

## pytest Output Format Variants

pytest timing output appears in several formats depending on version and flags. Parse whichever is present.

### Format A: `--fixture-durations` table (pytest ≥ 7.0)

Produced by `pytest --fixture-durations=N`. Has separate rows for fixture setup keyed by fixture name rather than test name. The `num` column is the number of times the fixture ran — the multiplier for wasted work.

```
==================================================================================== fixture duration top ====================================================================================
total          name                                                                                     num med            min
0:02:14.171075 tests/backup_test.py::backup_result                                                        1 0:02:14.171075 0:02:14.171075
0:01:01.216511 tests::yum_repository                                                                      4 0:00:15.195953 0:00:15.077021
0:00:35.195385 tests::client_environment                                                                  2 0:00:17.597693 0:00:17.584542
```

A fixture scoped to a module appears once per module; a function-scoped fixture appears once per test that uses it. The ratio of `num` to the number of test modules is the signal for scope waste.

### Format B: `--durations=N` (all pytest versions)

Produced by `pytest --durations=N`. Lists the slowest individual setup/call/teardown phases across all tests. Does not have a `num` column — each row is one test phase.

```
==================================================================================== slowest 10 durations ====================================================================================
134.17s setup    tests/backup_test.py::test_backup_directory_created
115.48s call     tests/target_lifecycle_test.py::test_foreman_target_restart
 53.76s call     tests/target_lifecycle_test.py::test_foreman_target_stop_start
 44.99s call     tests/pulp_test.py::test_pulp_manager_check
 35.86s setup    tests/feature/katello/client_test.py::test_foreman_content_view
 25.29s teardown tests/feature/katello/client_test.py::test_foreman_content_view
```

The `setup` phase includes time spent in all fixtures the test depends on. A slow `setup` line implicates the fixture chain, not the test body.

### Format C: Combined report (both tables present)

When both `--durations` and `--fixture-durations` are passed, pytest prints four tables in sequence:
1. fixture duration top
2. test call duration top
3. test setup duration top
4. test teardown duration top
5. slowest N durations

Use all four. The fixture table gives the scope-waste signal (`num` column). The setup/teardown tables attribute time to individual tests. The slowest N table is the quickest summary.

### Format D: JUnit XML

Produced by `pytest --junit-xml=report.xml`. Each `<testcase>` element has `time` (seconds) and a `classname` that maps to the test module path. There is no fixture breakdown — only per-test total time. Use to identify slow tests but not to attribute slowness to specific fixtures.

```xml
<testcase classname="tests.feature.katello.client_test"
          name="test_foreman_content_view"
          time="96.420" />
```

---

## Anti-pattern 1: Function-scoped fixtures for expensive remote resources

**What it looks like**: A fixture that makes API calls, SSH connections, or database writes has no `scope=` (default is function scope). The `num` column in the fixture duration table equals the number of tests that use it.

**Why it's slow**: The resource is created and destroyed for every test function. If creation takes 2s and teardown takes 2s, 10 tests cost 40s instead of 4s.

**Fix**: Add `scope="module"`. Requires verifying that tests within the module do not destructively modify the shared resource mid-body — cleanup that happens in a test body must move into the fixture's teardown after `yield`.

```python
# Before
@pytest.fixture
def organization(foremanapi):
    org = foremanapi.create('organizations', {'name': str(uuid.uuid4())})
    yield org
    foremanapi.delete('organizations', org)

# After
@pytest.fixture(scope="module")
def organization(foremanapi):
    org = foremanapi.create('organizations', {'name': str(uuid.uuid4())})
    yield org
    foremanapi.delete('organizations', org)
```

**Expected speedup**: `(N - 1) × (setup_time + teardown_time)` recovered per module, where N is the number of tests using the fixture.

**Caution**: Not safe if tests modify state that other tests in the same module depend on being clean. Audit each consuming test before promoting scope. Tests that delete or mutate the resource mid-body must be refactored to leave the resource intact and let the fixture teardown handle cleanup.

---

## Anti-pattern 2: Overly broad task/async wait

**What it looks like**: A `wait_for_*` helper searches for tasks by label only (no resource ID filter). It is called inside a fixture that runs multiple times.

**Why it's slow**: The wait matches ALL in-flight tasks with that label, including tasks triggered by other concurrent fixtures or tasks left pending from previous tests. A wait that should complete in 5s can take 15s because it blocks on unrelated work.

**Fix**: Pass the specific resource ID to the search filter.

```python
# Before — waits for every MetadataGenerate task in the system
def wait_for_metadata_generate(foremanapi):
    wait_for_tasks(foremanapi, 'label = Actions::Katello::Repository::MetadataGenerate')

# After — waits only for this repository's task
def wait_for_metadata_generate(foremanapi, repo_id):
    wait_for_tasks(
        foremanapi,
        f'label = Actions::Katello::Repository::MetadataGenerate AND input.repository_id = {repo_id}'
    )
```

---

## Anti-pattern 3: O(n×m) teardown loops

**What it looks like**: Teardown code lists resources, then for each resource makes another list call or a per-item delete. Two nested loops over API resources.

**Why it's slow**: Each loop iteration is a synchronous API call that may trigger a backend task and must be awaited. With function scope, the full loop runs for every test.

```python
# Example of the pattern
versions = foremanapi.list('content_view_versions', params={'content_view_id': cv['id']})
for version in versions:
    for environment_id in {e['id'] for e in version['environments']}:
        foremanapi.resource_action('content_views', 'remove_from_environment',
                                   params={'id': cv['id'], 'environment_id': environment_id})
    foremanapi.delete('content_view_versions', version)
```

**Fix**: Combine with Anti-pattern 1 — lift to module scope so the loop runs once per module rather than once per test. Also check whether the API supports bulk operations (`environment_ids` array instead of per-environment calls).

---

## Anti-pattern 4: Multiple runtime startups per test

**What it looks like**: A test or fixture issues two or more `subprocess.run` or container exec calls that each start a heavy runtime (Django, JVM, Rails). Each call pays the full startup cost independently.

**Why it's slow**: Django startup inside a container is 20–40s. Two separate exec calls cost 40–80s for work that could be done in one.

**Fix**: Batch both operations into a single exec invocation with an inline script, or restructure to use the service's HTTP API rather than its CLI when available.

```bash
# Before — two Django startups
podman exec pulp-api pulpcore-manager check --deploy
podman exec pulp-api pulpcore-manager shell -c "..."

# After — one Django startup, two operations
podman exec pulp-api python -c "
import django; django.setup()
# check --deploy logic
# shell logic
"
```

---

## Anti-pattern 5: Inherently slow tests mixed with fast tests

**What it looks like**: Tests that restart system services, run full backups, or perform end-to-end provisioning sit in the same collection as fast unit/API tests. No marker separates them.

**Why it matters**: These tests cannot be optimized — they are waiting for real infrastructure. Without a marker they always run and block the rest of the suite.

**Fix**: Add a `slow` (or `integration`, `e2e`) marker. Exclude from default runs with `-m "not slow"`. Run in a dedicated CI stage.

```python
@pytest.mark.slow
def test_foreman_target_restart(server, certificates, server_fqdn):
    ...
```

In `pytest.ini` or `pyproject.toml`:
```ini
[pytest]
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
```

---

## Parallelization opportunity

If individual test modules create isolated resources (e.g., UUID names), modules are independent and can run with `pytest-xdist`:

```bash
pytest -n auto
```

This does not reduce total CPU time but reduces wall-clock time proportionally to available cores. Before enabling: verify no shared mutable state exists between modules (shared files, fixed resource names, global database sequences).
