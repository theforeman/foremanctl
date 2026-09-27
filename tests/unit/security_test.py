import os

import yaml

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
SECURITY_PLAYBOOK = os.path.abspath(
    os.path.join(TEST_DIR, '..', '..', 'development', 'playbooks', 'security', 'security.yaml')
)


def test_fapolicyd_uses_large_subject_cache():
    with open(SECURITY_PLAYBOOK, 'r') as security_file:
        playbook = yaml.safe_load(security_file)

    fapolicyd_task = next(
        task for task in playbook[0]['tasks'] if task['name'] == 'Setup fapolicyd'
    )

    assert fapolicyd_task['vars']['fapolicyd_subj_cache_size'] == 65353
