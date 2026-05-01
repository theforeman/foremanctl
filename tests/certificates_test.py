import datetime
import dateutil.parser
import pytest

def certificate_info(server, certificate):
    openssl_result = server.run(f"openssl x509 -in {certificate} -noout -enddate -dateopt iso_8601 -subject -issuer")
    return dict([x.split('=', 1) for x in openssl_result.stdout.splitlines()])

@pytest.mark.parametrize("certificate_type", ['ca_certificate', 'server_ca_certificate', 'server_certificate', 'client_certificate', 'localhost_certificate'])
def test_certificate_expiry(server, certificates, certificate_type):
    openssl_data = certificate_info(server, certificates[certificate_type])
    not_after = dateutil.parser.parse(openssl_data['notAfter'])
    now = datetime.datetime.now(tz=not_after.tzinfo)
    assert not_after - now > datetime.timedelta(days=365*10)

def test_default_server_ca_matches_internal_ca(server, certificates, default_certificates):
    ca_info = certificate_info(server, certificates['ca_certificate'])
    server_ca_info = certificate_info(server, certificates['server_ca_certificate'])
    assert ca_info['subject'] == server_ca_info['subject'], \
        "Default/installer server CA should match the internal CA"

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

    assert len(subjects) == 2, f"CA bundle should contain exactly 2 certificates, found {len(subjects)}"
    assert ca_info['subject'] in subjects[0] or ca_info['subject'] in subjects[1], \
        f"Internal CA not found in bundle. Expected: {ca_info['subject']}, Found: {subjects}"
    assert server_ca_info['subject'] in subjects[0] or server_ca_info['subject'] in subjects[1], \
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

def test_localhost_certificate_issued_by_internal_ca(server, certificates, custom_certificates):
    localhost_info = certificate_info(server, certificates['localhost_certificate'])
    ca_info = certificate_info(server, certificates['ca_certificate'])
    assert localhost_info['issuer'] == ca_info['subject'], \
        "Localhost certificate should be issued by the internal CA even with custom server certs"

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

