import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml

WORKFLOW = Path(__file__).resolve().parents[2] / '.github/workflows/test.yml'
CHECK_RESULTS = yaml.safe_load(WORKFLOW.read_text())['jobs']['test-suite']['steps'][0]['run']


@pytest.mark.parametrize('jobs,success', [
    ({'tests': {'result': 'success'}, 'lint': {'result': 'success'}}, True),
    ({'tests': {'result': 'success'}, 'lint': {'result': 'failure'}}, False),
    ({'tests': {'result': 'success'}, 'lint': {'result': 'cancelled'}}, False),
    ({'tests': {'result': 'success'}, 'lint': {'result': 'skipped'}}, False),
    ({'tests': {'result': 'success'}, 'lint': {'result': 'abandoned'}}, False),
    ({'tests': {'result': 'success'}, 'lint': {'result': None}}, False),
    ({'tests': {'result': 'success'}, 'lint': {}}, False),
    ({'tests': {'result': 'success'}, 'lint': {'result': 'future-status'}}, False),
    ({}, False),
    ([], False),
    (None, False),
])
def test_required_ci_results(jobs, success):
    result = subprocess.run(
        ['bash', '-e', '-o', 'pipefail', '-c', CHECK_RESULTS],
        env={**os.environ, 'JOB_RESULTS': json.dumps(jobs)},
        capture_output=True, text=True, check=False,
    )

    assert (result.returncode == 0) == success, result.stdout + result.stderr
    if isinstance(jobs, dict):
        for name, job in jobs.items():
            expected = 'null' if job.get('result') is None else job['result']
            assert f'{name}: {expected}' in result.stdout


def test_malformed_ci_results():
    result = subprocess.run(
        ['bash', '-e', '-o', 'pipefail', '-c', CHECK_RESULTS],
        env={**os.environ, 'JOB_RESULTS': '{invalid json'},
        capture_output=True, text=True, check=False,
    )

    assert result.returncode != 0
