import shlex

EXPECTED_ROOT_IMAGES = {
    "quay.io/foreman/pulp:foreman-nightly",
    "quay.io/iop/puptoo:foreman-3.18",
    "quay.io/iop/yuptoo:foreman-3.18",
}


def test_root_containers_match_expected(server):
    """Verify that root containers match the temporary known-broken baseline."""
    result = server.run("podman ps --format '{{.Names}}'")
    assert result.succeeded, result.stderr

    container_names = result.stdout.split()
    assert container_names, "No running containers found"

    expected_root_containers = []
    root_containers = []

    for container_name in container_names:
        result = server.run(
            f"podman inspect {shlex.quote(container_name)} "
            "--format '{{.ImageName}}|{{.Config.User}}'"
        )
        assert result.succeeded, (
            f"Failed to inspect container {container_name}: {result.stderr}"
        )

        image_name, configured_user = result.stdout.strip().split("|", maxsplit=1)
        user = configured_user.split(":", maxsplit=1)[0].lower()

        container_details = (
            f"{container_name} "
            f"(image={image_name}, "
            f"Config.User={configured_user or '<empty>'})"
        )

        if image_name in EXPECTED_ROOT_IMAGES:
            expected_root_containers.append(container_details)

        if user in {"", "0", "root"}:
            root_containers.append(container_details)

    expected_output = "\n".join(sorted(expected_root_containers)) or "<none>"
    actual_output = "\n".join(sorted(root_containers)) or "<none>"

    assert sorted(expected_root_containers) == sorted(root_containers), (
        "Root containers differ from the expected temporary baseline:\n"
        f"Expected:\n{expected_output}\n"
        f"Actual:\n{actual_output}"
    )
