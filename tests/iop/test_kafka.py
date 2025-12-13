import pytest


def test_kafka_service(server):
    service = server.service("iop-core-kafka")
    assert service.is_running
    assert service.is_enabled


def test_kafka_volume(server):
    result = server.run("podman volume ls --format '{{.Name}}'")
    assert result.succeeded
    assert "iop-core-kafka-data" in result.stdout


def test_kafka_topics_initialized(server):
    result = server.run("podman exec iop-core-kafka /opt/kafka/init.sh --check")
    assert result.succeeded


def test_kafka_secrets(server):
    secrets = [
        'iop-core-kafka-init-start',
        'iop-core-kafka-server-properties',
        'iop-core-kafka-init'
    ]

    result = server.run("podman secret ls --format '{{.Name}}'")
    assert result.succeeded

    for secret_name in secrets:
        assert secret_name in result.stdout


def test_kafka_config_content(server):
    result = server.run("podman secret inspect iop-core-kafka-server-properties --showsecret")
    assert result.succeeded

    config_data = result.stdout.strip()
    assert "advertised.listeners=PLAINTEXT://iop-core-kafka:9092" in config_data
    assert "controller.quorum.voters=1@iop-core-kafka:9093" in config_data


def test_kafka_topic_creation(server):
    topics = [
        "platform.upload.available",
        "platform.inventory.events",
        "platform.system-profile",
        "advisor.recommendations",
        "advisor.payload-tracker",
        "advisor.rules-results",
        "remediations.updates",
        "remediations.status",
        "vulnerability.uploads",
        "vulnerability.evaluator",
        "vulnerability.manager",
        "vmaas.vulnerability.updates",
        "vmaas.package.updates",
        "puptoo.opening",
        "puptoo.validation",
        "yuptoo.opening",
        "yuptoo.validation"
    ]

    result = server.run("podman exec iop-core-kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server iop-core-kafka:9092 --list")
    assert result.succeeded

    for topic in topics:
        assert topic in result.stdout
