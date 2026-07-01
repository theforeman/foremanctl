import pytest

pytestmark = pytest.mark.feature("cloud-connector")


def test_rhc_package_installed(server):
    assert server.package("rhc").is_installed


def test_yggdrasil_worker_forwarder_package_installed(server):
    assert server.package("yggdrasil-worker-forwarder").is_installed


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


def test_worker_script_exists(server):
    script = server.file("/usr/libexec/rhc/foreman-rh-cloud-worker")
    assert script.is_file
    assert script.mode == 0o755
    assert script.contains("yggdrasil-worker-forwarder")


def test_rhcd_service_running(server):
    rhcd = server.service("rhcd")
    assert rhcd.is_running
    assert rhcd.is_enabled
