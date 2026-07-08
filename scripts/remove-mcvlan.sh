#!/usr/bin/env bash
# remove mcvlan network from docker host

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
NETWORK_NAME="${NETWORK_NAME:-homelab_mcvlan}"

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
