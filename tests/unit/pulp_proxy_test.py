from pathlib import Path

import pytest
import yaml
from ansible.plugins.filter.core import regex_replace
from jinja2 import Environment
from jinja2 import StrictUndefined

SRC = Path(__file__).resolve().parents[2] / 'src'
PULP_ROLE = SRC / 'roles' / 'pulp'


@pytest.mark.parametrize(
    ('deploy', 'api_url', 'expected_url'),
    [
        (True, None, 'https://node.example.test/pulp/api/v3/smart_proxy'),
        (True, 'https://content.example.test/', 'https://content.example.test/pulp/api/v3/smart_proxy'),
        (False, None, 'https://node.example.test/pulp/api/v3/smart_proxy'),
    ],
    ids=['default-deploy', 'configured-api-origin', 'standalone-role'],
)
def test_pulp_proxy_registration_url(deploy, api_url, expected_url):
    variables = yaml.safe_load((PULP_ROLE / 'defaults/main.yaml').read_text())
    if deploy:
        variables.update(yaml.safe_load((SRC / 'vars/base.yaml').read_text()))
    variables['ansible_facts'] = {'fqdn': 'node.example.test'}

    jinja = Environment(undefined=StrictUndefined)
    jinja.filters['regex_replace'] = regex_replace
    variables['pulp_pulp_url'] = api_url or jinja.from_string(variables['pulp_pulp_url']).render(variables)
    if 'pulp_smart_proxy_url' in variables:
        variables['pulp_smart_proxy_url'] = jinja.from_string(
            variables['pulp_smart_proxy_url']
        ).render(variables)

    tasks = yaml.safe_load((PULP_ROLE / 'tasks/main.yaml').read_text())
    registration = next(
        task['theforeman.foreman.smart_proxy'] for task in tasks if 'theforeman.foreman.smart_proxy' in task
    )
    assert jinja.from_string(registration['url']).render(variables) == expected_url
