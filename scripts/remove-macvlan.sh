#!/usr/bin/env bash
# remove-macvlan.sh
# Removes the shared external macvlan Docker network (homelab_macvlan) from the
# Docker host.
#
# Usage:
#   ./scripts/remove-macvlan.sh
#   (run from the repository root)
#
# Configuration (read from .env.common and .env, with defaults):
#   NETWORK_NAME  — name of the Docker network to remove (default: homelab_macvlan)
#
# The script exits without error if the network does not exist.
# All containers using the network must be stopped before removal.
#
# See also:
#   create-macvlan.sh              — create the network
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

#
# Check whether the network exists
#
if ! docker network inspect "${NETWORK_NAME}" >/dev/null 2>&1; then
    echo "✔ Docker network '${NETWORK_NAME}' does not exist."
    exit 0
fi

echo "Removing Docker macvlan network '${NETWORK_NAME}'..."

docker network rm "${NETWORK_NAME}"

echo
echo "✔ Network successfully removed."
