def test_iop_services_part_of_foreman_target(server, subtests):
    result = server.run(
        "systemctl list-units 'iop-core-*' 'iop-service-*'"
        " --type=service --no-legend --all --plain"
    )
    assert result.rc == 0
    services = [line.split()[0] for line in result.stdout.strip().splitlines()]
    assert services, "No IOP services found"

    for service_name in services:
        service = server.service(service_name)
        if service.systemd_properties.get("TriggeredBy"):
            continue
        with subtests.test(service_name):
            assert "foreman.target" in service.systemd_properties.get("PartOf")
