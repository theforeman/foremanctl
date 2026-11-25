#!/usr/bin/env python3
"""Executable DNF test double supplied by the fake_dnf pytest fixture."""

import json
import os
import sys

args = sys.argv[1:]
with open(os.environ['DNF_LOG'], 'a') as log:
    log.write(json.dumps(args) + '\n')
failure = os.environ['DNF_FAILURE']
second_repo = '--repo=copr:copr.fedorainfracloud.org:packit:example-smart_proxy_ansible-200' in args
if (failure == 'enable' and 'enable' in args
        or failure == 'query' and 'repoquery' in args
        or failure == 'query-second' and 'repoquery' in args and second_repo
        or failure == 'upgrade' and 'upgrade' in args):
    sys.exit(1)
if 'repoquery' in args and failure != 'empty' and not (failure == 'empty-second' and second_repo):
    if second_repo:
        print('rubygem-smart_proxy_ansible-0:3.0.0-0.pr200.noarch')
    else:
        print('foreman-proxy-0:5.2.0-0.pr100.noarch')
