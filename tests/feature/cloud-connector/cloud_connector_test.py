import pytest

pytestmark = pytest.mark.feature("cloud-connector")


def test_rhc_package_installed(server):
    assert server.package("rhc").is_installed


def test_yggdrasil_worker_forwarder_package_installed(server):
    pkg = server.package("yggdrasil-worker-forwarder")
    if not pkg.is_installed:
        pytest.skip("yggdrasil-worker-forwarder RPM not yet available")


def test_workers_directory_exists(server):
    workers_dir = server.file("/etc/rhc/workers")
    assert workers_dir.is_directory
    assert workers_dir.mode == 0o755


def test_worker_config_exists(server):
    config = server.file("/etc/rhc/workers/foreman_rh_cloud.toml")
    assert config.is_file
    assert config.mode == 0o640
    assert config.contains("FORWARDER_HANDLER=foreman_rh_cloud")
    assert config.contains("/api/v2/rh_cloud/cloud_request")


def test_worker_config_grpc_stanzas(server):
    """On EL 10+ the toml must not contain exec= or protocol= (D-Bus activation
    replaces them). On EL <= 9 both must be present for rhcd."""
    config = server.file("/etc/rhc/workers/foreman_rh_cloud.toml")
    release = server.file("/etc/redhat-release")
    if "release 10" in release.content_string:
        assert not config.contains("exec =")
        assert not config.contains("protocol =")
    else:
        assert config.contains("exec =")
        assert config.contains('protocol = "grpc"')


def test_dispatcher_service_running(server):
    """The dispatcher is rhcd on EL <= 9 and yggdrasil on EL 10+."""
    release = server.file("/etc/redhat-release")
    if "release 10" in release.content_string:
        svc = server.service("yggdrasil")
    else:
        svc = server.service("rhcd")
    assert svc.is_running
    assert svc.is_enabled


def test_worker_service_running(server):
    release = server.file("/etc/redhat-release")
    if "release 10" not in release.content_string:
        return
    svc = server.service("com.redhat.Yggdrasil1.Worker1.foreman_rh_cloud")
    assert svc.is_running
    assert svc.is_enabled


def test_worker_registered_on_dbus(server):
    """The worker must own its well-known D-Bus name on the system bus."""
    release = server.file("/etc/redhat-release")
    if "release 10" not in release.content_string:
        return
    result = server.run("busctl list --system --no-pager | grep foreman_rh_cloud")
    assert result.succeeded, f"worker not found on D-Bus: {result.stderr}"
    assert "com.redhat.Yggdrasil1.Worker1.foreman_rh_cloud" in result.stdout


def test_consumer_cert_exists(server):
    """The system must be registered with subscription-manager (prerequisite
    for cloud connector — the consumer cert CN is the MQTT client ID)."""
    cert = server.file("/etc/pki/consumer/cert.pem")
    assert cert.is_file


def test_worker_config_has_forwarder_url(server):
    """The TOML must set FORWARDER_URL to the Foreman cloud_request endpoint."""
    config = server.file("/etc/rhc/workers/foreman_rh_cloud.toml")
    assert config.contains("FORWARDER_URL=")
    assert config.contains("/api/v2/rh_cloud/cloud_request")


def test_worker_config_has_credentials(server):
    """The TOML must set FORWARDER_USER and FORWARDER_PASSWORD."""
    config = server.file("/etc/rhc/workers/foreman_rh_cloud.toml")
    assert config.contains("FORWARDER_USER=")
    assert config.contains("FORWARDER_PASSWORD=")


def test_cloud_connector_user_exists(server, foremanapi):
    """The Foreman service user for cloud connector must exist."""
    users = foremanapi.list("users", search="login=cloud_connector_user")
    assert len(users) > 0, "cloud_connector_user not found in Foreman"


def test_rhc_instance_id_setting(server, foremanapi):
    """The rhc_instance_id setting must be populated after announce to sources."""
    settings = foremanapi.list("settings", search="name=rhc_instance_id")
    assert len(settings) > 0, "rhc_instance_id setting not found"
    value = settings[0].get("value", "")
    assert value and value != "", "rhc_instance_id must not be empty"
