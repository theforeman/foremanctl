import urllib.parse

import requests


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
