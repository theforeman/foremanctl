import pytest

pytestmark = pytest.mark.feature("iop")


def test_vex_download_script(server):
    script = server.file("/usr/local/bin/iop-vex-downloader.sh")
    assert script.exists
    assert script.is_file
    assert script.mode == 0o755


def test_vex_download_service_unit(server):
    unit = server.file("/etc/systemd/system/iop-vex-download.service")
    assert unit.exists
    assert unit.is_file

    content = unit.content_string
    assert "Type=oneshot" in content
    assert "iop-vex-downloader.sh" in content
    assert "iop-core-gateway.service" in content


def test_vex_download_timer_unit(server):
    unit = server.file("/etc/systemd/system/iop-vex-download.timer")
    assert unit.exists
    assert unit.is_file

    content = unit.content_string
    assert "OnActiveSec=0" in content
    assert "OnUnitActiveSec=1d" in content
    assert "WantedBy=timers.target" in content


def test_vex_download_timer_enabled(server):
    timer = server.service("iop-vex-download.timer")
    assert timer.is_enabled
    assert timer.is_running


def test_vex_download_path_unit(server):
    unit = server.file("/etc/systemd/system/iop-vex-download.path")
    assert unit.exists
    assert unit.is_file

    content = unit.content_string
    assert "PathChanged=/var/lib/foreman/vex-latest.tar.zst" in content
    assert "PathModified=/var/lib/foreman/vex-latest.tar.zst" in content
    assert "WantedBy=multi-user.target" in content


def test_vex_download_path_enabled(server):
    path = server.service("iop-vex-download.path")
    assert path.is_enabled
    assert path.is_running


def test_vex_download_folder_exist(server):
    assert server.file("/var/www/html/pub/iop/data/csaf/v2/vex/").is_directory
