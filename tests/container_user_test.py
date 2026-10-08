def test_all_containers_run_nonroot(server, subtests):
    """Verify that all containers run with non-root users."""
    containers = server.podman.get_containers(status="running")
    assert containers, "No running containers found"

    for container in containers:
        if container.name.startswith("foreman-recurring-"):
            continue

        with subtests.test(container.name):
            config = container.inspect()["Config"]
            user = config["User"].split(":", maxsplit=1)[0].lower()
            assert user not in {"", "0", "root"}
