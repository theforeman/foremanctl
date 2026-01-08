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
        "platform.engine.results",
        "platform.insights.rule-hits",
        "platform.insights.rule-deactivation",
        "platform.inventory.events",
        "platform.inventory.host-ingress",
        "platform.sources.event-stream",
        "platform.playbook-dispatcher.runs",
        "platform.upload.announce",
        "platform.upload.validation",
        "platform.logging.logs",
        "platform.payload-status",
        "platform.remediation-updates.vulnerability",
        "vulnerability.evaluator.results",
        "vulnerability.evaluator.recalc",
        "vulnerability.evaluator.upload",
        "vulnerability.grouper.inventory.upload",
        "vulnerability.grouper.advisor.upload"
    ]

    result = server.run("podman exec iop-core-kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server iop-core-kafka:9092 --list")
    assert result.succeeded

    for topic in topics:
        assert topic in result.stdout
