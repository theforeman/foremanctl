import os

import yaml

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(TEST_DIR, '..', '..', 'src'))
ROLE_TASKS = os.path.join(SRC_DIR, 'roles', 'foreman_proxy', 'tasks', 'main.yaml')
WAIT_FOR_REACHABLE_TASKS = os.path.join(SRC_DIR, 'roles', 'foreman_proxy', 'tasks', 'wait_for_reachable.yaml')
BACKUP_ROLE_TASKS = os.path.join(SRC_DIR, 'roles', 'backup', 'tasks', 'main.yaml')


def _load_tasks():
    with open(ROLE_TASKS, 'r') as task_file:
        return yaml.safe_load(task_file)


def _load_wait_for_reachable_tasks():
    with open(WAIT_FOR_REACHABLE_TASKS, 'r') as task_file:
        return yaml.safe_load(task_file)


def _load_backup_tasks():
    with open(BACKUP_ROLE_TASKS, 'r') as task_file:
        return yaml.safe_load(task_file)


def _load_task(task_name):
    return next(task for task in _load_tasks() if task.get('name') == task_name)


def test_deploy_time_readiness_check_delegates_to_shared_wait_task():
    # The actual command/retry logic lives in the shared wait_for_reachable.yaml
    # task file (also used by the backup role, see
    # test_backup_reuses_shared_wait_for_reachable_task below) so both callers
    # stay in lockstep instead of drifting apart over time.
    task = _load_task("Wait for Foreman Proxy API to be reachable from Foreman")

    assert task["ansible.builtin.include_tasks"] == "wait_for_reachable.yaml"


def test_wait_for_proxy_probes_own_fqdn():
    task = _load_wait_for_reachable_tasks()[0]

    assert task["name"] == "Wait for Foreman Proxy API to be reachable from Foreman"
    assert task["ansible.builtin.include_role"]["name"] == "wait_for_smart_proxy"

    task_vars = task["vars"]
    # Spelled out with ansible_facts['fqdn'] (matching foreman_proxy_name's own
    # default) rather than foreman_proxy_url, since this task is also included
    # from the backup role's play, which doesn't load the foreman_proxy role's
    # defaults. foreman_proxy_registration_url plays no part here: this probe
    # only needs to know the proxy's own real endpoint, not whatever alternate
    # URL it may tell hosts to register through.
    assert task_vars["wait_for_smart_proxy_url"] == "https://{{ ansible_facts['fqdn'] }}:8443"

    when_condition = task["when"] if isinstance(task["when"], list) else [task["when"]]
    assert "enabled_features | has_feature('foreman')" in when_condition
    assert "enabled_features | has_feature('foreman-proxy')" in when_condition


def test_backup_reuses_shared_wait_for_reachable_task():
    # `foremanctl backup` restarts the whole foreman.target (including
    # foreman-proxy) under the bridge-network refactor, so it needs the same
    # Netavark/aardvark-dns reconvergence tolerance the deploy path already
    # has. Reusing the shared task file (rather than duplicating the curl
    # command/retry parameters) keeps both call sites from drifting.
    tasks = _load_backup_tasks()

    def iter_tasks(task_list):
        for task in task_list:
            yield task
            if "block" in task:
                yield from iter_tasks(task["block"])

    backup_tasks = list(iter_tasks(tasks))
    names = [task.get('name') for task in backup_tasks]

    assert 'Wait for Foreman Proxy API to be reachable from Foreman' in names
    wait_task = next(
        task for task in backup_tasks
        if task.get('name') == 'Wait for Foreman Proxy API to be reachable from Foreman'
    )
    included_path = wait_task["ansible.builtin.include_tasks"]
    resolved_path = os.path.normpath(
        os.path.join(SRC_DIR, 'roles', 'backup', 'tasks', included_path)
    )
    assert resolved_path == WAIT_FOR_REACHABLE_TASKS

    start_index = names.index('Start Foreman services')
    wait_index = names.index('Wait for Foreman Proxy API to be reachable from Foreman')
    assert wait_index == start_index + 1, (
        "the proxy-reachability wait must run right after foreman.target is "
        "restarted, before the backup is reported complete"
    )


def test_early_restart_before_readiness_check_is_a_plain_task_not_a_handler_flush():
    # This branch restarts the proxy container before the Foreman-reachability
    # readiness check (needed for bridge networking, unlike master's host
    # networking) via a plain imperative task rather than a notify/flush, so
    # that doing so can never also flush (and thus prematurely fire) the paired
    # "Refresh Foreman Proxy" handler notified from the same feature tasks.
    tasks = _load_tasks()
    names = [task.get('name') for task in tasks]

    assert 'Wait for Foreman Proxy API to be reachable from Foreman' in names
    readiness_index = names.index('Wait for Foreman Proxy API to be reachable from Foreman')

    early_restart = tasks[readiness_index - 1]
    assert early_restart.get('name') == 'Restart Foreman Proxy ahead of registration'
    assert 'notify' not in early_restart
    assert early_restart['ansible.builtin.systemd']['name'] == 'foreman-proxy'

    # No handler flush must occur before registration.
    register_index = names.index('Register Foreman Proxy to Foreman')
    for task in tasks[:register_index]:
        assert 'ansible.builtin.meta' not in task, (
            f"{task.get('name')!r} flushes handlers before registration"
        )


def test_end_of_role_handler_flush_reuses_shared_wait_for_reachable_task():
    # The role's final `flush_handlers` restarts foreman-proxy again (any
    # certs/configs/feature task notifying "Restart Foreman Proxy" earlier in
    # the role - which happens on effectively every deploy run) after the
    # deploy-time readiness check earlier in this file has already run, so it
    # needs its own readiness check immediately afterward before control
    # returns to the caller.
    tasks = _load_tasks()
    names = [task.get('name') for task in tasks]

    flush_indexes = [i for i, task in enumerate(tasks) if 'ansible.builtin.meta' in task]
    assert len(flush_indexes) == 1, "expected exactly one handler flush in the role"
    flush_index = flush_indexes[0]

    assert names.count('Wait for Foreman Proxy API to be reachable from Foreman') == 2, (
        "expected the shared readiness check both before registration and "
        "after the end-of-role handler flush"
    )

    post_flush_wait = tasks[flush_index + 1]
    assert post_flush_wait.get('name') == 'Wait for Foreman Proxy API to be reachable from Foreman'
    assert post_flush_wait['ansible.builtin.include_tasks'] == 'wait_for_reachable.yaml'
