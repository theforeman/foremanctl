VALKEY_HOST = 'localhost'
VALKEY_PORT = 6379
VALKEY_DATA_DIR = '/var/lib/valkey'
VALKEY_IMAGE_UID = 1001


def test_valkey_service(server):
    valkey = server.service("valkey")
    assert valkey.is_running


def test_redis_service_absent(server):
    redis = server.service("redis")
    assert not redis.exists


def test_valkey_port(server):
    valkey = server.addr(VALKEY_HOST)
    assert valkey.port(VALKEY_PORT).is_reachable


def test_valkey_userns_is_private(server):
    """UserNS=auto must isolate the container from the host user namespace."""
    result = server.run("podman inspect valkey --format '{{.HostConfig.UsernsMode}}'")
    assert result.rc == 0, result.stderr
    assert result.stdout.strip() == "private"


def test_valkey_runs_as_image_user(server):
    result = server.run("podman exec valkey id -u")
    assert result.rc == 0, result.stderr
    assert int(result.stdout.strip()) == VALKEY_IMAGE_UID


def test_valkey_data_not_owned_by_image_uid(server):
    """Bind-mounted data must not be owned by the container's numeric UID on the host."""
    data = server.file(VALKEY_DATA_DIR)
    assert data.exists
    assert data.is_directory
    assert data.uid != VALKEY_IMAGE_UID, (
        f"{VALKEY_DATA_DIR} owned by UID {data.uid}; expected remapped UID, not {VALKEY_IMAGE_UID}"
    )


def test_valkey_image_uid_cannot_write_host_data(server):
    """A host process with the container UID must not be able to write the data dir."""
    probe = (
        f"setpriv --reuid={VALKEY_IMAGE_UID} --clear-groups -- "
        f"touch {VALKEY_DATA_DIR}/.foremanctl-uid-leak-probe"
    )
    result = server.run(probe)
    server.run(f"rm -f {VALKEY_DATA_DIR}/.foremanctl-uid-leak-probe")
    assert result.rc != 0, (
        f"UID {VALKEY_IMAGE_UID} could write {VALKEY_DATA_DIR}; userns isolation is leaking"
    )


def test_valkey_container_can_write_data(server):
    """Remapping must not break the container's own access to its data dir."""
    result = server.run("podman exec valkey touch /data/.foremanctl-userns-write-test")
    assert result.rc == 0, result.stderr
    cleanup = server.run("podman exec valkey rm -f /data/.foremanctl-userns-write-test")
    assert cleanup.rc == 0, cleanup.stderr
