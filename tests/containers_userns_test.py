def test_containers_user_exists(server):
    """Rootful userns=auto requires the containers helper user."""
    result = server.run("getent passwd containers")
    assert result.rc == 0, "user 'containers' is required for Podman UserNS=auto"


def test_containers_subuid_subgid_ranges(server):
    """containers must have subordinate UID/GID ranges for userns=auto allocation."""
    subuid = server.run("grep '^containers:' /etc/subuid")
    subgid = server.run("grep '^containers:' /etc/subgid")
    assert subuid.rc == 0, "/etc/subuid missing containers: entry"
    assert subgid.rc == 0, "/etc/subgid missing containers: entry"

