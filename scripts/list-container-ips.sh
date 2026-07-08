#!/usr/bin/env bash
# lists ip addresses of docker containers inside mcvlan network (homelab_mcvlan)

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
