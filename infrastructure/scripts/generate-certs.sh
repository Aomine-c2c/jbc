#!/bin/bash
set -e

CERTS_DIR="$(pwd)/../certs"
DOMAIN="dwrms.company.internal"

echo "Generating self-signed certificates for ${DOMAIN}..."

mkdir -p "${CERTS_DIR}"

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "${CERTS_DIR}/dwrms.key" \
    -out "${CERTS_DIR}/dwrms.crt" \
    -subj "/C=US/ST=State/L=City/O=Company/OU=IT/CN=${DOMAIN}"

echo "Certificates generated successfully in ${CERTS_DIR}:"
ls -la "${CERTS_DIR}"
echo ""
echo "IMPORTANT: These are self-signed certificates intended for bootstrapping or testing."
echo "For production on an internal network, replace these with certificates signed by your internal CA."
