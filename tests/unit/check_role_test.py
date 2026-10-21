import os

import yaml

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(TEST_DIR, '..', '..', 'src'))
ROLES_DIR = os.path.join(SRC_DIR, 'roles')


def role_tasks(check_role):
    role_path = os.path.join(ROLES_DIR, check_role)
    main_yaml = os.path.join(role_path, 'tasks', 'main.yaml')
    with open(main_yaml, 'r') as f:
        return yaml.safe_load(f)


def ensure_role_has_feature_guards(check_role, features, tasks=None):
    """Ensure selected top-level tasks in role run only when all required features are present"""
    all_tasks = role_tasks(check_role)
    filtered_tasks = [t for t in all_tasks if tasks is None or t.get('name') in tasks]
    for task in filtered_tasks:
        assert 'when' in task, f"Task '{task.get('name')}' missing when condition"
        when_condition = task['when']
        when_conditions = when_condition if isinstance(when_condition, list) else [when_condition]
        expected_conditions = [f"enabled_features | has_feature('{feature}')" for feature in features]
        assert set(expected_conditions) <= set(when_conditions), \
            f"Task '{task.get('name')}' missing required feature guard(s)."


def test_check_foreman_api_has_feature_guards():
    ensure_role_has_feature_guards('check_foreman_api', ['tasks', 'katello'], ["Check Foreman tasks status"])


def test_check_foreman_tasks_has_feature_guards():
    ensure_role_has_feature_guards('check_foreman_tasks', ['tasks'])


def ensure_role_uses_foreman_api(check_role, task_name, resource):
    task = next(task for task in role_tasks(check_role) if task.get('name') == task_name)
    module_args = task['theforeman.foreman.resource_info']

    assert module_args['resource'] == resource
    assert module_args['oauth1_consumer_key'] == '{{ health_foreman_oauth_consumer_key }}'
    assert module_args['oauth1_consumer_secret'] == '{{ health_foreman_oauth_consumer_secret }}'
    assert 'community.postgresql.postgresql_query' not in task


def test_check_foreman_tasks_uses_authenticated_api():
    ensure_role_uses_foreman_api('check_foreman_tasks', 'Query Foreman tasks for errors', 'foreman_tasks')


def test_check_duplicate_permissions_uses_authenticated_api():
    ensure_role_uses_foreman_api('check_duplicate_permissions', 'Query for duplicate permissions', 'permissions')
