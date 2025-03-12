import urllib.parse

import requests
import time


def _repo_url(repo, ssh_config):
    return urllib.parse.urlunparse(urllib.parse.urlparse(repo['full_path'])._replace(netloc=ssh_config['hostname']))


def test_foreman_organization(organization):
    assert organization

def test_foreman_product(product):
    assert product

def test_foreman_yum_repository(yum_repository, foremanapi, ssh_config):
    assert yum_repository
    foremanapi.resource_action('repositories', 'sync', {'id': yum_repository['id']})
    repo_url = _repo_url(yum_repository, ssh_config)
    assert requests.get(f'{repo_url}/repodata/repomd.xml', verify=False)
    assert requests.get(f'{repo_url}/Packages/b/bear-4.1-1.noarch.rpm', verify=False)


def test_foreman_file_repository(file_repository, foremanapi, ssh_config):
    assert file_repository
    foremanapi.resource_action('repositories', 'sync', {'id': file_repository['id']})
    repo_url = _repo_url(file_repository, ssh_config)
    assert requests.get(f'{repo_url}/1.iso', verify=False)


def test_foreman_container_repository(container_repository, foremanapi, ssh_config):
    assert container_repository
    foremanapi.resource_action('repositories', 'sync', {'id': container_repository['id']})


def test_foreman_lifecycle_environment(lifecycle_environment):
    assert lifecycle_environment


def test_foreman_content_view(content_view, yum_repository, foremanapi):
    time.sleep(10)
    assert content_view
    foremanapi.update('content_views', {'id': content_view['id'], 'repository_ids': [yum_repository['id']]})
    foremanapi.resource_action('content_views', 'publish', {'id': content_view['id']})
    # do something with the published view
    versions = foremanapi.list('content_view_versions', params={'content_view_id': content_view['id']})
    for version in versions:
        current_environment_ids = {environment['id'] for environment in version['environments']}
        for environment_id in current_environment_ids:
            foremanapi.resource_action('content_views', 'remove_from_environment', params={'id': content_view['id'], 'environment_id': environment_id})
        foremanapi.delete('content_view_versions', version)
