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
