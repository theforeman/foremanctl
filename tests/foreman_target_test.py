from conftest import get_service


def test_foreman_target(server, user):
    foreman_target = get_service(server, "foreman.target", user)
    assert foreman_target.is_running
    assert foreman_target.is_enabled
