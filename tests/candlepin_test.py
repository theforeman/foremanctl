def test_candlepin_service(host):
    candlepin = host.service("candlepin")
    assert candlepin.is_running
    assert candlepin.is_enabled


def test_candlepin_port(host):
    candlepin = host.addr("localhost")
    assert candlepin.port("23443").is_reachable


def test_candlepin_status(host):
    status = host.run('curl -k -s -o /dev/null -w \'%{http_code}\' https://localhost:23443/candlepin/status')
    assert status.succeeded
