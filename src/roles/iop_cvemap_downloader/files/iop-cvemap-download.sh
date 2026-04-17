#!/bin/bash

set -euo pipefail

URL="${1:-}"
OUTPUT_FILE="${2:-}"

if [[ -z "$URL" || -z "$OUTPUT_FILE" ]]; then
    echo "Usage: $0 URL OUTPUT_FILE" >&2
    echo "Example: $0 https://security.access.redhat.com/data/meta/v1/cvemap.xml /var/www/html/pub/cvemap.xml" >&2
    exit 1
fi

OUTPUT_DIR=$(dirname "$OUTPUT_FILE")
MANUAL_FILE="/var/lib/foreman/cvemap.xml"
CHECKSUM_FILE="${OUTPUT_FILE}.checksum"
FILE_UPDATED=false

mkdir -p "$OUTPUT_DIR"

if [[ -f "$MANUAL_FILE" ]]; then
    echo "Offline mode: Using manual file from $MANUAL_FILE"

    CURRENT_CHECKSUM=$(sha256sum "$MANUAL_FILE" | cut -d' ' -f1)
    STORED_CHECKSUM=""

    if [[ -f "$CHECKSUM_FILE" ]]; then
        STORED_CHECKSUM=$(cat "$CHECKSUM_FILE")
    fi

    if [[ "$CURRENT_CHECKSUM" != "$STORED_CHECKSUM" ]]; then
        echo "Copying updated manual file"
        cp -Z "$MANUAL_FILE" "$OUTPUT_FILE" && echo "$CURRENT_CHECKSUM" > "$CHECKSUM_FILE"
        chmod 644 "$OUTPUT_FILE"
        FILE_UPDATED=true
    else
        echo "Manual file unchanged, skipping"
    fi
else
    echo "Online mode: Checking for updates from $URL"

    TEMP_FILE=$(mktemp -t "iop-cvemap-download.XXXXXX")

    cleanup() {
        rm -f "$TEMP_FILE"
    }
    trap cleanup EXIT

    if curl \
        --silent \
        --fail \
        --location \
        --output "$TEMP_FILE" \
        "$URL"; then

        echo "Downloaded new version"

        if [[ -f "$OUTPUT_FILE" ]]; then
            echo "Replacing existing file atomically"
        else
            echo "Creating new file"
        fi

        mv -Z "$TEMP_FILE" "$OUTPUT_FILE"
        chmod 644 "$OUTPUT_FILE"
        FILE_UPDATED=true
    else
        echo "Error: Failed to download from $URL" >&2
        exit 1
    fi
fi

echo "Update check completed successfully"

trigger_reposync() {
    echo "CVE map file was updated, triggering reposync via SSL API"

    local max_attempts=5
    local attempt=1
    local delay=2

    while [[ $attempt -le $max_attempts ]]; do
        echo "Attempt $attempt/$max_attempts to trigger reposync"

        if curl \
            --cert /etc/foreman/client_cert.pem \
            --key /etc/foreman/client_key.pem \
            --cacert /etc/foreman/proxy_ca.pem \
            --silent \
            --fail \
            --connect-timeout 10 \
            --max-time 30 \
            --request PUT \
            "https://localhost:24443/api/vmaas-reposcan/v1/sync"; then
            echo "Successfully triggered reposync"
            return 0
        else
            echo "Failed to trigger reposync (attempt $attempt/$max_attempts)"
            if [[ $attempt -lt $max_attempts ]]; then
                echo "Waiting ${delay}s before retry..."
                sleep $delay
                delay=$((delay * 2))
            else
                echo "Warning: Failed to trigger reposync after $max_attempts attempts"
                return 1
            fi
        fi

        ((attempt++))
    done
}

if [[ "$FILE_UPDATED" == "true" ]]; then
    trigger_reposync
else
    echo "CVE map file unchanged, skipping reposync trigger"
fi
