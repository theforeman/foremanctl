import pytest

pytestmark = pytest.mark.feature("iop")


def test_vuln_metadata_download_script(server):
    script = server.file("/usr/local/bin/iop-vuln-metadata-download.sh")
    assert script.exists
    assert script.is_file
    assert script.mode == 0o755


def test_vuln_metadata_download_service_unit(server):
    unit = server.file("/etc/systemd/system/iop-vuln-metadata-download.service")
    assert unit.exists
    assert unit.is_file

    content = unit.content_string
    assert "Type=oneshot" in content
    assert "iop-vuln-metadata-download.sh" in content
    assert "iop-core-gateway.service" in content
    assert "repository-to-cpe.json" in content
    assert "cpe-dictionary.xml" in content
    assert "cvemap.xml" in content


def test_vuln_metadata_download_reposync_trigger_is_in_script(server):
    # The reposync trigger is merged into the download script and runs only
    # when a file changed, so the service must not use a separate ExecStartPost.
    unit = server.file("/etc/systemd/system/iop-vuln-metadata-download.service")
    content = unit.content_string
    assert "ExecStartPost" not in content

    script = server.file("/usr/local/bin/iop-vuln-metadata-download.sh")
    script_content = script.content_string
    assert "trigger_reposync" in script_content
    assert "/api/vmaas-reposcan/v1/sync" in script_content


def test_vuln_metadata_download_timer_unit(server):
    unit = server.file("/etc/systemd/system/iop-vuln-metadata-download.timer")
    assert unit.exists
    assert unit.is_file

    content = unit.content_string
    assert "OnActiveSec=0" in content
    assert "OnUnitActiveSec=24h" in content
    assert "WantedBy=timers.target" in content


def test_vuln_metadata_download_timer_enabled(server):
    timer = server.service("iop-vuln-metadata-download.timer")
    assert timer.is_enabled
    assert timer.is_running


def test_vuln_metadata_download_path_unit(server):
    unit = server.file("/etc/systemd/system/iop-vuln-metadata-download.path")
    assert unit.exists
    assert unit.is_file

    content = unit.content_string
    assert "PathChanged=/var/lib/foreman/cpe-dictionary.xml" in content
    assert "PathModified=/var/lib/foreman/cpe-dictionary.xml" in content
    assert "PathChanged=/var/lib/foreman/repository-to-cpe.json" in content
    assert "PathModified=/var/lib/foreman/repository-to-cpe.json" in content
    assert "PathChanged=/var/lib/foreman/cvemap.xml" in content
    assert "PathModified=/var/lib/foreman/cvemap.xml" in content
    assert "WantedBy=multi-user.target" in content


def test_vuln_metadata_download_path_enabled(server):
    path = server.service("iop-vuln-metadata-download.path")
    assert path.is_enabled
    assert path.is_running
