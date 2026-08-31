#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <base_url> <filename>"
    echo "Example:"
    echo "  $0 https://alimonitor.cern.ch/train-workdir/tests/0071/00717653 AO2D.root"
    exit 1
fi

BASE_URL="${1%/}"   # Remove trailing slash if present
FILE="$2"

curl \
    --capath "$X509_CERT_DIR" \
    --cert ~/.globus/usercert.pem \
    --key ~/.globus/userkey.pem \
    "${BASE_URL}/${FILE}" \
    --output "$FILE"
