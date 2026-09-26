from pathlib import Path

import yaml

WORKFLOW_FILE = Path(__file__).parents[2] / '.github' / 'workflows' / 'test.yml'


def test_content_proxy_ci_memory_allocation():
    with WORKFLOW_FILE.open() as workflow_file:
        workflow = yaml.safe_load(workflow_file)

    environment = workflow['jobs']['foreman-proxy-content-tests']['env']
    quadlet_memory = int(environment['FOREMANCTL_QUADLET_MEMORY'])
    proxy_memory = int(environment['FOREMANCTL_PROXY_MEMORY'])

    assert quadlet_memory >= 10240
    assert proxy_memory >= 4096
    assert quadlet_memory + proxy_memory <= 15360
