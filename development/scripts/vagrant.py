#!/usr/bin/env python3
# Adapted from Mark Mandel's implementation
# https://github.com/ansible/ansible/blob/devel/plugins/inventory/vagrant.py
import argparse
import json
import subprocess
import sys
import yaml

from collections import defaultdict


def parse_args():
    parser = argparse.ArgumentParser(description="Vagrant inventory script")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list', action='store_true')
    group.add_argument('--yaml', action='store_true')
    group.add_argument('--host')
    return parser.parse_args()


def get_running_hosts():
    try:
        subprocess.check_call(["which", "vagrant"], stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return

    cmd = "vagrant status --machine-readable"
    status = subprocess.check_output(cmd.split(), universal_newlines=True).rstrip()

    for line in status.split('\n'):
        if len(line.split(',')) == 4:
            (_, host, key, value) = line.split(',')
        else:
            (_, host, key, value, _) = line.split(',')

        if key == 'state' and value in ('active', 'running'):
            yield host


def list_running_hosts():
    hosts = list(get_running_hosts())
    variables = dict(get_configs(hosts))

    return {
        "_meta": {
            "hostvars": variables,
        },
        "all": {
            "hosts": hosts,
        },
    }


def get_ssh_configs(hosts):
    cmd = ['vagrant', 'ssh-config'] + hosts
    try:
        output = subprocess.check_output(cmd, universal_newlines=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return None

    config = defaultdict(dict)
    host = None

    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        key, value = line.split(None, 1)
        if key == 'Host':
            host = value
        elif host:
            config[host][key.lower()] = value

    return config


def get_host_ssh_config(config, host):
    ssh = config.get(host)
    return {'ansible_host': ssh['hostname'],
            'ansible_port': ssh['port'],
            'ansible_user': ssh['user'],
            'ansible_ssh_private_key_file': ssh['identityfile']}


def get_configs(hosts):
    if not hosts:
        return

    ssh_configs = get_ssh_configs(hosts)

    for host in hosts:
        details = {}
        if ssh_configs:
            details.update(get_host_ssh_config(ssh_configs, host))
        yield host, details


def format_inventory():
    hosts = list(get_running_hosts())
    variables = dict(get_configs(hosts))

    return {
        "all": {
            "hosts": variables,
        },
    }


def main():
    args = parse_args()
    if args.list:
        hosts = list_running_hosts()
        json.dump(hosts, sys.stdout)
    elif args.yaml:
        inventory = format_inventory()
        print(yaml.dump(inventory))
    elif args.host:
        details = dict(get_configs([args.host]))
        json.dump(details[args.host], sys.stdout)


if __name__ == '__main__':
    main()
