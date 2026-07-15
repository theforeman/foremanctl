import base64
import json
import os
import textwrap

import pytest
import yaml

PULP_API_SOCKET = '/run/httpd.pulp-api.sock'
PULP_CONTENT_SOCKET = '/run/httpd.pulp-content.sock'

# Run both check --deploy and settings inspection in a single Django startup.
# Encoded as base64 and decoded at runtime to avoid shell quoting issues with
# multi-line Python passed to pulpcore-manager shell -c.
_PULP_MANAGER_SCRIPT = textwrap.dedent("""\
    import json
    from django.conf import settings
    from django.core.management import call_command
    check_ok = True
    try:
        call_command('check', '--deploy', verbosity=0)
    except Exception:
        check_ok = False
    print(json.dumps({
        'check_ok': check_ok,
        'import': sorted(settings.ALLOWED_IMPORT_PATHS),
        'export': sorted(settings.ALLOWED_EXPORT_PATHS),
    }))
""")


def load_pulp_paths_from_parameters():
    test_dir = os.path.dirname(os.path.abspath(__file__))
    foremanctl_dir = os.path.dirname(test_dir)
    params_file = os.path.join(foremanctl_dir, '.var', 'lib', 'foremanctl', 'parameters.yaml')

    if os.path.exists(params_file):
        with open(params_file, 'r') as f:
            params = yaml.safe_load(f)
            import_paths = params.get('pulp_import_paths', [])
            export_paths = params.get('pulp_export_paths', [])

    return import_paths, export_paths


@pytest.fixture(scope="module")
def pulp_status_curl(server, server_fqdn):
    return server.run(f"curl -k -s -w '%{{stderr}}%{{http_code}}' --unix-socket {PULP_API_SOCKET} http://{server_fqdn}/pulp/api/v3/status/")


@pytest.fixture(scope="module")
def pulp_status(pulp_status_curl):
    return json.loads(pulp_status_curl.stdout)


@pytest.fixture(scope="module")
def pulp_import_export_paths():
    return load_pulp_paths_from_parameters()


@pytest.fixture(scope="module")
def pulp_manager_info(server):
    encoded = base64.b64encode(_PULP_MANAGER_SCRIPT.encode()).decode()
    result = server.run(f"podman exec pulp-api pulpcore-manager shell -c \"$(echo '{encoded}' | base64 -d)\"")
    assert result.succeeded
    return json.loads(result.stdout)


def test_pulp_api_service(server):
    pulp_api = server.service("pulp-api")
    assert pulp_api.is_running


def test_pulp_content_service(server):
    pulp_content = server.service("pulp-content")
    assert pulp_content.is_running


def test_pulp_worker_services(server):
    result = server.run("systemctl list-units --all --type=service --no-legend 'pulp-worker@*.service' | awk '{print $1}'")
    worker_services = [s.strip() for s in result.stdout.split('\n') if s.strip()]
    assert len(worker_services) > 0

    for worker_service in worker_services:
        worker = server.service(worker_service)
        assert worker.is_running


def test_pulp_api_socket(server):
    assert server.socket(f"unix://{PULP_API_SOCKET}").is_listening


def test_pulp_content_socket(server):
    assert server.socket(f"unix://{PULP_CONTENT_SOCKET}").is_listening


def test_pulp_status(pulp_status_curl):
    assert pulp_status_curl.succeeded
    assert pulp_status_curl.stderr == '200'


def test_pulp_status_database_connection(pulp_status):
    assert pulp_status['database_connection']['connected']


def test_pulp_status_redis_connection(pulp_status):
    assert pulp_status['redis_connection']['connected']


def test_pulp_status_api(pulp_status):
    assert pulp_status['online_api_apps']


def test_pulp_status_content(pulp_status):
    assert pulp_status['online_content_apps']


def test_pulp_status_workers(pulp_status):
    assert pulp_status['online_workers']


def test_pulp_volumes(server):
    assert server.file("/var/lib/pulp").is_directory


def test_pulp_worker_target(server):
    pulp_worker_target = server.service("pulp-worker.target")
    assert pulp_worker_target.is_running
    assert pulp_worker_target.is_enabled


def test_pulp_manager_check(pulp_manager_info):
    assert pulp_manager_info['check_ok']


def test_pulp_import_export_settings(pulp_manager_info, pulp_import_export_paths):
    expected_import_paths, expected_export_paths = pulp_import_export_paths
    for path in expected_import_paths:
        assert path in pulp_manager_info['import'], f"expected {path} in Pulp ALLOWED_IMPORT_PATHS"
    for path in expected_export_paths:
        assert path in pulp_manager_info['export'], f"expected {path} in Pulp ALLOWED_EXPORT_PATHS"


def test_pulp_import_directories(server, pulp_import_export_paths):
    import_paths, _ = pulp_import_export_paths
    for path in import_paths:
        assert server.file(path).is_directory


def test_pulp_export_directories(server, pulp_import_export_paths):
    _, export_paths = pulp_import_export_paths
    for path in export_paths:
        assert server.file(path).is_directory


@pytest.mark.parametrize("container", ["pulp-api", "pulp-content", "pulp-worker-1"])
def test_pulp_import_export_volume_mounts(server, container, pulp_import_export_paths):
    import_paths, export_paths = pulp_import_export_paths
    result = server.run(f"podman inspect {container} --format '{{{{json .Mounts}}}}'")
    assert result.succeeded
    mounts = json.loads(result.stdout)
    destinations = [mount['Destination'] for mount in mounts]

    for path in import_paths + export_paths:
        mounted = path in destinations or any(path.startswith(d + '/') for d in destinations)
        assert mounted, f"expected {path} to be mounted as a volume in {container}"
