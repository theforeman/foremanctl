#!/bin/bash

set -uo pipefail

if [[ $# -lt 2 ]] || [[ $(($# % 2)) -ne 0 ]]; then
    echo "Usage: $0 URL OUTPUT_FILE [URL OUTPUT_FILE ...]" >&2
    echo "Example: $0 https://security.access.redhat.com/data/metrics/repository-to-cpe.json /var/www/html/pub/iop/data/metrics/repository-to-cpe.json" >&2
    exit 1
fi

DOWNLOAD_FAILED=false

while [[ $# -ge 2 ]]; do
    URL="$1"
    OUTPUT_FILE="$2"
    shift 2

    OUTPUT_DIR=$(dirname "$OUTPUT_FILE")
    BASENAME=$(basename "$OUTPUT_FILE")
    MANUAL_FILE="/var/lib/foreman/$BASENAME"

    mkdir -p "$OUTPUT_DIR"

    if [[ -f "$MANUAL_FILE" ]]; then
        echo "Offline mode: Using manual file from $MANUAL_FILE"

        CURRENT_CHECKSUM=$(sha256sum "$MANUAL_FILE" | cut -d' ' -f1)
        STORED_CHECKSUM=""

        if [[ -f "$OUTPUT_FILE" ]]; then
            STORED_CHECKSUM=$(sha256sum "$OUTPUT_FILE" | cut -d' ' -f1)
        fi

        if [[ "$CURRENT_CHECKSUM" != "$STORED_CHECKSUM" ]]; then
            echo "Copying updated manual file $BASENAME"
            cp -Z "$MANUAL_FILE" "$OUTPUT_FILE"
            chmod 644 "$OUTPUT_FILE"
        else
            echo "Manual file $BASENAME unchanged, skipping"
        fi
    else
        echo "Online mode: Checking for updates of $BASENAME from $URL"

        TEMP_FILE=$(mktemp -t "iop-cpe-download.XXXXXX")
        FILE_MODTIME="Thu, 01 Jan 1970 00:00:00 +0000"

        if [[ -f "$OUTPUT_FILE" ]]; then
            FILE_MODTIME=$(date -u -R -r "$OUTPUT_FILE")
        fi

        if curl \
            --silent \
            --fail \
            --location \
            --remote-time \
            --time-cond "$FILE_MODTIME" \
            --remote-time \
            --output "$TEMP_FILE" \
            "$URL"; then

            if [[ -s "$TEMP_FILE" ]]; then
                echo "Downloaded new version of $BASENAME"
                mv -Z "$TEMP_FILE" "$OUTPUT_FILE"
                chmod 644 "$OUTPUT_FILE"
            else
                echo "Not modified: $BASENAME"
                rm -f "$TEMP_FILE"
            fi
        else
            echo "Error: Failed to download from $URL" >&2
            rm -f "$TEMP_FILE"
            DOWNLOAD_FAILED=true
        fi
    fi
done

if [[ "$DOWNLOAD_FAILED" == "true" ]]; then
    echo "Error: One or more downloads failed" >&2
    exit 1
fi
