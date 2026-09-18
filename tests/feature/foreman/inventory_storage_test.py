import json

import pytest

pytestmark = pytest.mark.feature("rh-cloud")

FOREMAN_STORAGE_PATH = "/var/lib/foreman"
INVENTORY_PATH = f"{FOREMAN_STORAGE_PATH}/red_hat_inventory"
UPLOADS_PATH = f"{INVENTORY_PATH}/uploads"
INVENTORY_VOLUME = "foreman-rh-cloud-inventory"

FOREMAN_AND_DYNFLOW_CONTAINERS = [
    "foreman",
    "dynflow-sidekiq-orchestrator",
    "dynflow-sidekiq-worker",
    "dynflow-sidekiq-worker-hosts-queue",
]


def test_foreman_inventory_volume(server):
    result = server.run("podman volume ls --format '{{.Name}}'")
    assert result.succeeded
    assert INVENTORY_VOLUME in result.stdout


@pytest.mark.parametrize("container", FOREMAN_AND_DYNFLOW_CONTAINERS)
def test_foreman_inventory_volume_mount(server, container):
    result = server.run(f"podman inspect {container} --format '{{{{json .Mounts}}}}'")
    assert result.succeeded, result.stderr
    mounts = json.loads(result.stdout)
    inventory_mounts = [mount for mount in mounts if mount.get("Destination") == INVENTORY_PATH]
    assert inventory_mounts, (
        f"expected {INVENTORY_PATH} to be mounted in {container}, "
        f"got {[mount.get('Destination') for mount in mounts]}"
    )
    mount = inventory_mounts[0]
    assert mount.get("Type", "volume") == "volume"
    assert mount.get("Name") == INVENTORY_VOLUME


@pytest.mark.parametrize("container", FOREMAN_AND_DYNFLOW_CONTAINERS)
def test_foreman_inventory_writable(server, container):
    marker = f"foremanctl-write-test-{container}"
    path = f"{INVENTORY_PATH}/{marker}"
    try:
        result = server.run(f"podman exec {container} touch {path}")
        assert result.succeeded, result.stderr
        result = server.run(f"podman exec {container} test -f {path}")
        assert result.succeeded, result.stderr
    finally:
        server.run(f"podman exec {container} rm -f {path}")


def test_foreman_inventory_shared_between_foreman_and_dynflow(server):
    path = f"{INVENTORY_PATH}/foremanctl-shared-test"
    try:
        result = server.run(f"podman exec dynflow-sidekiq-worker touch {path}")
        assert result.succeeded, result.stderr
        result = server.run(f"podman exec foreman test -f {path}")
        assert result.succeeded, result.stderr
    finally:
        server.run(f"podman exec dynflow-sidekiq-worker rm -f {path}")


def test_foreman_inventory_uploads_writable_from_foreman_and_dynflow(server):
    path = f"{UPLOADS_PATH}/foremanctl-uploads-test"
    try:
        result = server.run(f"podman exec dynflow-sidekiq-worker mkdir -p {UPLOADS_PATH}")
        assert result.succeeded, result.stderr
        result = server.run(f"podman exec dynflow-sidekiq-worker touch {path}")
        assert result.succeeded, result.stderr
        result = server.run(f"podman exec foreman test -f {path}")
        assert result.succeeded, result.stderr
    finally:
        server.run(f"podman exec dynflow-sidekiq-worker rm -f {path}")
