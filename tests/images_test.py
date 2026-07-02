import pytest

CORE_IMAGES = [
    "valkey",
    'pulp'
]


@pytest.fixture(params=CORE_IMAGES)
def core_image(request):
    return request.param


def test_image_file_exists(server, core_image):
    image_file = server.file(f"/etc/containers/systemd/{core_image}.image")
    assert image_file.exists and image_file.is_file


def test_image_dropin_directory_exists(server, core_image):
    dropin_dir = server.file(f"/etc/containers/systemd/{core_image}.image.d")
    assert dropin_dir.exists and dropin_dir.is_directory


def test_image_service_exists(server, core_image):
    service = server.service(f"{core_image}-image")
    assert service.exists


def test_image_registry_auth_file(server, core_image):
    f = server.file(f"/etc/containers/systemd/{core_image}.image")
    assert "REGISTRY_AUTH_FILE" in f.content_string


def test_postgresql_image_file(server, database_mode):
    image_file = server.file("/etc/containers/systemd/postgresql.image")
    if database_mode == 'external':
        assert not image_file.exists
    else:
        assert image_file.exists and image_file.is_file


def test_foreman_proxy_image_file(server, enabled_features):
    image_file = server.file("/etc/containers/systemd/foreman-proxy.image")
    if 'foreman-proxy' in enabled_features:
        assert image_file.exists and image_file.is_file
    else:
        assert not image_file.exists


def test_foreman_proxy_image_registry_auth_file(server, enabled_features):
    image_file = server.file("/etc/containers/systemd/foreman-proxy.image")
    if 'foreman-proxy' in enabled_features:
        assert "REGISTRY_AUTH_FILE" in image_file.content_string
    else:
        assert not image_file.exists

