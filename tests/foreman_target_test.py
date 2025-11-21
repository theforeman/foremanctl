def test_foreman_target(server):
    foreman_target = server.service("foreman.target")
    assert foreman_target.is_running
    assert foreman_target.is_enabled
