from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

__metaclass__ = type

DOCUMENTATION = '''
---
module: foremanctl_api
short_description: Make authenticated Foreman API calls using OAuth1
description:
  - Make HTTP requests to the Foreman API using OAuth1 authentication.
  - Useful for one-off API calls where no dedicated Foreman Ansible Module exists.
options:
  server_url:
    description: Foreman server URL
    required: true
    type: str
  oauth1_consumer_key:
    description: OAuth1 consumer key
    required: true
    type: str
  oauth1_consumer_secret:
    description: OAuth1 consumer secret
    required: true
    type: str
    no_log: true
  endpoint:
    description: API endpoint path (e.g. /api/v2/rh_cloud/announce_to_sources)
    required: true
    type: str
  method:
    description: HTTP method
    default: GET
    type: str
    choices: [GET, POST, PUT, DELETE, PATCH]
  body:
    description: Request body (sent as JSON)
    type: dict
  ca_path:
    description: Path to CA certificate for SSL verification
    type: str
  status_code:
    description: List of acceptable HTTP status codes
    default: [200]
    type: list
    elements: int
'''

EXAMPLES = '''
- name: Announce to Sources
  foremanctl_api:
    server_url: "https://foreman.example.com"
    oauth1_consumer_key: "{{ foreman_oauth_consumer_key }}"
    oauth1_consumer_secret: "{{ foreman_oauth_consumer_secret }}"
    endpoint: /api/v2/rh_cloud/announce_to_sources
    method: POST
    status_code: [200, 201]
'''

import json

from ansible.module_utils.basic import AnsibleModule

try:
    import requests
    from requests_oauthlib import OAuth1
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(required=True, type='str'),
            oauth1_consumer_key=dict(required=True, type='str'),
            oauth1_consumer_secret=dict(required=True, type='str', no_log=True),
            endpoint=dict(required=True, type='str'),
            method=dict(default='GET', type='str', choices=['GET', 'POST', 'PUT', 'DELETE', 'PATCH']),
            body=dict(type='dict'),
            ca_path=dict(type='str'),
            status_code=dict(default=[200], type='list', elements='int'),
        ),
        supports_check_mode=True,
    )

    if not HAS_DEPS:
        module.fail_json(msg='requests and requests-oauthlib are required for this module')

    url = module.params['server_url'].rstrip('/') + module.params['endpoint']
    method = module.params['method']
    body = module.params['body']
    ca_path = module.params['ca_path']
    expected_status = module.params['status_code']

    auth = OAuth1(
        module.params['oauth1_consumer_key'],
        client_secret=module.params['oauth1_consumer_secret'],
    )

    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.request(
            method=method,
            url=url,
            auth=auth,
            headers=headers,
            json=body,
            verify=ca_path if ca_path else True,
        )
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f'Request failed: {e}', url=url)

    response_body = None
    try:
        response_body = response.json()
    except (json.JSONDecodeError, ValueError):
        response_body = response.text

    if response.status_code not in expected_status:
        module.fail_json(
            msg=f'Unexpected status code {response.status_code} (expected {expected_status})',
            url=url,
            status_code=response.status_code,
            body=response_body,
        )

    module.exit_json(
        changed=method != 'GET',
        url=url,
        status_code=response.status_code,
        body=response_body,
    )


def main():
    run_module()


if __name__ == '__main__':
    main()
