#!/usr/bin/env bash
# creates macvlan network (homelab_macvlan) inside docker host

set -euo pipefail

#
# Load .env if present
#
if [ -f ".env.common" ]; then
    set -a
    . ./.env.common
    set +a
fi


#
# Load .env if present
#
if [ -f ".env" ]; then
    set -a
    . ./.env
    set +a
fi

#
# Configuration
#
NETWORK_NAME="${NETWORK_NAME:-homelab_macvlan}"
SUBNET="${SUBNET:-192.168.178.224/27}"
GATEWAY="${GATEWAY:-192.168.178.1}"
NETWORK_ADAPTER="${NETWORK_ADAPTER:-eth0}"

#
# Check whether the network already exists
#
if docker network inspect "${NETWORK_NAME}" >/dev/null 2>&1; then
    echo "✔ Docker network '${NETWORK_NAME}' already exists."
    exit 0
fi

echo "Creating Docker macvlan network '${NETWORK_NAME}'..."

docker network create \
    --driver macvlan \
    --subnet "${SUBNET}" \
    --gateway "${GATEWAY}" \
    --opt parent="${NETWORK_ADAPTER}" \
    "${NETWORK_NAME}"

echo
echo "✔ Network successfully created."
echo
docker network inspect "${NETWORK_NAME}"
