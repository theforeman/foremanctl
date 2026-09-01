#!/bin/bash

CERTS_DIR=certs

# Fedora and RHEL disable SHA-1 signatures in the system OpenSSL configuration.
# The deliberately weak fixtures below need them, so they are generated with a
# throwaway configuration that turns them back on.
SHA1_CONF=$(mktemp)
trap 'rm -f "$SHA1_CONF"' EXIT
cat >"$SHA1_CONF" <<'CONF'
openssl_conf = openssl_init

[openssl_init]
alg_section = evp_properties

[evp_properties]
rh-allow-sha1-signatures = yes
CONF

THIRDPARTY_CA_CERT_NAME=ca-thirdparty
if [[ ! -f "$CERTS_DIR/$THIRDPARTY_CA_CERT_NAME.key" || ! -f "$CERTS_DIR/$THIRDPARTY_CA_CERT_NAME.crt" ]]; then
  echo "Generate CA"
  openssl genrsa -out $CERTS_DIR/$THIRDPARTY_CA_CERT_NAME.key 2048
  openssl req -x509 -new -nodes -key $CERTS_DIR/$THIRDPARTY_CA_CERT_NAME.key -sha256 -days 3650 -out $CERTS_DIR/$THIRDPARTY_CA_CERT_NAME.crt -subj "/CN=Thirdparty CA"
else
  echo "Thirdparty CA certificate exists. Skipping."
fi

CA_CERT_NAME=ca
if [[ ! -f "$CERTS_DIR/$CA_CERT_NAME.key" || ! -f "$CERTS_DIR/$CA_CERT_NAME.crt" ]]; then
  echo "Generate CA"
  openssl genrsa -out $CERTS_DIR/$CA_CERT_NAME.key 2048
  openssl req -x509 -new -nodes -key $CERTS_DIR/$CA_CERT_NAME.key -sha256 -days 3650 -out $CERTS_DIR/$CA_CERT_NAME.crt -subj "/CN=Test Self-Signed CA"
else
  echo "CA certificate exists. Skipping."
fi

CA_BUNDLE=ca-bundle
if [[ ! -f "$CERTS_DIR/$CA_BUNDLE.crt" ]]; then
  echo "Generate CA bundle"
  cat $CERTS_DIR/$THIRDPARTY_CA_CERT_NAME.crt $CERTS_DIR/$CA_CERT_NAME.crt > $CERTS_DIR/$CA_BUNDLE.crt
else
  echo "CA certificate bundle exists. Skipping."
fi

CA_BUNDLE=ca-bundle-with-trust-rules
CA_CERT_WITH_TRUST_RULES=ca-with-trust-rules
if [[ ! -f "$CERTS_DIR/$CA_BUNDLE.crt" ]]; then
  echo "Generate CA bundle with trust rules"
  openssl x509 -in $CERTS_DIR/$CA_CERT_NAME.crt -addtrust serverAuth -out $CERTS_DIR/$CA_CERT_WITH_TRUST_RULES.crt
  cat $CERTS_DIR/$THIRDPARTY_CA_CERT_NAME.crt $CERTS_DIR/$CA_CERT_WITH_TRUST_RULES.crt > $CERTS_DIR/$CA_BUNDLE.crt
else
  echo "CA certificate bundle with trust rules exists. Skipping."
fi

