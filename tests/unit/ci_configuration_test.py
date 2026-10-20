from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[2]


def test_debian_matrix_uses_rpm_client():
    workflow = (PROJECT_ROOT / ".github/workflows/test.yml").read_text()
    vagrantfile = (PROJECT_ROOT / "Vagrantfile").read_text()

    assert "FOREMANCTL_CLIENT_BOX: ${{ matrix.box == 'debian/trixie64' && 'centos/stream10' || matrix.box }}" in workflow
    assert 'ENV.fetch("FOREMANCTL_CLIENT_BOX") { ENV.fetch("FOREMANCTL_BASE_BOX", "centos/stream10") }' in vagrantfile


def test_httpd_ssl_probe_is_posix_compatible():
    httpd_test = (PROJECT_ROOT / "tests/feature/httpd/base_test.py").read_text()

    assert "echo -e 'GET /ssl-error-test" not in httpd_test
    assert "printf 'GET /ssl-error-test" in httpd_test


def test_webhook_listener_supports_traditional_netcat():
    webhook_test = (PROJECT_ROOT / "tests/feature/webhooks/base_test.py").read_text()

    assert "nc -l -p {LISTENER_PORT}" in webhook_test
