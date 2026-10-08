import os

import pytest
import yaml

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
TUNING_DIR = os.path.abspath(os.path.join(TEST_DIR, '..', '..', 'src', 'vars', 'tuning'))


def load_tuning_profile(name):
    with open(os.path.join(TUNING_DIR, f'{name}.yml'), 'r') as tuning_file:
        return yaml.safe_load(tuning_file)


@pytest.fixture
def development_tuning():
    return load_tuning_profile('development')


def test_development_tuning_limits_puma_workers(development_tuning):
    assert development_tuning['foreman_puma_workers'] == 2


def test_development_tuning_limits_pulp_workers(development_tuning):
    assert development_tuning['pulp_worker_count'] == 2
    assert development_tuning['pulp_content_service_worker_count'] == 2
    assert development_tuning['pulp_api_service_worker_count'] == 2


def test_development_tuning_limits_candlepin_heap(development_tuning):
    assert development_tuning['candlepin_java_opts_xms'] == '512m'
    assert development_tuning['candlepin_java_opts_xmx'] == '2g'