CA_SHA1_CERT_NAME=ca-sha1
CA_SHA1_CERT_BUNDLE=ca-sha1-bundle
if [[ ! -f "$CERTS_DIR/$CA_SHA1_CERT_NAME.key" || ! -f "$CERTS_DIR/$CA_SHA1_CERT_NAME.crt" || ! -f "$CERTS_DIR/$CA_SHA1_CERT_BUNDLE.crt" ]]; then
  echo "Generate CA with sha1 signing algorithm"
  openssl genrsa -out $CERTS_DIR/$CA_SHA1_CERT_NAME.key 2048
  OPENSSL_CONF="$SHA1_CONF" openssl req -new -key $CERTS_DIR/$CA_SHA1_CERT_NAME.key -sha1 -out $CERTS_DIR/$CA_SHA1_CERT_NAME.csr -subj "/CN=Test Self-Signed CA"
  OPENSSL_CONF="$SHA1_CONF" openssl x509 -req -in $CERTS_DIR/$CA_SHA1_CERT_NAME.csr -CA $CERTS_DIR/$CA_CERT_NAME.crt -CAkey $CERTS_DIR/$CA_CERT_NAME.key -CAcreateserial -out $CERTS_DIR/$CA_SHA1_CERT_NAME.crt -days 3650 -sha1

  cat $CERTS_DIR/$CA_CERT_NAME.crt $CERTS_DIR/$CA_SHA1_CERT_NAME.crt > $CERTS_DIR/$CA_SHA1_CERT_BUNDLE.crt
else
  echo "CA certificate exists. Skipping."
fi

CERT_NAME=foreman-sha1.example.com
if [[ ! -f "$CERTS_DIR/$CERT_NAME.key" || ! -f "$CERTS_DIR/$CERT_NAME.crt" ]]; then
  echo "Generate server certificate"
  openssl genrsa -out $CERTS_DIR/$CERT_NAME.key 2048
  openssl req -new -key $CERTS_DIR/$CERT_NAME.key -out $CERTS_DIR/$CERT_NAME.csr -subj "/CN=foreman.example.com"
  openssl x509 -req -in $CERTS_DIR/$CERT_NAME.csr -CA $CERTS_DIR/$CA_SHA1_CERT_NAME.crt -CAkey $CERTS_DIR/$CA_SHA1_CERT_NAME.key -CAcreateserial -out $CERTS_DIR/$CERT_NAME.crt -days 3650 -sha256 -extfile extensions.txt -extensions extensions
else
  echo "Server certificate with sha1 CA exists. Skipping."
fi

CERT_NAME=foreman-bad-san.example.com
if [[ ! -f "$CERTS_DIR/$CERT_NAME.key" || ! -f "$CERTS_DIR/$CERT_NAME.crt" ]]; then
  echo "Generate server certificate"
  openssl genrsa -out $CERTS_DIR/$CERT_NAME.key 2048
  openssl req -new -key $CERTS_DIR/$CERT_NAME.key -out $CERTS_DIR/$CERT_NAME.csr -subj "/CN=${CERT_NAME}"
  openssl x509 -req -in $CERTS_DIR/$CERT_NAME.csr -CA $CERTS_DIR/$CA_CERT_NAME.crt -CAkey $CERTS_DIR/$CA_CERT_NAME.key -CAcreateserial -out $CERTS_DIR/$CERT_NAME.crt -days 3650 -sha256 -extfile extensions.txt -extensions extensions
else
  echo "Server certificate with bad SAN exists. Skipping."
fi

CERT_NAME=foreman.example.com
if [[ ! -f "$CERTS_DIR/$CERT_NAME.key" || ! -f "$CERTS_DIR/$CERT_NAME.crt" ]]; then
  echo "Generate server certificate"
  openssl genrsa -out $CERTS_DIR/$CERT_NAME.key 2048
  openssl req -new -key $CERTS_DIR/$CERT_NAME.key -out $CERTS_DIR/$CERT_NAME.csr -subj "/CN=foreman.example.com"
  openssl x509 -req -in $CERTS_DIR/$CERT_NAME.csr -CA $CERTS_DIR/$CA_CERT_NAME.crt -CAkey $CERTS_DIR/$CA_CERT_NAME.key -CAcreateserial -out $CERTS_DIR/$CERT_NAME.crt -days 3650 -sha256 -extfile extensions.txt -extensions extensions
else
  echo "Server certificate exists. Skipping."
fi

