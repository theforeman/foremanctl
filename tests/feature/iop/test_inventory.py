def test_inventory_migrate_service(server):
    service = server.service("iop-core-host-inventory-migrate")
    assert service.is_enabled


def test_inventory_mq_service(server):
    service = server.service("iop-core-host-inventory")
    assert service.is_running
    assert service.is_enabled


def test_inventory_api_service(server):
    service = server.service("iop-core-host-inventory-api")
    assert service.is_running
    assert service.is_enabled


def test_inventory_service_dependencies(server):
    result = server.run("systemctl show iop-core-host-inventory --property=After")
    assert result.succeeded
    assert "iop-core-host-inventory-migrate.service" in result.stdout


def test_inventory_api_endpoint(server, iop_image):
    result = server.run(f"podman run --network=iop-core-network --rm {iop_image('iop-inventory')} curl --fail -s -o /dev/null http://iop-core-host-inventory-api:8081/health")
    assert result.succeeded


def test_inventory_cleanup_service(server):
    service = server.service("iop-core-host-inventory-cleanup")
    assert not service.is_running


def test_inventory_cleanup_service_enabled(server):
    result = server.run("systemctl is-enabled iop-core-host-inventory-cleanup")
    assert result.succeeded
    assert "generated" in result.stdout


def test_inventory_cleanup_timer(server):
    service = server.service("iop-core-host-inventory-cleanup.timer")
    assert service.is_enabled
    assert service.is_running


def test_inventory_cleanup_timer_config(server):
    timer_file = server.file("/etc/systemd/system/iop-core-host-inventory-cleanup.timer")
    assert timer_file.exists
    assert timer_file.is_file

    content = timer_file.content_string
    assert "OnBootSec=10min" in content
    assert "OnUnitActiveSec=24h" in content
    assert "Persistent=true" in content
    assert "RandomizedDelaySec=300" in content
    assert "WantedBy=timers.target" in content
