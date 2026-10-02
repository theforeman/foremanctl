import os

import yaml

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
IMAGE_PULL_TASKS = os.path.join(
    TEST_DIR,
    '..',
    '..',
    'src',
    'roles',
    'images',
    'tasks',
    'pull.yaml',
)


def test_image_pull_checks_final_service_state():
    with open(IMAGE_PULL_TASKS, 'r') as tasks_file:
        tasks = yaml.safe_load(tasks_file)

    pull_tasks = tasks[2]['block']
    wait_task = next(
        task for task in pull_tasks if task['name'] == 'Wait for image pulls to complete'
    )
    verify_task = next(
        task
        for task in pull_tasks
        if task['name'] == 'Verify image pull services completed successfully'
    )

    assert wait_task['failed_when'] is False
    assert verify_task['ansible.builtin.command']['argv'] == [
        'systemctl',
        'is-active',
        '{{ item }}-image.service',
    ]
    assert verify_task['until'] == 'images_pull_service_status.rc == 0'
