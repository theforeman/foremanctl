from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

__metaclass__ = type

DOCUMENTATION = '''
---
module: foremanctl_announce_to_sources
short_description: Register this Foreman instance in Red Hat Sources
description:
  - Calls the Foreman API to announce this instance to Red Hat Sources, a prerequisite for cloud-initiated remediations via Cloud Connector.
  - Waits for the resulting Foreman task to complete and fails if the task does not succeed.
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
  ca_path:
    description: Path to CA certificate for SSL verification
    type: str
  instance_id:
    description: RHC instance ID to register with Red Hat Sources. Also stored as the rhc_instance_id Foreman setting.
    required: true
    type: str
'''

EXAMPLES = '''
- name: Announce to Sources
  foremanctl_announce_to_sources:
    server_url: "https://foreman.example.com"
    oauth1_consumer_key: "{{ foreman_oauth_consumer_key }}"
    oauth1_consumer_secret: "{{ foreman_oauth_consumer_secret }}"
    instance_id: "{{ cloud_connector_cert_info.subject.commonName }}"
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from ansible_collections.theforeman.foreman.plugins.module_utils._apypie import ForemanApi
    from ansible_collections.theforeman.foreman.plugins.module_utils._apypie import ForemanApiException
    HAS_APYPIE = True
except ImportError:
    HAS_APYPIE = False


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(required=True, type='str'),
            oauth1_consumer_key=dict(required=True, type='str'),
            oauth1_consumer_secret=dict(required=True, type='str', no_log=True),
            ca_path=dict(type='str'),
            instance_id=dict(required=True, type='str'),
        ),
        supports_check_mode=True,
    )

    if not HAS_APYPIE:
        module.fail_json(msg='The theforeman.foreman collection is required for this module')

    ca_path = module.params['ca_path']

    api = ForemanApi(
        uri=module.params['server_url'],
        oauth1_consumer_key=module.params['oauth1_consumer_key'],
        oauth1_consumer_secret=module.params['oauth1_consumer_secret'],
        verify_ssl=ca_path if ca_path else True,
    )

    try:
        # apypie caches the apidoc on disk, keyed by an Apipie-Checksum header that
        # doesn't reliably change when a plugin adds/renames an action (observed:
        # the checksum stayed identical after announce_to_sources was added to the
        # rh_cloud inventory controller). Force a fresh fetch so a stale on-disk
        # apidoc from before this feature was installed can't hide the new action.
        api.clean_cache()

        # The announce_to_sources action lives on the rh_cloud "inventory" resource.
        # It returns its Foreman task wrapped as {"task": {...}}, so resource_action's
        # own task auto-detection doesn't fire; wait for the task explicitly.
        result = api.resource_action('inventory', 'announce_to_sources', {'instance_id': module.params['instance_id']})
        task = result.get('task') if isinstance(result, dict) else None
        if task:
            task = api.wait_for_task(task)
    except ForemanApiException as e:
        module.fail_json(msg=f'Announce to Sources failed: {e}')

    module.exit_json(changed=True, task=task)


def main():
    run_module()


if __name__ == '__main__':
    main()
