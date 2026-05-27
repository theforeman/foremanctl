import subprocess

import pytest


@pytest.fixture
def errored_foreman_task(database):
    """Create an errored foreman task for testing, cleanup after test"""

    database.run(
        "podman exec postgresql psql -U foreman -d foreman -c "
        "\"DELETE FROM foreman_tasks_tasks WHERE label = 'test_errored_task'\""
    )
    database.run(
        "podman exec postgresql psql -U foreman -d foreman -c "
        "\"INSERT INTO foreman_tasks_tasks (id, type, label, state, result, started_at, ended_at, state_updated_at) "
        "VALUES (gen_random_uuid(), 'Actions::Test::Task', 'test_errored_task', 'paused', 'error', NOW(), NOW(), NOW())\""
    )

    yield

    # cleanup
    database.run(
        "podman exec postgresql psql -U foreman -d foreman -c "
        "\"DELETE FROM foreman_tasks_tasks WHERE label = 'test_errored_task'\""
    )


def test_health_checks_pass():
    """Verify health checks pass on a working deployment"""

    subprocess.check_call(
        ['./foremanctl', 'health', '--skip-check-foreman-tasks']
    )


def test_foreman_tasks_check_detects_errors(errored_foreman_task):
    """Verify foreman tasks check detects errored tasks and fails"""

    result = subprocess.run(
        ['./foremanctl', 'health'],
        capture_output=True,
        text=True
    )
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert 'foreman task' in output.lower() and 'error' in output.lower()


def test_foreman_tasks_skipped(errored_foreman_task):
    """Verify foreman tasks check is skipped when passed the `--skip-check-foreman-tasks` param"""

    subprocess.check_call(
        ['./foremanctl', 'health', '--skip-check-foreman-tasks']
    )
