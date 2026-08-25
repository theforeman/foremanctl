def test_compliance_backend_api_service(server):
    service = server.service("iop-service-compliance-backend-api")
    assert service.is_running
    assert service.is_enabled


def test_compliance_ssg_service(server):
    service = server.service("iop-service-compl-ssg")
    assert service.is_running
    assert service.is_enabled


def test_compliance_inventory_consumer_service(server):
    service = server.service("iop-service-compl-inventory-consumer")
    assert service.is_running
    assert service.is_enabled


def test_compliance_goodjob_service(server):
    service = server.service("iop-service-compl-goodjob")
    assert service.is_running
    assert service.is_enabled


def test_compliance_dbmigrate_quadlet_file(server):
    quadlet_file = server.file("/etc/containers/systemd/iop-service-compl-dbmigrate.container")
    assert quadlet_file.exists
    assert quadlet_file.is_file


def test_compliance_api_container(server):
    result = server.run("podman ps --format '{{.Names}}' | grep iop-service-compliance-backend-api")
    assert result.succeeded
    assert "iop-service-compliance-backend-api" in result.stdout


def test_compliance_ssg_container(server):
    result = server.run("podman ps --format '{{.Names}}' | grep iop-service-compl-ssg")
    assert result.succeeded
    assert "iop-service-compl-ssg" in result.stdout


def test_compliance_api_quadlet_file(server):
    quadlet_file = server.file("/etc/containers/systemd/iop-service-compliance-backend-api.container")
    assert quadlet_file.exists
    assert quadlet_file.is_file


def test_compliance_api_service_dependencies(server):
    result = server.run("systemctl show iop-service-compliance-backend-api --property=After")
    assert result.succeeded
    assert "iop-service-compl-dbmigrate.service" in result.stdout


def test_compliance_inventory_consumer_dependencies(server):
    result = server.run("systemctl show iop-service-compl-inventory-consumer --property=After")
    assert result.succeeded
    assert "iop-core-kafka.service" in result.stdout


def test_compliance_database_secrets(server):
    result = server.run("podman secret ls --format '{{.Name}}'")
    assert result.succeeded
    assert "iop-service-compliance-database-username" in result.stdout
    assert "iop-service-compliance-database-password" in result.stdout
    assert "iop-service-compliance-database-name" in result.stdout
    assert "iop-service-compliance-database-host" in result.stdout
    assert "iop-service-compliance-database-port" in result.stdout


def test_compliance_secret_key_base_secret(server):
    result = server.run("podman secret ls --format '{{.Name}}'")
    assert result.succeeded
    assert "iop-service-compliance-secret-key-base" in result.stdout


def test_compliance_import_ssg_timer(server):
    service = server.service("iop-service-compl-import-ssg.timer")
    assert service.is_running
    assert service.is_enabled


def test_compliance_import_ssg_timer_file(server):
    timer_file = server.file("/etc/systemd/system/iop-service-compl-import-ssg.timer")
    assert timer_file.exists
    assert timer_file.is_file
    assert "OnUnitActiveSec=5min" in timer_file.content_string
