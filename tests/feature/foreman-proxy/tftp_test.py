"""Integration tests for TFTP feature."""

import json
import shlex
import uuid

import pytest
import yaml


@pytest.fixture(scope="module")
def tftp_root(obsah_params):
    """The TFTP root directory the deployment is configured to use."""
    return obsah_params.get("foreman_proxy_tftp_root", "/var/lib/tftpboot")


@pytest.fixture
def tftp_serving_configured_root(server, tftp_root):
    """Make the OS tftp.socket/tftp.service actually serve `tftp_root`.

    The packaged tftp.service hardcodes /var/lib/tftpboot, so a systemd
    drop-in is needed to point in.tftpd at the root the deployment configured.
    """
    assert server.run("dnf install -y tftp-server tftp").succeeded

    was_active = server.run("systemctl is-active --quiet tftp.socket").succeeded
    was_enabled = server.run("systemctl is-enabled --quiet tftp.socket").succeeded

    dropin_dir = "/etc/systemd/system/tftp.service.d"
    dropin = f"{dropin_dir}/zz-foremanctl-test-{uuid.uuid4().hex}.conf"
    quoted_root = tftp_root.replace("\\", "\\\\").replace('"', '\\"').replace("%", "%%")
    unit_override = f'[Service]\nExecStart=\nExecStart=/usr/sbin/in.tftpd -s "{quoted_root}"\n'

    server.check_output(f"mkdir -p {shlex.quote(dropin_dir)}")
    server.check_output(f"tee {shlex.quote(dropin)} > /dev/null <<'UNIT'\n{unit_override}UNIT")
    server.check_output("systemctl daemon-reload")
    server.check_output("systemctl enable --now tftp.socket")
    server.check_output("systemctl restart tftp.socket")

    yield

    server.run(f"rm -f {shlex.quote(dropin)}")
    server.run("systemctl daemon-reload")

    if was_active:
        server.run("systemctl restart tftp.socket")
    else:
        server.run("systemctl stop tftp.socket tftp.service")

    if not was_enabled:
        server.run("systemctl disable tftp.socket")


@pytest.fixture
def tftp_default_file_sandbox(server, tftp_root):
    """Back up and restore pxelinux.cfg/default, yielding a scratch dir for TFTP transfers."""
    default_file = f"{tftp_root}/pxelinux.cfg/default"
    temp_dir = server.check_output("mktemp -d").strip()
    backup_file = f"{temp_dir}/default.backup"
    default_existed = server.run(f"test -f {shlex.quote(default_file)}").succeeded
    if default_existed:
        server.check_output(f"cp {shlex.quote(default_file)} {shlex.quote(backup_file)}")

    yield temp_dir

    if default_existed:
        server.run(f"cp {shlex.quote(backup_file)} {shlex.quote(default_file)}")
    else:
        server.run(f"rm -f {shlex.quote(default_file)}")
    server.run(f"rm -rf {shlex.quote(temp_dir)}")


@pytest.mark.feature("tftp")
def test_tftp_directory_exists(server, tftp_root):
    """Verify deployment creates the configured TFTP root."""
    assert server.run(f"ls -ld {shlex.quote(tftp_root)}").succeeded


@pytest.mark.feature("tftp")
def test_tftp_directory_ownership(server, tftp_root):
    """Verify the Smart Proxy container user owns the TFTP root."""
    uid = server.check_output("podman exec foreman-proxy id -u").strip()
    owner = server.check_output(f"stat -c '%u' {shlex.quote(tftp_root)}").strip()
    assert owner == uid


@pytest.mark.feature("tftp")
def test_tftp_directory_selinux_context(server, tftp_root):
    """Verify the TFTP root has a valid SELinux context."""
    if server.check_output("getenforce").strip() == "Disabled":
        pytest.skip("SELinux is disabled")

    context = server.check_output(f"ls -Zd {shlex.quote(tftp_root)}")
    assert context.strip()
    assert "?" not in context


@pytest.mark.feature("tftp")
def test_tftp_directory_writable_by_container(server, tftp_root):
    """Verify the Smart Proxy container can write to the host TFTP root."""
    container_test_file = "/var/lib/tftpboot/.test-write"
    host_test_file = f"{tftp_root}/.test-write"

    write_and_read = f"echo test-content > {container_test_file} && cat {container_test_file}"
    server.check_output(f"podman exec foreman-proxy sh -c {shlex.quote(write_and_read)}")

    assert server.run(f"test -f {shlex.quote(host_test_file)}").succeeded
    server.run(f"rm -f {shlex.quote(host_test_file)}")


@pytest.mark.feature("tftp")
def test_tftp_settings_configured(server, proxy_v2_features, obsah_params, tftp_root):
    """Verify TFTP settings match the bind mount and configured server name."""
    assert "tftp" in proxy_v2_features
    settings = yaml.safe_load(server.check_output(
        "podman exec foreman-proxy cat /etc/foreman-proxy/settings.d/tftp.yml"
    ))
    mounts = json.loads(server.check_output(
        "podman inspect --format '{{json .Mounts}}' foreman-proxy"
    ))
    tftp_mount = next(mount for mount in mounts if mount["Source"] == tftp_root)

    assert settings[":tftproot"] == tftp_mount["Destination"]
    assert settings.get(":tftp_servername") == obsah_params.get("foreman_proxy_tftp_servername")


@pytest.mark.feature("tftp")
def test_tftp_file_can_be_retrieved_over_tftp(
    server, curl_request, proxy_base_url, tftp_serving_configured_root, tftp_default_file_sandbox
):
    """Verify a Smart Proxy generated file can be retrieved over TFTP."""
    temp_dir = tftp_default_file_sandbox

    response = curl_request(
        "tftp/create_default",
        base_url=proxy_base_url,
        method="POST",
        data="menu=test",
    )
    assert response.succeeded
    assert response.stdout.strip() == "200"

    server.check_output(f"cd {shlex.quote(temp_dir)} && tftp localhost -c get pxelinux.cfg/default")
    downloaded = server.check_output(f"cat {shlex.quote(f'{temp_dir}/default')}")
    assert "test" in downloaded
