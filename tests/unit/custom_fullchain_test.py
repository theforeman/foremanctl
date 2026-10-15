"""Exercise custom-certificate tasks locally; no deployed VM is needed."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

TASKS = Path(__file__).resolve().parents[2] / "src/roles/certificates/tasks/custom.yml"


def test_custom_chain_redeploy_and_auth_bundle_ca_reuse(tmp_path):
    if not shutil.which("ansible-playbook"):
        pytest.skip("ansible-playbook is required")
    certs = tmp_path / "certs"
    certs.mkdir()
    leaf = tmp_path / "leaf.pem"
    leaf.write_text("LEAF")
    key = tmp_path / "key.pem"
    key.write_text("KEY")
    ca = tmp_path / "ca.pem"
    ca.write_text("INTERMEDIATE\nROOT\n")
    output = certs / "proxy.example.com.crt"
    variables = {
        "ansible_remote_tmp": str(tmp_path / "remote-tmp"),
        "certificates_hostname": "proxy.example.com",
        "certificates_custom_server_certificate": str(leaf),
        "certificates_custom_server_key": str(key),
        "certificates_custom_server_ca_certificate": str(ca),
        "certificates_ca_directory_certs": str(certs),
        "certificates_output_directory_certs": str(certs),
        "certificates_output_directory_keys": str(tmp_path),
    }

    def deploy():
        playbook = tmp_path / "play.yml"
        playbook.write_text(
            yaml.safe_dump([
                {
                    "hosts": "localhost",
                    "gather_facts": False,
                    "vars": variables,
                    "tasks": [{"ansible.builtin.include_tasks": str(TASKS)}],
                }
            ])
        )
        result = subprocess.run(
            ["ansible-playbook", "-i", "localhost,", "-c", "local", str(playbook)],
            env=os.environ | {"ANSIBLE_LOCAL_TEMP": str(tmp_path / "ansible")},
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout

    deploy()
    assert output.read_text() == "LEAF\nINTERMEDIATE\nROOT\n"
    assert output.stat().st_mode & 0o777 == 0o444
    assert "changed=0" in deploy()
    assert output.read_text().count("INTERMEDIATE") == 1
    del variables["certificates_custom_server_ca_certificate"]
    host_certs = tmp_path / "host-certs"
    host_certs.mkdir()
    variables["certificates_output_directory_certs"] = str(host_certs)
    deploy()
    assert (host_certs / output.name).read_bytes() == output.read_bytes()
    (certs / "server-ca.crt").unlink()
    (certs / "server-ca.crt").write_text("NEW INTERMEDIATE\nROOT\n")
    leaf.write_text("NEW LEAF\n")
    deploy()
    assert (host_certs / output.name).read_text() == "NEW LEAF\nNEW INTERMEDIATE\nROOT\n"
    assert "changed=0" in deploy()
