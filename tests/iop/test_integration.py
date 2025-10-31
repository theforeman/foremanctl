import json
import pytest
import time


def test_all_services_healthy(server, iop_services):
    for service in iop_services:
        result = server.run(f"systemctl is-active {service}")
        assert result.succeeded
        assert "active" in result.stdout

        result = server.run(f"podman inspect {service} --format '{{{{.State.Health.Status}}}}'")
        if result.succeeded and result.stdout.strip():
            assert "healthy" in result.stdout or "starting" in result.stdout


def test_data_persistence(server):
    result = server.run("podman volume inspect iop-core-kafka-data --format '{{.Mountpoint}}'")
    assert result.succeeded

    mount_point = result.stdout.strip()
    data_dir = server.file(mount_point)
    assert data_dir.exists
    assert data_dir.is_directory


def test_secret_permissions(server, iop_secrets):
    for secret in iop_secrets:
        result = server.run(f"podman secret inspect {secret} --format '{{{{.Spec.Driver.Name}}}}'")
        assert result.succeeded
        assert "file" in result.stdout


def get_service_start_time(server, service_name):
    result = server.run(f"systemctl show {service_name} --property=ActiveEnterTimestamp --value")
    if result.succeeded and result.stdout.strip():
        timestamp_str = result.stdout.strip()
        try:
            # Parse format like "Thu 2025-10-30 19:16:01 UTC"
            return time.mktime(time.strptime(timestamp_str, "%a %Y-%m-%d %H:%M:%S %Z"))
        except (ValueError, IndexError):
            return 0
    return 0
