def test_ingress_service(server):
    service = server.service("iop-core-ingress")
    assert service.is_running
    assert service.is_enabled


def test_ingress_http_endpoint(server, iop_image):
    result = server.run(f"podman run --network=foreman-core-network --rm {iop_image('iop-ingress')} curl --fail -s -o /dev/null http://iop-core-ingress:8080/")
    assert result.succeeded


def test_ingress_archive_volume(server):
    result = server.run("podman volume inspect iop-core-ingress-archives")
    assert result.succeeded

    result = server.run(
        "podman inspect iop-core-ingress "
        "--format '{{range .Mounts}}{{.Name}}:{{.Destination}}{{end}}'"
    )
    assert result.succeeded
    assert (
        "iop-core-ingress-archives:/var/tmp/insights-archives"
        in result.stdout
    )

    result = server.run(
        "podman inspect iop-core-ingress "
        "--format '{{range .Config.Env}}{{println .}}{{end}}'"
    )
    assert result.succeeded
    assert (
        "INGRESS_STORAGEFILESYSTEMPATH=/var/tmp/insights-archives"
        in result.stdout.splitlines()
    )


def test_ingress_archive_volume_is_writable(server):
    result = server.run(
        "podman exec iop-core-ingress "
        "test -w /var/tmp/insights-archives"
    )
    assert result.succeeded, result.stderr


def test_ingress_archive_survives_container_recreation(server):
    command = """
      volume_path=$(podman volume inspect \
        --format '{{.Mountpoint}}' iop-core-ingress-archives) &&
      probe="$volume_path/sat47410-persistence-probe.tar.gz" &&
      trap 'rm -f "$probe"' EXIT &&
      old_container_id=$(podman inspect \
        --format '{{.Id}}' iop-core-ingress) &&
      podman exec iop-core-ingress \
        touch /var/tmp/insights-archives/sat47410-persistence-probe.tar.gz &&
      systemctl restart iop-core-ingress &&
      new_container_id=$(podman inspect \
        --format '{{.Id}}' iop-core-ingress) &&
      test "$old_container_id" != "$new_container_id" &&
      podman exec iop-core-ingress \
        test -f /var/tmp/insights-archives/sat47410-persistence-probe.tar.gz
    """

    result = server.run(command)
    assert result.succeeded, result.stderr


def test_ingress_archive_cleanup_timer(server):
    timer = server.service("iop-core-ingress-archive-cleanup.timer")
    assert timer.is_running
    assert timer.is_enabled

    unit = server.file(
        "/etc/systemd/system/iop-core-ingress-archive-cleanup.timer"
    )
    assert unit.exists
    assert "OnCalendar=hourly" in unit.content_string
    assert "Persistent=true" in unit.content_string


def test_ingress_archive_cleanup(server):
    command = """
      volume_path=$(podman volume inspect \
        --format '{{.Mountpoint}}' iop-core-ingress-archives) &&
      expired="$volume_path/sat47410-expired.tar.gz" &&
      recent="$volume_path/sat47410-recent.tar.gz" &&
      trap 'rm -f "$expired" "$recent"' EXIT &&
      touch -d '25 hours ago' "$expired" &&
      touch "$recent" &&
      /usr/local/bin/iop-ingress-archive-cleanup \
        iop-core-ingress-archives 1440 &&
      test ! -e "$expired" &&
      test -e "$recent"
    """

    result = server.run(command)
    assert result.succeeded, result.stderr
