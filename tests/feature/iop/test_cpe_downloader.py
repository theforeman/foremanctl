import pytest

pytestmark = pytest.mark.feature("iop")


def test_cpe_download_script(server):
    script = server.file("/usr/local/bin/iop-cpe-download.sh")
    assert script.exists
    assert script.is_file
    assert script.mode == 0o755


def test_cpe_download_service_unit(server):
    unit = server.file("/etc/systemd/system/iop-cpe-download.service")
    assert unit.exists
    assert unit.is_file

    content = unit.content_string
    assert "Type=oneshot" in content
    assert "iop-cpe-download.sh" in content
    assert "iop-core-gateway.service" in content
    assert "repository-to-cpe.json" in content
    assert "cpe-dictionary.xml" in content


def test_cpe_download_service_triggers_reposync(server):
    unit = server.file("/etc/systemd/system/iop-cpe-download.service")
    content = unit.content_string
    assert "ExecStartPost" in content
    assert "iop-reposync-trigger.sh" in content


def test_cpe_download_timer_unit(server):
    unit = server.file("/etc/systemd/system/iop-cpe-download.timer")
    assert unit.exists
    assert unit.is_file

    content = unit.content_string
    assert "OnActiveSec=0" in content
    assert "OnUnitActiveSec=24h" in content
    assert "WantedBy=timers.target" in content


def test_cpe_download_timer_enabled(server):
    timer = server.service("iop-cpe-download.timer")
    assert timer.is_enabled
    assert timer.is_running


def test_cpe_download_path_unit(server):
    unit = server.file("/etc/systemd/system/iop-cpe-download.path")
    assert unit.exists
    assert unit.is_file

    content = unit.content_string
    assert "PathChanged=/var/lib/foreman/cpe-dictionary.xml" in content
    assert "PathModified=/var/lib/foreman/cpe-dictionary.xml" in content
    assert "PathChanged=/var/lib/foreman/repository-to-cpe.json" in content
    assert "PathModified=/var/lib/foreman/repository-to-cpe.json" in content
    assert "WantedBy=multi-user.target" in content


def test_cpe_download_path_enabled(server):
    path = server.service("iop-cpe-download.path")
    assert path.is_enabled
    assert path.is_running
