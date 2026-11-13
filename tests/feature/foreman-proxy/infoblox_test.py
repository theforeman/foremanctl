import pytest
import yaml


@pytest.mark.feature('dhcp-infoblox')
def test_dhcp_infoblox_settings_enabled(server):
    cmd = server.run(
        "podman secret inspect "
        "--format '{{.SecretData}}' "
        "--showsecret foreman-proxy-settings-d-dhcp-infoblox"
    )
    assert cmd.succeeded

    settings = yaml.safe_load(cmd.stdout)
    assert settings.get(':enabled') is True
    assert settings.get(':record_type') == 'fixedaddress'
    assert settings.get(':dns_view') == 'default'
    assert settings.get(':network_view') == 'default'
    assert settings.get(':used_ips_search_type') == 'record_type'


@pytest.mark.feature('dns-infoblox')
def test_dns_infoblox_settings_enabled(server):
    cmd = server.run(
        "podman secret inspect "
        "--format '{{.SecretData}}' "
        "--showsecret foreman-proxy-settings-d-dns-infoblox"
    )
    assert cmd.succeeded

    settings = yaml.safe_load(cmd.stdout)
    assert settings.get(':enabled') is True
    assert settings.get(':dns_view') == 'default'
