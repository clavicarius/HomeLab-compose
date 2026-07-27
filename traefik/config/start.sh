#!/usr/bin/env sh

set -eu

CONFIG_DIR="/config"

echo "==> Loading environment..."

if [ -f "${CONFIG_DIR}/.env" ]; then
    set -a
    . "${CONFIG_DIR}/.env"
    set +a
else
    echo "ERROR: ${CONFIG_DIR}/.env not found"
    exit 1
fi

required_vars="
TRAEFIK_HOST
HOMELAB_DOMAIN
TRAEFIK_ENTRYPOINT
"

echo "==> Checking required variables..."

for var in $required_vars; do
    eval value=\$$var

    if [ -z "${value}" ]; then
        echo "ERROR: Variable ${var} is not set."
        exit 1
    fi
done

echo "==> Rendering dynamic.yml..."

envsubst \
'${TRAEFIK_HOST}
${HOMELAB_DOMAIN}
${TRAEFIK_ENTRYPOINT}
${TRAEFIK_BASIC_AUTH}
${CERT_RESOLVER}' \
< "${CONFIG_DIR}/dynamic.yml.template" \
> "${CONFIG_DIR}/dynamic.yml"

echo "==> Generated dynamic.yml"

cat "${CONFIG_DIR}/dynamic.yml"

echo "==> Starting Traefik..."

exec traefik --configFile="${CONFIG_DIR}/traefik.yml"
