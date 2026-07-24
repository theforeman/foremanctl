import shlex


def test_all_containers_run_nonroot(server):
    """Verify all running containers use non-root users."""
    
    result = server.run("podman ps --format '{{.Names}}'")
    assert result.succeeded, result.stderr

    container_names = result.stdout.split()
    assert container_names, "No running containers found"

    root_containers = []

    for container_name in container_names:
        result = server.run(
            f"podman inspect {shlex.quote(container_name)} "
            "--format '{{.ImageName}}|{{.Config.User}}'"
        )
        assert result.succeeded, f"Failed to inspect container {container_name}: {result.stderr}"

        image_name, configured_user = result.stdout.strip().split("|", maxsplit=1)
        user = configured_user.split(":", maxsplit=1)[0].lower()

        if user in {"", "0", "root"}:
            root_containers.append(
                f"{container_name} (image={image_name}, Config.User={configured_user or '<empty>'})"
            )

    assert not root_containers, (
        "Running containers configured to use root:\n" + "\n".join(root_containers)
    )
