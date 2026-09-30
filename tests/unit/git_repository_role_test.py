import os

import yaml

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(TEST_DIR, '..', '..'))
ROLE_DIR = os.path.join(PROJECT_DIR, 'development', 'roles', 'git_repository')


def test_unpinned_repository_preserves_existing_checkout():
    with open(os.path.join(ROLE_DIR, 'tasks', 'main.yml'), 'r') as tasks_file:
        tasks = yaml.safe_load(tasks_file)

    clone_task = next(task for task in tasks if task.get('name') == 'Clone repository')
    git_options = clone_task['ansible.builtin.git']

    assert git_options['version'] == '{{ git_repository_revision }}'
    assert git_options['update'] == "{{ git_repository_revision != 'HEAD' }}"


def test_default_revision_preserves_developer_checkout():
    with open(os.path.join(ROLE_DIR, 'defaults', 'main.yml'), 'r') as defaults_file:
        defaults = yaml.safe_load(defaults_file)

    assert defaults['git_repository_revision'] == 'HEAD'
