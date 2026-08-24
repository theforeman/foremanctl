#!/bin/bash

set -uo pipefail

CERT=""
KEY=""
CACERT=""
MAX_ATTEMPTS=5

usage() {
    echo "Usage: $0 --cert CERT --key KEY --cacert CA URL OUTPUT_FILE [URL OUTPUT_FILE ...]" >&2
    echo "Downloads vulnerability metadata and triggers a vmaas reposync when any file changed." >&2
    echo "Example: $0 --cert client.crt --key client.key --cacert ca.crt \\" >&2
    echo "  https://security.access.redhat.com/data/meta/v1/cvemap.xml /var/www/html/pub/cvemap.xml" >&2
    exit 1
}

trigger_reposync() {
    if [[ -z "$CERT" || -z "$KEY" || -z "$CACERT" ]]; then
        echo "Error: --cert, --key and --cacert are required to trigger reposync" >&2
        return 1
    fi

    echo "Triggering reposync via SSL API"

    local attempt=1
    local delay=1

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
            return 0
        else
            echo "Failed to trigger reposync (attempt $attempt/$MAX_ATTEMPTS)"
            if [[ $attempt -lt $MAX_ATTEMPTS ]]; then
                echo "Waiting ${delay}s before retry..."
                sleep $delay
                delay=$((delay * 2))
            else
                echo "Warning: Failed to trigger reposync after $MAX_ATTEMPTS attempts" >&2
                return 1
            fi
        fi

        ((attempt++))
    done

    return 1
}

# Parse reposync trigger options; remaining args are URL/OUTPUT_FILE pairs.
while [[ $# -gt 0 ]]; do
    case "$1" in
        --cert)    CERT="$2"; shift 2 ;;
        --key)     KEY="$2"; shift 2 ;;
        --cacert)  CACERT="$2"; shift 2 ;;
        --) shift; break ;;
        -*) usage ;;
        *) break ;;
    esac
done

if [[ $# -lt 2 ]] || [[ $(($# % 2)) -ne 0 ]]; then
    usage
fi

DOWNLOAD_FAILED=false
CHANGED=false

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
            CHANGED=true
        else
            echo "Manual file $BASENAME unchanged, skipping"
        fi
    else
        echo "Online mode: Checking for updates of $BASENAME from $URL"

        TEMP_FILE=$(mktemp -t "iop-vuln-metadata-download.XXXXXX")
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
                CHANGED=true
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

TRIGGER_FAILED=false

if [[ "$CHANGED" == "true" ]]; then
    echo "One or more files changed, triggering reposync"
    if ! trigger_reposync; then
        TRIGGER_FAILED=true
    fi
else
    echo "No files changed, skipping reposync"
fi

if [[ "$DOWNLOAD_FAILED" == "true" ]]; then
    echo "Error: One or more downloads failed" >&2
    exit 1
fi

if [[ "$TRIGGER_FAILED" == "true" ]]; then
    exit 1
fi