CERT_NAME=foreman-ec384.example.com
if [[ ! -f "$CERTS_DIR/$CERT_NAME.key" || ! -f "$CERTS_DIR/$CERT_NAME.crt" ]]; then
  echo "Generate server certificate"
  openssl ecparam -genkey -name secp384r1 -out $CERTS_DIR/$CERT_NAME.key
  openssl req -new -key $CERTS_DIR/$CERT_NAME.key -out $CERTS_DIR/$CERT_NAME.csr -subj "/CN=${CERT_NAME}"
  openssl x509 -req -in $CERTS_DIR/$CERT_NAME.csr -CA $CERTS_DIR/$CA_CERT_NAME.crt -CAkey $CERTS_DIR/$CA_CERT_NAME.key -CAcreateserial -out $CERTS_DIR/$CERT_NAME.crt -days 3650 -sha256 -extfile extensions.txt -extensions ec_extensions
else
  echo "ECC Server certificate exists. Skipping."
fi

CERT_NAME=foreman-nokeyenc.example.com
if [[ ! -f "$CERTS_DIR/$CERT_NAME.key" || ! -f "$CERTS_DIR/$CERT_NAME.crt" ]]; then
  echo "Generate RSA server certificate without Key Encipherment"
  openssl genrsa -out $CERTS_DIR/$CERT_NAME.key 2048
  openssl req -new -key $CERTS_DIR/$CERT_NAME.key -out $CERTS_DIR/$CERT_NAME.csr -subj "/CN=${CERT_NAME}"
  openssl x509 -req -in $CERTS_DIR/$CERT_NAME.csr -CA $CERTS_DIR/$CA_CERT_NAME.crt -CAkey $CERTS_DIR/$CA_CERT_NAME.key -CAcreateserial -out $CERTS_DIR/$CERT_NAME.crt -days 3650 -sha256 -extfile extensions.txt -extensions nokeyenc_extensions
else
  echo "RSA server certificate without Key Encipherment exists. Skipping."
fi

CERT_NAME=invalid
if [[ ! -f "$CERTS_DIR/$CERT_NAME.key" || ! -f "$CERTS_DIR/$CERT_NAME.crt" ]]; then
  echo "Generate invalid server certificate"
  openssl genrsa -out $CERTS_DIR/$CERT_NAME.key 2048
  openssl req -new -key $CERTS_DIR/$CERT_NAME.key -out $CERTS_DIR/$CERT_NAME.csr -subj "/CN=foreman.example.com"
  openssl x509 -req -in $CERTS_DIR/$CERT_NAME.csr -CA $CERTS_DIR/$CA_CERT_NAME.crt -CAkey $CERTS_DIR/$CA_CERT_NAME.key -CAcreateserial -out $CERTS_DIR/$CERT_NAME.crt -days 3650 -sha256 -extfile extensions.txt -extensions client_extensions
else
  echo "Invalid server certificate exists. Skipping."
fi

CERT_NAME=wildcard
if [[ ! -f "$CERTS_DIR/$CERT_NAME.key" || ! -f "$CERTS_DIR/$CERT_NAME.crt" ]]; then
  echo "Generate server certificate"
  openssl genrsa -out $CERTS_DIR/$CERT_NAME.key 2048
  openssl req -new -key $CERTS_DIR/$CERT_NAME.key -out $CERTS_DIR/$CERT_NAME.csr -subj "/CN=*.example.com"
  openssl x509 -req -in $CERTS_DIR/$CERT_NAME.csr -CA $CERTS_DIR/$CA_CERT_NAME.crt -CAkey $CERTS_DIR/$CA_CERT_NAME.key -CAcreateserial -out $CERTS_DIR/$CERT_NAME.crt -days 3650 -sha256 -extfile extensions.txt -extensions wildcard_extensions
else
  echo "Wildcard server certificate exists. Skipping."
fi

