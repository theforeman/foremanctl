import os

import yaml

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
TUNING_DIR = os.path.abspath(os.path.join(TEST_DIR, '..', '..', 'src', 'vars', 'tuning'))


def test_development_tuning_limits_candlepin_heap():
    with open(os.path.join(TUNING_DIR, 'development.yml'), 'r') as tuning_file:
        tuning = yaml.safe_load(tuning_file)

    assert tuning['candlepin_java_opts_xms'] == '512m'
    assert tuning['candlepin_java_opts_xmx'] == '2g'
