import json
import os
import shutil
import subprocess
import tempfile

import pytest
import yaml

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(TEST_DIR, '..', '..'))
SRC_DIR = os.path.join(ROOT_DIR, 'src')
ROLES_DIR = os.path.join(SRC_DIR, 'roles')
FLAVORS_DIR = os.path.join(SRC_DIR, 'vars', 'flavors')
PLAYBOOK = os.path.join(ROOT_DIR, 'tests', 'fixtures', 'check_ip_stack', 'run_role.yml')

# Flavors that wire the check into their preflight checks (see src/vars/flavors/).
FLAVORS_WITH_CHECK = ['capsule', 'foreman-proxy-content', 'katello', 'satellite']

RH_SOLUTION = 'access.redhat.com/solutions/5045841'

# Loopback facts with both loopback addresses present, the common healthy case.
LO_BOTH = {'ipv4': {'address': '127.0.0.1'}, 'ipv6': [{'address': '::1'}]}
# Loopback with IPv4 only (e.g. ::1 removed via net.ipv6.conf.lo.disable_ipv6=1).
LO_IPV4_ONLY = {'ipv4': {'address': '127.0.0.1'}, 'ipv6': []}

GW4 = {'gateway': '10.0.0.1', 'interface': 'eth0'}
GW6 = {'gateway': 'fe80::1', 'interface': 'eth0'}


def ipv6_facts(default_ipv4, default_ipv6, lo):
    return {'default_ipv4': default_ipv4, 'default_ipv6': default_ipv6, 'lo': lo}


# (id, ansible_facts, should_pass). The first three mirror the acceptance VMs
# from the issue: (a) IPv6 disabled, (b) IPv6-only, (c) IPv6-only without ::1.
SCENARIOS = [
    # (a) IPv6 disabled: IPv4 is complete -> pass.
    ('ipv6_disabled_ipv4_complete', ipv6_facts(GW4, {}, LO_IPV4_ONLY), True),
    # (b) IPv6-only: IPv6 is complete -> pass.
    ('ipv6_only_complete', ipv6_facts({}, GW6, LO_BOTH), True),
    # (c) IPv6-only with ::1 removed: v6 has gateway but no loopback, v4 has
    # loopback but no gateway -> neither complete -> fail.
    ('ipv6_only_without_loopback', ipv6_facts({}, GW6, LO_IPV4_ONLY), False),
    # Dual stack: both complete -> pass.
    ('dual_stack', ipv6_facts(GW4, GW6, LO_BOTH), True),
    # No default gateway at all, loopbacks present -> fail.
    ('no_gateway', ipv6_facts({}, {}, LO_BOTH), False),
    # IPv4 gateway but no IPv4 loopback, no IPv6 -> fail.
    ('ipv4_gateway_without_loopback', ipv6_facts(GW4, {}, {'ipv4': {}, 'ipv6': []}), False),
]


requires_ansible = pytest.mark.skipif(
    shutil.which('ansible-playbook') is None,
    reason='ansible-core is required to exercise the check_ip_stack role',
)


def run_check(ansible_facts, enabled_features=None):
    """Run the check_ip_stack role with mocked facts and return the process result."""
    extra_vars = {'ansible_facts': ansible_facts, 'enabled_features': enabled_features or []}
    env = os.environ.copy()
    env.update({
        'ANSIBLE_ROLES_PATH': ROLES_DIR,
        'ANSIBLE_FILTER_PLUGINS': os.path.join(SRC_DIR, 'filter_plugins'),
        'ANSIBLE_STDOUT_CALLBACK': 'default',
        'ANSIBLE_LOAD_CALLBACK_PLUGINS': 'false',
        'ANSIBLE_LOCALHOST_WARNING': 'false',
        'ANSIBLE_INVENTORY_UNPARSED_WARNING': 'false',
        'ANSIBLE_RETRY_FILES_ENABLED': 'false',
        'ANSIBLE_NOCOWS': '1',
        'ANSIBLE_FORCE_COLOR': '0',
    })
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as handle:
        json.dump(extra_vars, handle)
        vars_file = handle.name
    try:
        return subprocess.run(
            ['ansible-playbook', '-i', 'localhost,', PLAYBOOK, '-e', f'@{vars_file}'],
            cwd=ROOT_DIR,
            env=env,
            text=True,
            capture_output=True,
        )
    finally:
        os.unlink(vars_file)


@requires_ansible
@pytest.mark.parametrize('scenario_id, ansible_facts, should_pass',
                         SCENARIOS, ids=[s[0] for s in SCENARIOS])
def test_check_ip_stack_scenarios(scenario_id, ansible_facts, should_pass):
    result = run_check(ansible_facts)
    if should_pass:
        assert result.returncode == 0, f'expected check to pass:\n{result.stdout}\n{result.stderr}'
    else:
        assert result.returncode != 0, f'expected check to fail:\n{result.stdout}\n{result.stderr}'


@requires_ansible
def test_failure_includes_per_family_diagnostics():
    # The (c) scenario: message should report each family's gateway/loopback state.
    result = run_check(ipv6_facts({}, GW6, LO_IPV4_ONLY))
    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert 'IPv4: default gateway missing, loopback 127.0.0.1 present' in output
    assert 'IPv6: default gateway present, loopback ::1 missing' in output


@requires_ansible
def test_satellite_failure_includes_solution_link():
    facts = ipv6_facts({}, GW6, LO_IPV4_ONLY)
    result = run_check(facts, enabled_features=['theme-satellite'])
    assert result.returncode != 0
    assert RH_SOLUTION in result.stdout + result.stderr


@requires_ansible
def test_non_satellite_failure_omits_solution_link():
    facts = ipv6_facts({}, GW6, LO_IPV4_ONLY)
    result = run_check(facts, enabled_features=[])
    assert result.returncode != 0
    assert RH_SOLUTION not in result.stdout + result.stderr


@pytest.mark.parametrize('flavor', FLAVORS_WITH_CHECK)
def test_check_wired_into_flavor(flavor):
    # This static check runs even without ansible-core installed.
    with open(os.path.join(FLAVORS_DIR, f'{flavor}.yml'), 'r') as flavor_file:
        flavor_vars = yaml.safe_load(flavor_file)
    assert 'check_ip_stack' in flavor_vars['checks_to_execute']
