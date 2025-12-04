import pytest


def test_vmaas_reposcan_service(server):
    service = server.service("iop-service-vmaas-reposcan")
    assert service.is_running
    assert service.is_enabled


def test_vmaas_webapp_go_service(server):
    service = server.service("iop-service-vmaas-webapp-go")
    assert service.is_running
    assert service.is_enabled


def test_vmaas_webapp_go_service_dependencies(server):
    result = server.run("systemctl show iop-service-vmaas-webapp-go --property=After")
    assert result.succeeded
    assert "iop-service-vmaas-reposcan.service" in result.stdout


def test_vmaas_webapp_go_service_wants(server):
    result = server.run("systemctl show iop-service-vmaas-webapp-go --property=Wants")
    assert result.succeeded
    assert "iop-service-vmaas-reposcan.service" in result.stdout


def test_vmaas_database_secrets(server):
    result = server.run("podman secret ls --format '{{.Name}}'")
    assert result.succeeded
    assert "iop-service-vmaas-reposcan-database-username" in result.stdout
    assert "iop-service-vmaas-reposcan-database-password" in result.stdout
    assert "iop-service-vmaas-reposcan-database-name" in result.stdout
    assert "iop-service-vmaas-reposcan-database-host" in result.stdout
    assert "iop-service-vmaas-reposcan-database-port" in result.stdout


def test_vmaas_data_volume(server):
    result = server.run("podman volume ls --format '{{.Name}}' | grep iop-service-vmaas-data")
    assert result.succeeded
    assert "iop-service-vmaas-data" in result.stdout
