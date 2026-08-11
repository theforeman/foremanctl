import os

import yaml

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(TEST_DIR, '..', '..', 'src'))
ROLE_DEFAULTS = os.path.join(SRC_DIR, 'roles', 'wait_for_smart_proxy', 'defaults', 'main.yaml')
ROLE_TASKS = os.path.join(SRC_DIR, 'roles', 'wait_for_smart_proxy', 'tasks', 'main.yaml')
IOP_CORE_TASKS = os.path.join(SRC_DIR, 'roles', 'iop_core', 'tasks', 'main.yaml')


def _load_defaults():
    with open(ROLE_DEFAULTS, 'r') as defaults_file:
        return yaml.safe_load(defaults_file)


def _load_task():
    with open(ROLE_TASKS, 'r') as task_file:
        tasks = yaml.safe_load(task_file)
    assert len(tasks) == 1
    return tasks[0]


def _load_iop_core_task(task_name):
    with open(IOP_CORE_TASKS, 'r') as task_file:
        tasks = yaml.safe_load(task_file)
    return next(task for task in tasks if task.get('name') == task_name)


def test_defaults_provide_retry_schedule():
    defaults = _load_defaults()

    assert defaults["wait_for_smart_proxy_retries"] == 30
    assert defaults["wait_for_smart_proxy_delay"] == 5


def test_task_probes_caller_supplied_url_via_foreman():
    task = _load_task()

    assert task["name"] == "Wait for smart proxy API to be reachable from Foreman"
    assert "{{ wait_for_smart_proxy_url }}/v2/features" in task["ansible.builtin.command"]["cmd"]
    assert "podman exec foreman curl" in task["ansible.builtin.command"]["cmd"]

    assert task["changed_when"] is False
    assert task["retries"] == "{{ wait_for_smart_proxy_retries }}"
    assert task["delay"] == "{{ wait_for_smart_proxy_delay }}"
    assert task["until"] == "_wait_for_smart_proxy_result.rc == 0"
    assert task["register"] == "_wait_for_smart_proxy_result"


def test_iop_gateway_delegates_to_shared_wait_role():
    # iop_core's own smart proxy (iop-gateway) needs the same Netavark/
    # aardvark-dns reconvergence tolerance as foreman-proxy, so it reuses the
    # same shared role instead of duplicating the curl/retry logic.
    task = _load_iop_core_task("Wait for IOP Gateway smart proxy API to be reachable from Foreman")

    assert task["ansible.builtin.include_role"]["name"] == "wait_for_smart_proxy"
    assert task["vars"]["wait_for_smart_proxy_url"] == "{{ iop_core_gateway_registration_url }}"
