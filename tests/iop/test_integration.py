import pytest


def test_iop_core_kafka_service(server):
    service = server.service("iop-core-kafka")
    assert service.is_running
    assert service.is_enabled
