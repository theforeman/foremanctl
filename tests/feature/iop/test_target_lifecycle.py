def test_iop_services_follow_foreman_target_stop_lifecycle(server, subtests):
    result = server.run(
        "systemctl list-units 'iop-core-*' 'iop-service-*'"
        " --type=service --no-legend --all --plain"
    )
    assert result.succeeded
    services = [line.split()[0] for line in result.stdout.strip().splitlines()]
    assert services, "No IOP services found"

    for service_name in services:
        service = server.service(service_name)
        if service.systemd_properties.get("TriggeredBy"):
            continue
        with subtests.test(service_name):
            part_of = service.systemd_properties.get("PartOf") or ""
            stop_propagated_from = (
                service.systemd_properties.get("StopPropagatedFrom") or ""
            )
            assert (
                "foreman.target" in part_of
                or "foreman.target" in stop_propagated_from
            )
