#!/usr/bin/env bash
# Test-only CA hierarchy. Reuse the CA when issuing another hostname.
set -euo pipefail
cert_dir=$1
shift
umask 077
mkdir -p "$cert_dir"
cd "$cert_dir"
if [ ! -f root.pem ]; then
  openssl req -x509 -newkey rsa:3072 -nodes -sha256 -days 10950 \
    -subj '/CN=SAT-20173 Test Root' -keyout root.key -out root.pem \
    -addext 'basicConstraints=critical,CA:TRUE,pathlen:1' \
    -addext 'keyUsage=critical,keyCertSign,cRLSign'
fi
if [ ! -f intermediate.pem ]; then
  openssl req -new -newkey rsa:3072 -nodes -sha256 \
    -subj '/CN=SAT-20173 Test Intermediate' -keyout intermediate.key -out intermediate.csr
  cat > intermediate.ext <<'EOF'
basicConstraints=critical,CA:TRUE,pathlen:0
keyUsage=critical,keyCertSign,cRLSign
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid,issuer
EOF
  openssl x509 -req -in intermediate.csr -CA root.pem -CAkey root.key \
    -CAcreateserial -days 7300 -sha256 -extfile intermediate.ext -out intermediate.pem
fi
cat intermediate.pem root.pem > server-ca.pem
for cert_host in "$@"; do
  case "$cert_host" in *[!a-zA-Z0-9.-]*|'') echo 'Invalid hostname' >&2; exit 1;; esac
  openssl req -new -newkey rsa:3072 -nodes -sha256 -subj "/CN=$cert_host" \
    -keyout "$cert_host.key" -out "$cert_host.csr"
  cat > "$cert_host.ext" <<EOF
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth,clientAuth
subjectAltName=DNS:$cert_host
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid,issuer
EOF
  openssl x509 -req -in "$cert_host.csr" -CA intermediate.pem -CAkey intermediate.key \
    -CAcreateserial -days 7300 -sha256 -extfile "$cert_host.ext" -out "$cert_host.crt"
  openssl verify -CAfile root.pem -untrusted intermediate.pem "$cert_host.crt"
done
