def test_iop_services_part_of_foreman_target(server):
    result = server.run(
        "systemctl list-units 'iop-core-*' 'iop-service-*'"
        " --type=service --no-legend --all --plain"
    )
    assert result.rc == 0
    services = [line.split()[0] for line in result.stdout.strip().splitlines()]
    assert services, "No IOP services found"

    missing = []
    for service in services:
        # Skip timer-triggered services (cleanup, vmaas-sync)
        triggered_by = server.run(f"systemctl show {service} -p TriggeredBy --value")
        if triggered_by.stdout.strip():
            continue
        result = server.run(f"systemctl show {service} -p PartOf --value")
        if "foreman.target" not in result.stdout:
            missing.append(service)

    assert not missing, f"IOP services not PartOf foreman.target: {missing}"
