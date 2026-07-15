import json

from tests.pulp_helpers import parse_pulp_mounts


def test_parse_pulp_mounts_from_combined_inspect_output():
    output = json.dumps([
        {
            'Name': '/pulp-api',
            'Mounts': [
                {'Destination': '/var/lib/pulp/imports'},
                {'Destination': '/var/lib/pulp/exports'},
            ],
        },
        {
            'Name': '/pulp-content',
            'Mounts': [{'Destination': '/var/lib/pulp'}],
        },
    ])

    assert parse_pulp_mounts(output) == {
        'pulp-api': ['/var/lib/pulp/imports', '/var/lib/pulp/exports'],
        'pulp-content': ['/var/lib/pulp'],
    }


def test_parse_pulp_mounts_accepts_single_container_output():
    output = json.dumps({'Name': 'pulp-worker-1', 'Mounts': []})

    assert parse_pulp_mounts(output) == {'pulp-worker-1': []}
