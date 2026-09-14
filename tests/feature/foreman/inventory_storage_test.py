import json

import pytest

pytestmark = pytest.mark.feature("rh-cloud")

FOREMAN_STORAGE_PATH = "/var/lib/foreman"
INVENTORY_PATH = f"{FOREMAN_STORAGE_PATH}/red_hat_inventory"
GENERATED_REPORTS_PATH = f"{INVENTORY_PATH}/generated_reports"

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


def test_foreman_inventory_directory(server):
    directory = server.file(INVENTORY_PATH)
    assert directory.is_directory


@pytest.mark.parametrize("container", FOREMAN_AND_DYNFLOW_CONTAINERS)
def test_foreman_inventory_volume_mount(server, container):
    result = server.run(f"podman inspect {container} --format '{{{{json .Mounts}}}}'")
    assert result.succeeded, result.stderr
    mounts = json.loads(result.stdout)
    destinations = [mount["Destination"] for mount in mounts]
    assert INVENTORY_PATH in destinations, (
        f"expected {INVENTORY_PATH} to be mounted in {container}, got {destinations}"
    )


@pytest.mark.parametrize("container", FOREMAN_AND_DYNFLOW_CONTAINERS)
def test_foreman_inventory_writable(server, container):
    marker = f"foremanctl-write-test-{container}"
    path = f"{INVENTORY_PATH}/{marker}"
    try:
        result = server.run(f"podman exec {container} touch {path}")
        assert result.succeeded, result.stderr
        assert server.file(path).exists
    finally:
        server.run(f"rm -f {path}")


def test_foreman_inventory_shared_between_foreman_and_dynflow(server):
    path = f"{INVENTORY_PATH}/foremanctl-shared-test"
    try:
        result = server.run(f"podman exec dynflow-sidekiq-worker touch {path}")
        assert result.succeeded, result.stderr
        result = server.run(f"podman exec foreman test -f {path}")
        assert result.succeeded, result.stderr
    finally:
        server.run(f"rm -f {path}")


def test_foreman_inventory_generated_reports_writable_from_foreman_and_dynflow(server):
    path = f"{GENERATED_REPORTS_PATH}/foremanctl-generated-reports-test"
    try:
        result = server.run(f"podman exec dynflow-sidekiq-worker mkdir -p {GENERATED_REPORTS_PATH}")
        assert result.succeeded, result.stderr
        result = server.run(f"podman exec dynflow-sidekiq-worker touch {path}")
        assert result.succeeded, result.stderr
        result = server.run(f"podman exec foreman test -f {path}")
        assert result.succeeded, result.stderr
        assert server.file(path).exists
    finally:
        server.run(f"rm -f {path}")
