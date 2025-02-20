import json

import pytest


FOREMAN_PROXY_HOST = 'localhost'
FOREMAN_PROXY_PORT = 9090


def test_foreman_proxy_port(server):
    foreman_proxy = server.addr(FOREMAN_PROXY_HOST)
    assert not foreman_proxy.port(FOREMAN_PROXY_PORT).is_reachable
