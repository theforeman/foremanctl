import pytest
import testinfra


@pytest.fixture(scope="module")
def server():
    yield testinfra.get_host('paramiko://quadlet', sudo=True, ssh_config='./.vagrant/ssh-config')
