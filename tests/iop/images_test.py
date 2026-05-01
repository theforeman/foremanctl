import pytest

pytestmark = pytest.mark.feature("iop")

IOP_IMAGES = [
    "iop-kafka",
    "iop-ingress",
    "iop-puptoo",
    "iop-yuptoo",
    "iop-engine",
    "iop-gateway",
    "iop-inventory",
    "iop-advisor",
    "iop-remediation",
    "iop-vmaas",
    "iop-vulnerability",
    "iop-advisor-frontend",
    "iop-inventory-frontend",
    "iop-vulnerability-frontend",
]


@pytest.mark.parametrize("image_name", IOP_IMAGES)
def test_iop_image_file_exists(server, image_name):
    image_file = server.file(f"/etc/containers/systemd/{image_name}.image")
    assert image_file.exists and image_file.is_file


@pytest.mark.parametrize("image_name", IOP_IMAGES)
def test_iop_image_registry_auth_file(server, image_name):
    f = server.file(f"/etc/containers/systemd/{image_name}.image")
    assert "REGISTRY_AUTH_FILE" in f.content_string
