import pytest

FLAVOR_CORE_IMAGES = [
    "pulp",
    "candlepin",
    "foreman"
]


@pytest.fixture(params=FLAVOR_CORE_IMAGES)
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
