import os

import yaml

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.abspath(os.path.join(TEST_DIR, '..', '..'))
BACKUP_MAIN = os.path.join(REPO_DIR, 'src', 'roles', 'backup', 'tasks', 'main.yaml')


def _load_task(task_name):
    with open(BACKUP_MAIN, 'r') as task_file:
        tasks = yaml.safe_load(task_file)

    def iter_tasks(task_list):
        for task in task_list:
            yield task
            if "block" in task:
                yield from iter_tasks(task["block"])

    return next(task for task in iter_tasks(tasks) if task.get('name') == task_name)


def test_backup_selects_socket_host_for_internal_database():
    task = _load_task("Select database access host for backup")

    actual = " ".join(task["ansible.builtin.set_fact"]["backup_database_host"].split())
    expected = (
        "{{ (backup_database_mode == 'internal') | ternary((postgresql_socket_dir | "
        "default('/var/run/postgresql')), database_host) }}"
    )

    assert actual == expected


def test_backup_readiness_uses_selected_database_host():
    task = _load_task("Wait for PostgreSQL readiness")

    assert task["ansible.builtin.command"]["cmd"] == (
        "pg_isready -h {{ backup_database_host }} -p {{ database_port }}"
    )


def test_backup_database_dump_config_uses_selected_database_host():
    task = _load_task("Build database backup configuration")

    assert task["vars"]["db_entry"]["host"] == "{{ backup_database_host }}"
