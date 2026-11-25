"""Validate and plan a deployment using Packit PR images."""

import contextlib
import io
import re
import shlex
from pathlib import Path
from urllib.parse import urlsplit

import obsah
from ansible.errors import AnsibleFilterError
from obsah.constraints import validate_constraints


def packit_stack_plan(deployment, foreman_urls, proxy_urls, deploy_args):
    """Return the target, grouped COPR projects, and validated deployment arguments."""
    if deployment not in ('server', 'proxy'):
        raise AnsibleFilterError('Deployment must be server or proxy')
    if not foreman_urls and not proxy_urls:
        raise AnsibleFilterError('Supply at least one --foreman-pr-url or --proxy-pr-url')
    if deployment == 'proxy' and foreman_urls:
        raise AnsibleFilterError('Standalone proxy deployments cannot include Foreman PRs')

    projects = {}
    for component, urls in (('foreman', foreman_urls), ('foreman-proxy', proxy_urls)):
        if not urls:
            continue
        projects[component] = []
        for url in urls:
            parsed = urlsplit(url)
            match = re.fullmatch(r'/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)/pull/([0-9]+)/?', parsed.path)
            if parsed.scheme != 'https' or parsed.hostname != 'github.com' or not match:
                raise AnsibleFilterError(f'Invalid GitHub pull request URL: {url}')
            project = '-'.join(match.groups())
            if project not in projects[component]:
                projects[component].append(project)

    try:
        arguments = shlex.split(deploy_args)
    except ValueError as exc:
        raise AnsibleFilterError(f'Invalid --deploy-args: {exc}') from exc
    arguments = ['--flavor', 'foreman-proxy-content' if deployment == 'proxy' else 'katello'] + arguments
    if deployment == 'server' and proxy_urls:
        arguments += ['--add-feature', 'foreman-proxy']

    command = 'deploy-proxy' if deployment == 'proxy' else 'deploy'
    root = Path(__file__).resolve().parents[2]

    class DeploymentConfig(obsah.ApplicationConfig):
        @staticmethod
        def name():
            return 'foremanctl'

        @staticmethod
        def playbooks_path():
            return str(root / 'src/playbooks')

        @staticmethod
        def persist_params():
            return True

        @staticmethod
        def allow_extra_vars():
            return False

    errors = io.StringIO()
    with contextlib.redirect_stderr(errors):
        parser = obsah.obsah_argument_parser(DeploymentConfig, targets=[])
        try:
            args = parser.parse_args([command] + arguments)
            args = obsah.reset_args(DeploymentConfig, args.playbook.metadata, args)
        except SystemExit as exc:
            raise AnsibleFilterError('Invalid --deploy-args: ' + errors.getvalue().strip()) from exc
    constraint_errors = validate_constraints(args.playbook.metadata, args)
    if constraint_errors:
        raise AnsibleFilterError('Invalid --deploy-args: ' + '; '.join(constraint_errors))
    if getattr(args, 'air_gapped', False):
        raise AnsibleFilterError('Packit image builds require registry access; --air-gapped is not supported')

    return {
        'target': 'proxy' if deployment == 'proxy' else 'quadlet',
        'command': command,
        'arguments': arguments,
        'projects': projects,
    }


class FilterModule:
    def filters(self):
        return {'packit_stack_plan': packit_stack_plan}
