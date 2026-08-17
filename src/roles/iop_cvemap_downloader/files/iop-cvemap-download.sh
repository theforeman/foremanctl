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
