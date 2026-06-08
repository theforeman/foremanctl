#!/usr/bin/env python3

import argparse
import json
import re
import subprocess
import sys

import yaml


def parse_args():
    parser = argparse.ArgumentParser(description="Broker inventory script")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list', action='store_true')
    group.add_argument('--host')
    return parser.parse_args()


def parse_broker_inventory(output):
    # Broker emits ruamel-specific tags (e.g. !NetworkType) that safe_load rejects.
    output = re.sub(r'!\w+\s+', '', output)
    inventory = yaml.safe_load(output)
    if not inventory:
        return
    return inventory.values()


def get_running_hosts():
    cmd = ["broker", "inventory", "--details"]

    try:
        output = subprocess.check_output(
            cmd, universal_newlines=True, stderr=subprocess.DEVNULL
        ).rstrip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return

    try:
        return parse_broker_inventory(output)
    except yaml.YAMLError:
        return


def list_running_hosts():
    hosts = get_running_hosts()
    variables = dict(get_configs(hosts))

    return {
        "_meta": {
            "hostvars": variables
        },
        "all": {
            "hosts": list(variables.keys())
        },
    }


def get_configs(hosts):
    if not hosts:
        return

    for host in hosts:
        if not host.get('hostname') or not host.get('ip'):
            continue

        details = {
            'ansible_host': host['ip'],
            'ansible_port': '22',
            'ansible_user': 'root'
        }
        yield host['hostname'], details


def main():
    args = parse_args()
    hosts = list_running_hosts()

    if args.list:
        json.dump(hosts, sys.stdout)
    elif args.host:
        details = hosts['_meta']['hostvars'].get(args.host, {})
        json.dump(details, sys.stdout)


if __name__ == '__main__':
    main()
