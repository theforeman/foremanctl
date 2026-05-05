import json
import os
import pytest
import yaml

FOREMAN_PROXY_PORT = 8443
BMC_CONFIG = "/etc/foreman-proxy/settings.d/bmc.yml"

test_dir = os.path.dirname(os.path.abspath(__file__))                                                                                                                                                                                                                        
foremanctl_dir = os.path.dirname(test_dir)                                                                                                                                                                                                                                   
params_file = os.path.join(foremanctl_dir, '.var', 'lib', 'foremanctl', 'parameters.yaml')

def is_bmc_enabled():                                                                                                                                                                                                                                                            
    if os.path.exists(params_file):
        with open(params_file, 'r') as f:
            params = yaml.safe_load(f)
            features = params.get('features', [])
            if isinstance(features, str):
                features = features.split()
            return 'bmc' in features
    return False

def get_bmc_provider():                                                                                                                                                                                                                                                          
    if os.path.exists(params_file):
        with open(params_file, 'r') as f:
            params = yaml.safe_load(f)
            return params.get('foreman_proxy_bmc_default_provider', 'ipmitool')
    return 'ipmitool'

@pytest.mark.skipif("not is_bmc_enabled()")
def test_bmc_feature_in_proxy(server, certificates, server_fqdn):
    cmd = server.run(f"curl --cacert {certificates['ca_certificate']} --silent https://{server_fqdn}:{FOREMAN_PROXY_PORT}/features")
    assert cmd.succeeded
    features = json.loads(cmd.stdout)
    assert "bmc" in features

@pytest.mark.skipif("not is_bmc_enabled()")
def test_bmc_default_provider(server):
    cmd = server.run(f"podman exec foreman-proxy grep ':bmc_default_provider:' {BMC_CONFIG}")
    assert cmd.succeeded
    assert get_bmc_provider() in cmd.stdout