CERT_NAME=shortname
if [[ ! -f "$CERTS_DIR/$CERT_NAME.key" || ! -f "$CERTS_DIR/$CERT_NAME.crt" ]]; then
  echo "Generate shortname server certificate"
  openssl genrsa -out $CERTS_DIR/$CERT_NAME.key 2048
  openssl req -new -key $CERTS_DIR/$CERT_NAME.key -out $CERTS_DIR/$CERT_NAME.csr -subj "/CN=foreman"
  openssl x509 -req -in $CERTS_DIR/$CERT_NAME.csr -CA $CERTS_DIR/$CA_CERT_NAME.crt -CAkey $CERTS_DIR/$CA_CERT_NAME.key -CAcreateserial -out $CERTS_DIR/$CERT_NAME.crt -days 3650 -sha256 -extfile extensions.txt -extensions shortname_extensions
else
  echo "Shortname server certificate exists. Skipping."
fi

CA_EC_CERT_NAME=ca-ec
if [[ ! -f "$CERTS_DIR/$CA_EC_CERT_NAME.key" || ! -f "$CERTS_DIR/$CA_EC_CERT_NAME.crt" ]]; then
  echo "Generate EC CA"
  openssl ecparam -genkey -name secp384r1 -out $CERTS_DIR/$CA_EC_CERT_NAME.key
  openssl req -x509 -new -nodes -key $CERTS_DIR/$CA_EC_CERT_NAME.key -sha256 -days 3650 -out $CERTS_DIR/$CA_EC_CERT_NAME.crt -subj "/CN=Test EC CA"
else
  echo "EC CA certificate exists. Skipping."
fi

CERT_NAME=foreman-ec-ca.example.com
if [[ ! -f "$CERTS_DIR/$CERT_NAME.key" || ! -f "$CERTS_DIR/$CERT_NAME.crt" ]]; then
  echo "Generate server certificate signed by the EC CA"
  openssl ecparam -genkey -name secp384r1 -out $CERTS_DIR/$CERT_NAME.key
  openssl req -new -key $CERTS_DIR/$CERT_NAME.key -out $CERTS_DIR/$CERT_NAME.csr -subj "/CN=${CERT_NAME}"
  openssl x509 -req -in $CERTS_DIR/$CERT_NAME.csr -CA $CERTS_DIR/$CA_EC_CERT_NAME.crt -CAkey $CERTS_DIR/$CA_EC_CERT_NAME.key -CAcreateserial -out $CERTS_DIR/$CERT_NAME.crt -days 3650 -sha256 -extfile extensions.txt -extensions ec_ca_extensions
else
  echo "Server certificate signed by the EC CA exists. Skipping."
fi

CA_EC_SHA1_CERT_NAME=ca-ec-sha1
CA_EC_SHA1_CERT_BUNDLE=ca-ec-sha1-bundle
if [[ ! -f "$CERTS_DIR/$CA_EC_SHA1_CERT_NAME.key" || ! -f "$CERTS_DIR/$CA_EC_SHA1_CERT_NAME.crt" || ! -f "$CERTS_DIR/$CA_EC_SHA1_CERT_BUNDLE.crt" ]]; then
  echo "Generate EC CA with sha1 signing algorithm"
  openssl ecparam -genkey -name secp384r1 -out $CERTS_DIR/$CA_EC_SHA1_CERT_NAME.key
  OPENSSL_CONF="$SHA1_CONF" openssl req -new -key $CERTS_DIR/$CA_EC_SHA1_CERT_NAME.key -sha1 -out $CERTS_DIR/$CA_EC_SHA1_CERT_NAME.csr -subj "/CN=Test EC SHA1 CA"
  OPENSSL_CONF="$SHA1_CONF" openssl x509 -req -in $CERTS_DIR/$CA_EC_SHA1_CERT_NAME.csr -CA $CERTS_DIR/$CA_EC_CERT_NAME.crt -CAkey $CERTS_DIR/$CA_EC_CERT_NAME.key -CAcreateserial -out $CERTS_DIR/$CA_EC_SHA1_CERT_NAME.crt -days 3650 -sha1 -extfile extensions.txt -extensions intermediate_ca_extensions

  cat $CERTS_DIR/$CA_EC_CERT_NAME.crt $CERTS_DIR/$CA_EC_SHA1_CERT_NAME.crt > $CERTS_DIR/$CA_EC_SHA1_CERT_BUNDLE.crt
