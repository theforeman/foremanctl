FRONTENDS = [
    ("iop-advisor-frontend-assets-source", "iop-advisor-frontend"),
    ("iop-host-inventory-frontend-assets-source", "iop-host-inventory-frontend"),
    ("iop-vulnerability-frontend-assets-source", "iop-vulnerability-frontend"),
]


def test_frontend_source_volume_definitions_are_installed(server):
    for source_volume, image_unit in FRONTENDS:
        image_quadlet = server.file(f"/etc/containers/systemd/{image_unit}.image")
        assert image_quadlet.exists
        assert image_quadlet.is_file

        volume_quadlet = server.file(
            f"/etc/containers/systemd/{source_volume}.volume"
        )
        assert volume_quadlet.exists
        assert volume_quadlet.is_file
        assert "Driver=image" in volume_quadlet.content_string
        assert f"Image={image_unit}.image" in volume_quadlet.content_string
        assert f"VolumeName={source_volume}" in volume_quadlet.content_string


def test_frontend_source_volume_services_are_stopped_after_extraction(server):
    for source_volume, _image_unit in FRONTENDS:
        result = server.run(
            f"systemctl is-active {source_volume}-volume.service"
        )
        assert result.stdout.strip() == "inactive"


def test_frontend_source_volumes_are_removed_after_extraction(server):
    for source_volume, _image_unit in FRONTENDS:
        result = server.run(f"podman volume exists {source_volume}")
        assert not result.succeeded
