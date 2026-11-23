import pytest


@pytest.fixture(scope="module")
def upgraded_environment(server):
    if not server.file("/etc/containers/systemd/foreman-upgrade-run.container").exists:
        pytest.skip("Not an upgraded environment")


def test_upgrade_run_service_succeeded(server, upgraded_environment):
    result = server.run("systemctl show --property=ExecMainStatus --value foreman-upgrade-run.service")
    assert result.rc == 0
    assert result.stdout.strip() == "0"


def test_upgrade_tasks_executed(server, upgraded_environment):
    result = server.run(
        "podman exec postgresql psql -U foreman -d foreman -tAc "
        "\"SELECT count(*) FROM upgrade_tasks WHERE last_run_time IS NOT NULL\""
    )
    assert result.rc == 0
    assert int(result.stdout.strip()) > 0
