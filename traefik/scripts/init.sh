#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ENV_FILE="${ROOT_DIR}/.env"
ENV_TEMPLATE="${ROOT_DIR}/.env.example"

echo "-----------------------------------------------------"
echo " CI Platform - Traefik Bootstrap"
echo "-----------------------------------------------------"

#
# prerequisites
#

command -v docker >/dev/null || {
    echo "ERROR: docker not installed."
    exit 1
}

command -v openssl >/dev/null || {
    echo "ERROR: openssl not installed."
    exit 1
}

#
# directory structure
#

echo
echo "Creating directories..."

mkdir -p "${ROOT_DIR}/config"
mkdir -p "${ROOT_DIR}/certs"
mkdir -p "${ROOT_DIR}/step"
mkdir -p "${ROOT_DIR}/logs"

#
# create .env
#

if [[ ! -f "${ENV_FILE}" ]]; then

    if [[ ! -f "${ENV_TEMPLATE}" ]]; then
        echo
        echo "ERROR: .env.example not found."
        exit 1
    fi

    cp "${ENV_TEMPLATE}" "${ENV_FILE}"

    echo "Created .env"

else

    echo ".env already exists"

fi

#
# random passwords
#

STEP_CA_PASSWORD="$(openssl rand -base64 32 | tr -d '\n')"

#
# BasicAuth
#

if command -v htpasswd >/dev/null; then

    BASIC_AUTH="$(htpasswd -nbB admin "${STEP_CA_PASSWORD}" | cut -d':' -f2)"

else

    echo
    echo "WARNING: htpasswd not installed."
    echo "BasicAuth password not generated."

    BASIC_AUTH=""

fi

#
# update env
#

update_env() {

    local key="$1"
    local value="$2"

    if grep -q "^${key}=" "${ENV_FILE}"; then

        sed -i.bak "s#^${key}=.*#${key}=${value}#" "${ENV_FILE}"

    else

        echo "${key}=${value}" >> "${ENV_FILE}"

    fi

}

update_env STEP_CA_PASSWORD "${STEP_CA_PASSWORD}"
update_env TRAEFIK_BASIC_AUTH "admin:${BASIC_AUTH}"

rm -f "${ENV_FILE}.bak"

echo
echo "Bootstrap completed."

echo
echo "Next steps:"
echo
echo "  1. edit .env"
echo "  2. run scripts/render.sh"
echo "  3. docker compose up -d"

echo
