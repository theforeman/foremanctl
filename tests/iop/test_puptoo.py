import pytest


def test_puptoo_service(server):
    service = server.service("iop-core-puptoo")
    assert service.is_running
    assert service.is_enabled