else
  echo "EC CA certificate with sha1 signing algorithm exists. Skipping."
fi

CERT_NAME=foreman-ec-sha1.example.com
if [[ ! -f "$CERTS_DIR/$CERT_NAME.key" || ! -f "$CERTS_DIR/$CERT_NAME.crt" ]]; then
  echo "Generate server certificate signed by the sha1 EC CA"
  openssl ecparam -genkey -name secp384r1 -out $CERTS_DIR/$CERT_NAME.key
  openssl req -new -key $CERTS_DIR/$CERT_NAME.key -out $CERTS_DIR/$CERT_NAME.csr -subj "/CN=${CERT_NAME}"
  openssl x509 -req -in $CERTS_DIR/$CERT_NAME.csr -CA $CERTS_DIR/$CA_EC_SHA1_CERT_NAME.crt -CAkey $CERTS_DIR/$CA_EC_SHA1_CERT_NAME.key -CAcreateserial -out $CERTS_DIR/$CERT_NAME.crt -days 3650 -sha256 -extfile extensions.txt -extensions ec_sha1_extensions
else
  echo "Server certificate signed by the sha1 EC CA exists. Skipping."
fi

# ML-DSA needs OpenSSL 3.5 or newer. The generated fixtures are committed, so
# older systems can still run the tests that consume them.
if openssl list -signature-algorithms 2>/dev/null | grep -q 'ML-DSA-65'; then
  CA_MLDSA_CERT_NAME=ca-mldsa
  if [[ ! -f "$CERTS_DIR/$CA_MLDSA_CERT_NAME.key" || ! -f "$CERTS_DIR/$CA_MLDSA_CERT_NAME.crt" ]]; then
    echo "Generate ML-DSA CA"
    openssl genpkey -algorithm ML-DSA-65 -out $CERTS_DIR/$CA_MLDSA_CERT_NAME.key
    openssl req -x509 -new -nodes -key $CERTS_DIR/$CA_MLDSA_CERT_NAME.key -days 3650 -out $CERTS_DIR/$CA_MLDSA_CERT_NAME.crt -subj "/CN=Test ML-DSA CA"
  else
    echo "ML-DSA CA certificate exists. Skipping."
  fi

  CERT_NAME=foreman-mldsa.example.com
  if [[ ! -f "$CERTS_DIR/$CERT_NAME.key" || ! -f "$CERTS_DIR/$CERT_NAME.crt" ]]; then
    echo "Generate ML-DSA server certificate"
    openssl genpkey -algorithm ML-DSA-65 -out $CERTS_DIR/$CERT_NAME.key
    openssl req -new -key $CERTS_DIR/$CERT_NAME.key -out $CERTS_DIR/$CERT_NAME.csr -subj "/CN=${CERT_NAME}"
    openssl x509 -req -in $CERTS_DIR/$CERT_NAME.csr -CA $CERTS_DIR/$CA_MLDSA_CERT_NAME.crt -CAkey $CERTS_DIR/$CA_MLDSA_CERT_NAME.key -CAcreateserial -out $CERTS_DIR/$CERT_NAME.crt -days 3650 -extfile extensions.txt -extensions mldsa_extensions
  else
    echo "ML-DSA server certificate exists. Skipping."
  fi
else
  echo "OpenSSL does not support ML-DSA. Skipping the ML-DSA fixtures."
fi
