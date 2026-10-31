import os

import yaml

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(TEST_DIR, '..', '..', 'src'))
ROLES_DIR = os.path.join(SRC_DIR, 'roles')


def ensure_role_has_feature_guards(check_role, features, tasks=None):
    """Ensure selected top-level tasks in role run only when all required features are present"""
    role_path = os.path.join(ROLES_DIR, check_role)
    main_yaml = os.path.join(role_path, 'tasks', 'main.yaml')
    with open(main_yaml, 'r') as f:
        all_tasks = yaml.safe_load(f)
    filtered_tasks = [t for t in all_tasks if tasks is None or t.get('name') in tasks]
    for task in filtered_tasks:
        assert 'when' in task, f"Task '{task.get('name')}' missing when condition"
        when_condition = task['when']
        when_conditions = when_condition if isinstance(when_condition, list) else [when_condition]
        expected_conditions = [f"enabled_features | has_feature('{feature}')" for feature in features]
        assert set(expected_conditions) <= set(when_conditions), \
            f"Task '{task.get('name')}' missing required feature guard(s)."


def test_check_hostname_rejects_loopback_entries_from_etc_hosts():
    role_path = os.path.join(ROLES_DIR, 'check_hostname', 'tasks', 'main.yaml')
    with open(role_path, 'r') as f:
        tasks = yaml.safe_load(f)

    getent_task = next(task for task in tasks if task.get('ansible.builtin.getent'))
    assert getent_task['ansible.builtin.getent'] == {
        'database': 'ahosts',
        'key': "{{ ansible_facts['fqdn'] }}",
        'service': 'files',
        'fail_key': False,
    }

    loopback_assertion = next(
        task for task in tasks
        if task.get('name') == 'Assert FQDN does not resolve to a loopback address in /etc/hosts'
    )
    conditions = loopback_assertion['ansible.builtin.assert']['that']
    expected_condition = (
        '(_check_hostname_hosts.ansible_facts.getent_ahosts.keys() '
        '| loopback_addresses | length) == 0'
    )
    assert expected_condition in conditions


def test_check_foreman_api_has_feature_guards():
    ensure_role_has_feature_guards('check_foreman_api', ['tasks', 'katello'], ["Check Foreman tasks status"])


def test_check_foreman_tasks_has_feature_guards():
    ensure_role_has_feature_guards('check_foreman_tasks', ['tasks'])


def test_backup_foreman_task_checks_have_feature_guards():
    preflight_yaml = os.path.join(ROLES_DIR, 'backup', 'tasks', 'preflight.yaml')
    with open(preflight_yaml, 'r') as f:
        all_tasks = yaml.safe_load(f)

    foreman_tasks = [task for task in all_tasks if 'Foreman' in task.get('name', '')]
    assert len(foreman_tasks) == 4
    for task in foreman_tasks:
        when_condition = task.get('when', [])
        when_conditions = when_condition if isinstance(when_condition, list) else [when_condition]
        assert "enabled_features | has_feature('foreman')" in when_conditions, \
            f"Task '{task.get('name')}' must only run on a Foreman server."
