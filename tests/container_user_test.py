# These still need to be fixed
EXPECTED_ROOT_IMAGES = {
    "quay.io/iop/puptoo:foreman-3.18",
    "quay.io/iop/yuptoo:foreman-3.18",
}


def test_root_containers_match_expected(server, subtests):
    """Verify that root containers match the temporary known-broken baseline."""
    containers = server.podman.get_containers(status="running")
    assert containers, "No running containers found"

    for container in containers:
        with subtests.test(container.name):
            config = container.inspect()['Config']
            if config['Image'] in EXPECTED_ROOT_IMAGES:
                assert config['User'] in {"", "0", "root"}
            else:
                assert config['User'] not in {"", "0", "root"}
