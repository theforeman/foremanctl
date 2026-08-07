from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

__metaclass__ = type

DOCUMENTATION = '''
---
module: foremanctl_api
short_description: Make authenticated Foreman API calls
description:
  - Make HTTP requests to the Foreman API using apypie from the theforeman.foreman collection.
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
'''

EXAMPLES = '''
- name: Announce to Sources
  foremanctl_api:
    server_url: "https://foreman.example.com"
    oauth1_consumer_key: "{{ foreman_oauth_consumer_key }}"
    oauth1_consumer_secret: "{{ foreman_oauth_consumer_secret }}"
    endpoint: /api/v2/rh_cloud/announce_to_sources
    method: POST
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from ansible_collections.theforeman.foreman.plugins.module_utils._apypie import Api
    HAS_APYPIE = True
except ImportError:
    HAS_APYPIE = False


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
        ),
        supports_check_mode=True,
    )

    if not HAS_APYPIE:
        module.fail_json(msg='The theforeman.foreman collection is required for this module')

    server_url = module.params['server_url']
    endpoint = module.params['endpoint']
    method = module.params['method'].lower()
    body = module.params['body']
    ca_path = module.params['ca_path']

    api = Api(
        uri=server_url,
        oauth1_consumer_key=module.params['oauth1_consumer_key'],
        oauth1_consumer_secret=module.params['oauth1_consumer_secret'],
        verify_ssl=ca_path if ca_path else True,
    )

    url = server_url.rstrip('/') + endpoint

    try:
        response_body = api.http_call(method, endpoint, params=body)
    except Exception as e:
        module.fail_json(msg=f'API call failed: {e}', url=url)

    module.exit_json(
        changed=method != 'get',
        url=url,
        body=response_body,
    )


def main():
    run_module()


if __name__ == '__main__':
    main()
