#!/usr/bin/env bash
set -euo pipefail

STEP_DIR="./step"

CA_NAME="HomeLab CA"
DNS_NAMES="step-ca,${HOMELAB_DOMAIN:-homelab.internal}"
PASSWORD="${TRAEFIK_CA_PASSWORD:TopS3cretPa$$w0rd}"

mkdir -p "${STEP_DIR}"

if [ -f "${STEP_DIR}/config/ca.json" ]; then
    echo "step-ca is already initialized."
    exit 0
fi

docker run --rm \
    -v "$(pwd)/step:/home/step" \
    -e DOCKER_STEPCA_INIT_NAME="${CA_NAME}" \
    -e DOCKER_STEPCA_INIT_DNS_NAMES="${DNS_NAMES}" \
    -e DOCKER_STEPCA_INIT_PASSWORD="${PASSWORD}" \
    smallstep/step-ca

echo
echo "✓ Root CA created."
echo "Root certificate:"
echo "  ${STEP_DIR}/certs/root_ca.crt"
echo
echo "Install this certificate on your clients to trust certificates issued by step-ca."
