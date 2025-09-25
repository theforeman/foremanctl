import pytest


def test_hammer_ping(server):
    if server.system_info.distribution == 'debian':
        pytest.xfail('Hammer is not properly set up on Debian yet')
    hammer = server.run("hammer ping")
    assert hammer.succeeded
