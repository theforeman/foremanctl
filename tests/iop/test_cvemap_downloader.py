import pytest

pytestmark = pytest.mark.iop


def test_cvemap_download_script(server):
    script = server.file("/usr/local/bin/iop-cvemap-download.sh")
    assert script.exists
    assert script.is_file
    assert script.mode == 0o755


def test_cvemap_download_service_unit(server):
    unit = server.file("/etc/systemd/system/iop-cvemap-download.service")
    assert unit.exists
    assert unit.is_file

    content = unit.content_string
    assert "Type=oneshot" in content
    assert "iop-cvemap-download.sh" in content
    assert "iop-core-gateway.service" in content


def test_cvemap_download_timer_unit(server):
    unit = server.file("/etc/systemd/system/iop-cvemap-download.timer")
    assert unit.exists
    assert unit.is_file

    content = unit.content_string
    assert "OnActiveSec=0" in content
    assert "OnUnitActiveSec=24h" in content
    assert "WantedBy=timers.target" in content


def test_cvemap_download_timer_enabled(server):
    timer = server.service("iop-cvemap-download.timer")
    assert timer.is_enabled
    assert timer.is_running


def test_cvemap_download_path_unit(server):
    unit = server.file("/etc/systemd/system/iop-cvemap-download.path")
    assert unit.exists
    assert unit.is_file

    content = unit.content_string
    assert "PathChanged=/var/lib/foreman/cvemap.xml" in content
    assert "PathModified=/var/lib/foreman/cvemap.xml" in content
    assert "WantedBy=multi-user.target" in content


def test_cvemap_download_path_enabled(server):
    path = server.service("iop-cvemap-download.path")
    assert path.is_enabled
    assert path.is_running
