import json
import time

import pytest

FOREMAN_SOCKET = '/run/httpd.foreman.sock'

RECURRING_INSTANCES = [
    "hourly",
    "daily",
    "weekly",
    "monthly",
]


@pytest.fixture(scope="module")
def foreman_status_curl(server, server_fqdn):
    return server.run(f"curl --header 'X-FORWARDED-PROTO: https' --silent --write-out '%{{stderr}}%{{http_code}}' --unix-socket {FOREMAN_SOCKET} http://{server_fqdn}/api/v2/ping")


@pytest.fixture(scope="module")
def foreman_status(foreman_status_curl):
    return json.loads(foreman_status_curl.stdout)


def test_foreman_service(server):
    foreman = server.service("foreman")
    assert foreman.is_running


def test_foreman_socket(server):
    assert server.socket(f"unix://{FOREMAN_SOCKET}").is_listening


def test_foreman_status(foreman_status_curl):
    assert foreman_status_curl.succeeded
    assert foreman_status_curl.stderr == '200'


def test_foreman_status_database(foreman_status):
    assert foreman_status['results']['foreman']['database']['active']


def test_foreman_status_cache(foreman_status):
    assert foreman_status['results']['foreman']['cache']['servers']
    assert foreman_status['results']['foreman']['cache']['servers'][0]['status'] == 'ok'


@pytest.mark.feature('katello')
@pytest.mark.parametrize("katello_service", ['candlepin', 'candlepin_auth', 'foreman_tasks', 'katello_events', 'pulp3', 'pulp3_content'])
def test_katello_services_status(foreman_status, katello_service):
    assert foreman_status['results']['katello']['services'][katello_service]['status'] == 'ok'


@pytest.mark.parametrize("dynflow_instance", ['orchestrator', 'worker', 'worker-hosts-queue'])
def test_foreman_dynflow_container_instances(server, dynflow_instance):
    file = server.file(f"/etc/containers/systemd/dynflow-sidekiq@{dynflow_instance}.container")
    assert file.exists
    assert file.is_symlink


@pytest.mark.parametrize("dynflow_instance", ['orchestrator', 'worker', 'worker-hosts-queue'])
def test_foreman_dynflow_service_instances(server, dynflow_instance):
    service = server.service(f"dynflow-sidekiq@{dynflow_instance}")
    assert service.is_running


@pytest.mark.parametrize("instance", RECURRING_INSTANCES)
def test_foreman_recurring_timers_enabled_and_running(server, instance):
    timer = server.service(f"foreman-recurring@{instance}.timer")
    assert timer.is_enabled
    assert timer.is_running


@pytest.mark.parametrize("instance", RECURRING_INSTANCES)
def test_foreman_recurring_services_exist(server, instance):
    service = server.service(f"foreman-recurring@{instance}.service")
    assert service.exists


@pytest.mark.parametrize("instance", RECURRING_INSTANCES)
def test_foreman_recurring_timer_last_trigger(server, instance):
    """Verify that timers have a valid last trigger time (if they've run)."""
    timer_name = f"foreman-recurring@{instance}.timer"
    timer = server.service(timer_name)
    props = timer.systemd_properties
    assert 'LastTriggerUSec' in props or 'LastTriggerUSecRealtime' in props


@pytest.mark.parametrize("instance", RECURRING_INSTANCES)
def test_foreman_recurring_timer_next_trigger(server, instance):
    """Verify that timers have a scheduled next trigger time."""
    timer_name = f"foreman-recurring@{instance}.timer"
    timer = server.service(timer_name)
    assert timer.systemd_properties["NextElapseUSecRealtime"] != "0"


@pytest.mark.slow
@pytest.mark.parametrize("instance", RECURRING_INSTANCES)
def test_foreman_recurring_timer_execution(server, instance):
    """Verify the recurring container is wired up correctly and can run.

    Triggers a controlled run to exercise the quadlet/image/secrets/env/
    volume plumbing. It deliberately does not wait for the rake task to
    finish: cron:daily/weekly/monthly can run for many minutes and their
    runtime and outcome are not what this test verifies.
    """
    service_name = f"foreman-recurring@{instance}.service"

    previous_invocation = server.service(service_name).systemd_properties.get("InvocationID", "")

    server.check_output(f"systemctl start --no-block {service_name}")

    startup_timeout = 60
    poll_interval = 5
    waited = 0
    while waited < startup_timeout:
        props = server.service(service_name).systemd_properties
        active_state = props["ActiveState"]
        result = props["Result"]
        invocation = props.get("InvocationID", "")

        assert active_state != "failed", (
            f"{service_name} failed to start: "
            f"ActiveState={active_state}, Result={result}"
        )

        if invocation and invocation != previous_invocation and (
            active_state in ("active", "activating", "deactivating")
            or (active_state == "inactive" and result == "success")
        ):
            break

        time.sleep(poll_interval)
        waited += poll_interval
    else:
        pytest.fail(f"{service_name} did not start within {startup_timeout}s")


def test_foreman_delivery_method_setting(foremanapi):
    delivery_method_setting = foremanapi.list('settings', search='name=delivery_method')
    assert delivery_method_setting[0]['value'] == 'smtp'


@pytest.mark.parametrize("setting", ["foreman_url", "unattended_url"])
def test_foreman_fqdn_in_url_settings(foremanapi, server_fqdn, setting):
    settings = foremanapi.list('settings', search=f'name={setting}')
    assert server_fqdn in settings[0]['value']


@pytest.mark.parametrize("setting", ["administrator", "email_reply_address"])
def test_foreman_domain_in_mail_settings(foremanapi, server_fqdn, setting):
    settings = foremanapi.list('settings', search=f'name={setting}')
    domain = str.join('.', server_fqdn.split('.')[1:])
    assert domain in settings[0]['value']


def test_foreman_host_injection(server):
    cmd = server.run(f"curl --header 'X-FORWARDED-PROTO: https' --silent --write-out '%{{stderr}}%{{http_code}}' --unix-socket {FOREMAN_SOCKET} http://evil.hackers.test/api/v2/ping")
    assert cmd.succeeded
    assert cmd.stderr == '403'
