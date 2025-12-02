import pytest

pytestmark = pytest.mark.iop


def test_yuptoo_service(server):
    service = server.service("iop-core-yuptoo")
    assert service.is_running
    assert service.is_enabled
