import datetime
import re
import ssl

import dateutil.parser
import pytest


def certificate_info(server, certificate):
    openssl_result = server.run(f"openssl x509 -in {certificate} -noout -enddate -dateopt iso_8601 -subject -issuer")
    return dict([x.split('=', 1) for x in openssl_result.stdout.splitlines()])


@pytest.mark.parametrize("certificate_type", ['ca_certificate', 'server_ca_certificate', 'server_certificate', 'client_certificate'])
def test_certificate_expiry(server, certificates, certificate_type):
    openssl_data = certificate_info(server, certificates[certificate_type])
    not_after = dateutil.parser.parse(openssl_data['notAfter'])
    now = datetime.datetime.now(tz=not_after.tzinfo)
    assert not_after - now > datetime.timedelta(days=365*10)


def test_default_server_ca_matches_internal_ca(server, certificates, default_certificates):
    ca_info = certificate_info(server, certificates['ca_certificate'])
    server_ca_info = certificate_info(server, certificates['server_ca_certificate'])
    assert ca_info['subject'] == server_ca_info['subject'], \
        "Default server CA should match the internal CA"


def test_custom_server_ca_differs_from_internal_ca(server, certificates, custom_certificates):
    ca_info = certificate_info(server, certificates['ca_certificate'])
    server_ca_info = certificate_info(server, certificates['server_ca_certificate'])
    assert ca_info['subject'] != server_ca_info['subject'], \
        "Custom server CA should have a different subject than the internal CA"


def test_custom_server_certificate_issued_by_custom_ca(server, certificates, custom_certificates):
    server_info = certificate_info(server, certificates['server_certificate'])
    server_ca_info = certificate_info(server, certificates['server_ca_certificate'])
    assert server_info['issuer'] == server_ca_info['subject'], \
        "Server certificate should be issued by the custom server CA"


def test_client_certificate_issued_by_internal_ca(server, certificates, custom_certificates):
    client_info = certificate_info(server, certificates['client_certificate'])
    ca_info = certificate_info(server, certificates['ca_certificate'])
    assert client_info['issuer'] == ca_info['subject'], \
        "Client certificate should still be issued by the internal CA"


def test_ca_bundle_contains_both_cas(server, certificates, custom_certificates):
    openssl_result = server.run(f"awk '/BEGIN CERTIFICATE/,/END CERTIFICATE/' {certificates['ca_bundle']} | openssl crl2pkcs7 -nocrl -certfile /dev/stdin | openssl pkcs7 -print_certs -noout -text | grep 'Subject:'")
    subjects = [line.strip() for line in openssl_result.stdout.splitlines()]

    ca_info = certificate_info(server, certificates['ca_certificate'])
    server_ca_info = certificate_info(server, certificates['server_ca_certificate'])

    expected_count = 1 + len(pem_certificates(server.file(certificates['server_ca_certificate']).content_string))
    assert len(subjects) == expected_count, f"CA bundle should contain {expected_count} certificates, found {len(subjects)}"
    assert any(ca_info['subject'] in subject for subject in subjects), \
        f"Internal CA not found in bundle. Expected: {ca_info['subject']}, Found: {subjects}"
    assert any(server_ca_info['subject'] in subject for subject in subjects), \
        f"Server CA not found in bundle. Expected: {server_ca_info['subject']}, Found: {subjects}"


def test_server_certificate_chain_verifies(server, certificates):
    cmd = server.run(
        f"openssl verify -CAfile {certificates['ca_bundle']} "
        f"{certificates['server_certificate']}"
    )
    assert cmd.succeeded
    assert "OK" in cmd.stdout


def test_client_certificate_chain_verifies(server, certificates):
    cmd = server.run(
        f"openssl verify -CAfile {certificates['ca_certificate']} "
        f"{certificates['client_certificate']}"
    )
    assert cmd.succeeded
    assert "OK" in cmd.stdout


def test_ca_bundle_exists(server, certificates):
    f = server.file(certificates['ca_bundle'])
    assert f.exists
    assert not f.is_directory


def test_ca_bundle_verifies_server_certificate(server, certificates):
    cmd = server.run(
        f"openssl verify -CAfile {certificates['ca_bundle']} "
        f"{certificates['server_certificate']}"
    )
    assert cmd.succeeded
    assert "OK" in cmd.stdout


def test_ca_key_unencrypted(server, server_hostname, certificates):
    if server_hostname == 'proxy':
        pytest.skip("no ca key on proxy")
    f = server.file(certificates['ca_key'])
    assert f.exists
    assert f.mode == 0o600
    assert 'ENCRYPTED' not in f.content_string
    cmd = server.run(f"openssl pkey -in {certificates['ca_key']} -noout")
    assert cmd.succeeded


def test_ca_key_password_file_absent(server, certificates):
    ca_pwd = certificates['ca_key'].rsplit('/', 1)[0] + '/ca.pwd'
    assert not server.file(ca_pwd).exists


def test_ca_key_matches_ca_certificate(server, server_hostname, certificates):
    if server_hostname == 'proxy':
        pytest.skip("no ca key on proxy")
    key_pub = server.run(f"openssl pkey -in {certificates['ca_key']} -pubout")
    cert_pub = server.run(f"openssl x509 -in {certificates['ca_certificate']} -noout -pubkey")
    assert key_pub.succeeded
    assert cert_pub.succeeded
    assert key_pub.stdout == cert_pub.stdout


@pytest.mark.parametrize("cert_key,expected_mode", [
    ('server_certificate', 0o444),
    ('server_ca_certificate', 0o444),
    ('ca_bundle', 0o444),
])
def test_custom_certificate_file_permissions(server, certificates, custom_certificates, cert_key, expected_mode):
    f = server.file(certificates[cert_key])
    assert f.exists
    assert f.mode == expected_mode


def test_custom_server_key_permissions(server, certificates, custom_certificates):
    f = server.file(certificates['server_key'])
    assert f.exists
    assert f.mode == 0o440


def pem_certificates(content):
    return [
        ssl.PEM_cert_to_DER_cert(pem)
        for pem in re.findall(r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", content, re.S)
    ]


def test_custom_server_file_contains_ca_chain(server, certificates, custom_certificates):
    chain = pem_certificates(server.file(certificates["server_certificate"]).content_string)
    ca_chain = pem_certificates(server.file(certificates["server_ca_certificate"]).content_string)
    assert chain[1:] == ca_chain, "Server file must contain the leaf followed by the issuing chain"
