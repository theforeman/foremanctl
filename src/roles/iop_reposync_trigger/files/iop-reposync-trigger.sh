#!/bin/bash

set -euo pipefail

usage() {
    echo "Usage: $0 --cert CERT --key KEY --cacert CA" >&2
    echo "Triggers vmaas reposync via the iop-gateway SSL API" >&2
    exit 1
}

CERT=""
KEY=""
CACERT=""
MAX_ATTEMPTS=5

while [[ $# -gt 0 ]]; do
    case "$1" in
        --cert)    CERT="$2"; shift 2 ;;
        --key)     KEY="$2"; shift 2 ;;
        --cacert)  CACERT="$2"; shift 2 ;;
        *) usage ;;
    esac
done

if [[ -z "$CERT" || -z "$KEY" || -z "$CACERT" ]]; then
    usage
fi

echo "Triggering reposync via SSL API"

attempt=1
delay=2

while [[ $attempt -le $MAX_ATTEMPTS ]]; do
    echo "Attempt $attempt/$MAX_ATTEMPTS to trigger reposync"

    if curl \
        --cert "$CERT" \
        --key "$KEY" \
        --cacert "$CACERT" \
        --silent \
        --fail \
        --header 'X-Org-Id: _iop-reposync-trigger' \
        --connect-timeout 10 \
        --max-time 30 \
        --request PUT \
        "https://localhost:24443/api/vmaas-reposcan/v1/sync"; then
        echo "Successfully triggered reposync"
        exit 0
    else
        echo "Failed to trigger reposync (attempt $attempt/$MAX_ATTEMPTS)"
        if [[ $attempt -lt $MAX_ATTEMPTS ]]; then
            echo "Waiting ${delay}s before retry..."
            sleep $delay
            delay=$((delay * 2))
        else
            echo "Warning: Failed to trigger reposync after $MAX_ATTEMPTS attempts"
            exit 1
        fi
    fi

    ((attempt++))
done
