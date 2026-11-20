import json
import shlex
import time

import pytest

DEVELOPMENT_UNIT = "/etc/systemd/system/foreman-development.service"
BACKEND_PORTS = {
    "postgresql": 5432,
    "valkey": 6379,
    "candlepin": 23443,
}


def _wait_for_json(server, url):
    last_error = ""
    for _ in range(60):
        result = server.run(f"curl --silent --show-error --fail --max-time 5 {shlex.quote(url)}")
        if result.succeeded:
            return json.loads(result.stdout)
        last_error = result.stderr
        time.sleep(2)

    pytest.fail(f"Timed out waiting for {url}: {last_error}")


@pytest.fixture(scope="module", autouse=True)
def development_environment(server):
    if not server.file(DEVELOPMENT_UNIT).exists:
        pytest.skip("No Foreman development deployment on this host")


@pytest.fixture(scope="module")
def development_paths(server, obsah_params):
    user_name = obsah_params.get("foreman_development_user", "vagrant")
    user = server.user(user_name)
    assert user.exists, f"Development user {user_name!r} does not exist"
    return {
        "user": user_name,
        "home": user.home,
        "foreman": f"{user.home}/foreman",
        "certificates": f"{user.home}/foreman-certs",
        "database": obsah_params.get("foreman_development_database_name", "foreman_development"),
        "database_user": obsah_params.get("foreman_database_user", "foreman"),
    }


@pytest.fixture(scope="module")
def development_smart_proxy(server, enabled_features, curl_request, proxy_base_url):
    if "foreman-proxy" not in enabled_features:
        pytest.skip("The foreman-proxy feature is not enabled")

    assert server.file("/etc/systemd/system/smart-proxy-development.service").exists
    service = server.service("smart-proxy-development")
    assert service.is_running, "Development Smart Proxy should be running after deployment"
    assert service.is_enabled, "Development Smart Proxy should be enabled after deployment"

    result = curl_request("features", base_url=proxy_base_url)
    assert result.succeeded, f"Failed to query the development Smart Proxy: {result.stderr}"
    return result.stdout.strip()


@pytest.fixture(scope="module")
def running_development_server(server):
    service = server.service("foreman-development")
    assert not service.is_running, "Foreman development should be stopped after deployment"
    assert not service.is_enabled, "Foreman development should be disabled after deployment"

    try:
        start = server.run("systemctl start foreman-development")
        assert start.succeeded, f"Could not start foreman-development: {start.stderr}"
        yield _wait_for_json(server, "http://127.0.0.1:3000/api/v2/ping")
    finally:
        server.run("systemctl stop foreman-development")
        server.run("systemctl disable foreman-development")
        assert not service.is_running
        assert not service.is_enabled


def test_development_workspace_is_usable(server, development_paths):
    user = development_paths["user"]
    foreman = development_paths["foreman"]
    checkout = server.file(foreman)

    assert checkout.is_directory
    assert checkout.user == user
    assert checkout.mode & 0o200, "Development user cannot write to the Foreman checkout"
    assert server.file(f"{foreman}/.git").exists, "Foreman checkout is missing its Git metadata"

    foreman_test = server.file("/usr/local/bin/foreman-test")
    assert foreman_test.exists
    assert foreman_test.is_symlink

    readable_paths = [
        f"{foreman}/config/database.yml",
        f"{foreman}/config/settings.yaml",
        f"{foreman}/.env",
        f"{development_paths['certificates']}/proxy_ca.pem",
        f"{development_paths['certificates']}/client_cert.pem",
        f"{development_paths['certificates']}/client_key.pem",
    ]
    for path in readable_paths:
        file = server.file(path)
        assert file.is_file, f"Missing development file: {path}"
        assert file.user == user
        assert file.mode & 0o400, f"Development user cannot read {path}"


def test_development_service_is_stopped_and_disabled_after_deploy(server):
    assert server.file(DEVELOPMENT_UNIT).exists
    service = server.service("foreman-development")
    assert not service.is_running
    assert not service.is_enabled


def test_development_rails_ping_reports_healthy_backends(running_development_server):
    foreman = running_development_server["results"]["foreman"]
    assert foreman["database"]["active"]
    assert foreman["cache"]["servers"]
    assert foreman["cache"]["servers"][0]["status"] == "ok"


def test_development_application_is_available_through_apache(running_development_server, foremanapi):
    users = foremanapi.list("users")
    assert any(user["login"] == "admin" for user in users)


def test_hammer_development_setup(
    server, enabled_features, development_paths, running_development_server,
):
    if "hammer" not in enabled_features:
        pytest.skip("The hammer feature is not enabled")

    hammer_dir = f"{development_paths['home']}/hammer-cli"
    result = server.run(f"cd {shlex.quote(hammer_dir)} && bundle exec hammer --version")
    assert result.succeeded, f"Hammer CLI failed: {result.stderr}"
    assert result.stdout.strip()

    config = server.file(f"{hammer_dir}/config/cli.modules.d/foreman.yml")
    assert config.is_file
    assert ":host:" in config.content_string


def test_development_smart_proxy_integration(
    server_fqdn, foremanapi, development_smart_proxy, running_development_server,
):
    assert development_smart_proxy == "200"
    proxies = foremanapi.list("smart_proxies")
    assert any(proxy["name"] == f"{server_fqdn}-dev" for proxy in proxies)
