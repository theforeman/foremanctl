import pytest


def test_engine_service(server):
    service = server.service("iop-core-engine")
    assert service.is_running
    assert service.is_enabled


def test_engine_secret(server):
    result = server.run("podman secret ls --format '{{.Name}}'")
    assert result.succeeded
    assert "iop-core-engine-config-yml" in result.stdout


def test_engine_config_content(server):
    result = server.run("podman secret inspect iop-core-engine-config-yml --showsecret")
    assert result.succeeded

    config_data = result.stdout.strip()
    assert "insights.specs.default" in config_data
    assert "insights_kafka_service.rules" in config_data
    assert "iop-core-kafka:9092" in config_data


def test_engine_service_dependencies(server):
    result = server.run("systemctl show iop-core-engine --property=After")
    assert result.succeeded
    assert "iop-core-ingress.service" in result.stdout
    assert "iop-core-kafka.service" in result.stdout


def test_engine_kafka_connectivity(server):
    result = server.run("podman logs iop-core-engine 2>&1 | grep -i 'kafka\\|bootstrap'")
    assert result.succeeded