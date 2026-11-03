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
  - A successful task does not guarantee registration actually happened (e.g. the organization is skipped if its Candlepin identity cert isn't ready yet). Check the returned C(registered) value, retrying the task (e.g. with C(until)) when it is C(false).
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
  register: announce_result
  until: announce_result.registered
  retries: 5
  delay: 15
'''

RETURN = '''
task:
  description: The completed Foreman task.
  type: dict
  returned: always
status:
  description: The task's human-readable per-organization outcome (e.g. "Registered ..." or "Skipped (no manifest) ...").
  type: str
  returned: always
registered:
  description: Whether the organization was actually registered with Red Hat Sources, as opposed to skipped or failed without raising.
  type: bool
  returned: always
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

    # The task can report result=success without having registered anything: if the
    # organization's Candlepin identity cert isn't available yet (e.g. this ran very
    # early in a deploy), CloudConnectorAnnounceTask skips the org instead of raising,
    # recording that only in output.status. Surface it as `registered` so callers can
    # retry (e.g. via `until:`) instead of trusting a successful task as proof.
    status = (task or {}).get('output', {}).get('status', '') or ''
    registered = bool(status) and 'Skipped' not in status and 'Failed' not in status

    module.exit_json(changed=True, task=task, status=status, registered=registered)


def main():
    run_module()


if __name__ == '__main__':
    main()
