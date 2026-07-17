#!/usr/bin/env bash
# create-macvlan.sh
# Creates the shared external macvlan Docker network (homelab_macvlan) on the
# Docker host. This network is used by all Compose stacks in the repository.
#
# Usage:
#   ./scripts/create-macvlan.sh
#   (run from the repository root)
#
# Configuration (read from .env.common and .env, with defaults):
#   NETWORK_NAME     — name of the Docker network  (default: homelab_macvlan)
#   SUBNET           — macvlan subnet CIDR          (default: 192.168.178.224/27)
#   GATEWAY          — default gateway              (default: 192.168.178.1)
#   NETWORK_ADAPTER  — host network interface       (default: eth0)
#
# The script exits without error if the network already exists.
#
# See also:
#   remove-macvlan.sh              — remove the network
#   list-container-ips.sh          — list IPs of containers in the network
#   docs/network-architecture.md   — full network documentation
#   docs/scripts.md                — overview of all helper scripts

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
