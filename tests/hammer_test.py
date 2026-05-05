import pytest

from conftest import has_feature

pytestmark = pytest.mark.skipif(
    not has_feature("hammer"),
    reason="hammer not enabled",
)


def test_hammer_ping(server):
    hammer = server.run("hammer ping")
    assert hammer.succeeded

def test_hammer_organizations_list(server):
    hammer = server.run("hammer organization list")
    assert hammer.succeeded
