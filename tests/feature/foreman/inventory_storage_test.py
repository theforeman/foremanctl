import json

import pytest

FOREMAN_STORAGE_PATH = "/var/lib/foreman"
INVENTORY_EXPORTS_PATH = f"{FOREMAN_STORAGE_PATH}/red_hat_inventory/exports"

FOREMAN_AND_DYNFLOW_CONTAINERS = [
    "foreman",
    "dynflow-sidekiq-orchestrator",
    "dynflow-sidekiq-worker",
    "dynflow-sidekiq-worker-hosts-queue",
]


def test_foreman_storage_directory(server):
    directory = server.file(f"{FOREMAN_STORAGE_PATH}/")
    assert directory.is_directory
    assert directory.user == "root"
    assert directory.group == "root"
    assert directory.mode == 0o755


@pytest.mark.parametrize("container", FOREMAN_AND_DYNFLOW_CONTAINERS)
def test_foreman_storage_volume_mount(server, container):
    result = server.run(f"podman inspect {container} --format '{{{{json .Mounts}}}}'")
    assert result.succeeded, result.stderr
    mounts = json.loads(result.stdout)
    destinations = [mount["Destination"] for mount in mounts]
    assert FOREMAN_STORAGE_PATH in destinations, (
        f"expected {FOREMAN_STORAGE_PATH} to be mounted in {container}, got {destinations}"
    )


@pytest.mark.parametrize("container", FOREMAN_AND_DYNFLOW_CONTAINERS)
def test_foreman_storage_writable(server, container):
    marker = f"foremanctl-write-test-{container}"
    path = f"{FOREMAN_STORAGE_PATH}/{marker}"
    try:
        result = server.run(f"podman exec {container} touch {path}")
        assert result.succeeded, result.stderr
        assert server.file(path).exists
    finally:
        server.run(f"rm -f {path}")


def test_foreman_storage_shared_between_foreman_and_dynflow(server):
    path = f"{FOREMAN_STORAGE_PATH}/foremanctl-shared-test"
    try:
        result = server.run(f"podman exec dynflow-sidekiq-worker touch {path}")
        assert result.succeeded, result.stderr
        result = server.run(f"podman exec foreman test -f {path}")
        assert result.succeeded, result.stderr
    finally:
        server.run(f"rm -f {path}")


def test_foreman_inventory_exports_writable_from_foreman_and_dynflow(server):
    path = f"{INVENTORY_EXPORTS_PATH}/foremanctl-exports-test"
    try:
        result = server.run(f"podman exec dynflow-sidekiq-worker mkdir -p {INVENTORY_EXPORTS_PATH}")
        assert result.succeeded, result.stderr
        result = server.run(f"podman exec dynflow-sidekiq-worker touch {path}")
        assert result.succeeded, result.stderr
        result = server.run(f"podman exec foreman test -f {path}")
        assert result.succeeded, result.stderr
        assert server.file(path).exists
    finally:
        server.run(f"rm -f {path}")
