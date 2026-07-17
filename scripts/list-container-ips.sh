#!/usr/bin/env bash
# list-container-ips.sh
# Lists the IP addresses of all running containers attached to the shared
# macvlan Docker network (homelab_macvlan).
#
# Usage:
#   ./scripts/list-container-ips.sh
#   (run from the repository root or any service directory)
#
# Configuration (read from .env.common and .env, with defaults):
#   NETWORK_NAME  — name of the macvlan network to inspect (default: homelab_macvlan)
#
# Output format:
#   CONTAINER                      NETWORK            IP ADDRESS
#   ----------------------------- ------------------ ---------------
#   adguard-homelab                homelab_macvlan    192.168.178.252
#   ...
#
# See also:
#   create-macvlan.sh              — create the shared network
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

printf "%-30s %-18s %-15s\n" "CONTAINER" "NETWORK" "IP ADDRESS"
printf "%-30s %-18s %-15s\n" \
    "------------------------------" \
    "------------------" \
    "---------------"

docker ps -q | while read -r CONTAINER_ID; do

    CONTAINER_NAME=$(docker inspect \
        --format '{{ .Name }}' "${CONTAINER_ID}" | sed 's#^/##')

    IP=$(docker inspect \
        --format "{{with index .NetworkSettings.Networks \"${NETWORK_NAME}\"}}{{.IPAddress}}{{end}}" \
        "${CONTAINER_ID}")

    if [ -n "${IP}" ]; then
        printf "%-30s %-18s %-15s\n" \
            "${CONTAINER_NAME}" \
            "${NETWORK_NAME}" \
            "${IP}"
    fi

done | sort
