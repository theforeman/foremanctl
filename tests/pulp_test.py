import testinfra

def test_pulp_service(host):
    pulp = host.service("pulp")
    assert pulp.exists and pulp.is_running and pulp.is_enabled

def test_pulp_port(host):
    pulp = host.addr("localhost")
    assert pulp.port("8080").is_reachable

def test_pulp_no_daemon_reload_needed(host):
    pulp = host.service("pulp")
    assert pulp.systemd_properties['NeedDaemonReload'] == 'no'

def test_systemd_reload_if_needed(host):
    pulp = host.service("pulp")
    result = host.run("systemctl show pulp --property=NeedDaemonReload")
    assert "NeedDaemonReload=no" in result.stdout
