#!/bin/sh

set -eu

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"

ENV_FILE="$BASE_DIR/.env"
TEMPLATE_DIR="$BASE_DIR/templates"
CONFIG_DIR="$BASE_DIR/config"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: .env fehlt"
    exit 1
fi

mkdir -p "$CONFIG_DIR"

set -a
. "$ENV_FILE"
set +a


render() {
    INPUT="$1"
    OUTPUT="$2"

    sed \
      -e "s|{{HOMELAB_DOMAIN}}|${HOMELAB_DOMAIN}|g" \
      -e "s|{{TRAEFIK_HOST}}|${TRAEFIK_HOST}|g" \
      -e "s|{{TRAEFIK_ENTRYPOINT}}|${TRAEFIK_ENTRYPOINT}|g" \
      -e "s|{{CERT_RESOLVER}}|${CERT_RESOLVER}|g" \
      -e "s|{{TRAEFIK_BASIC_AUTH}}|${TRAEFIK_BASIC_AUTH}|g" \
      -e "s|{{CERT_RESOLVER}}|${CERT_RESOLVER}|g" \
      -e "s|{{CERT_RESOLVER}}|${CERT_RESOLVER}|g" \
	  
      "$INPUT" > "$OUTPUT"

    echo "generated: $OUTPUT"
}


render \
 "$TEMPLATE_DIR/traefik.yml.tpl" \
 "$CONFIG_DIR/traefik.yml"


render \
 "$TEMPLATE_DIR/dynamic.yml.tpl" \
 "$CONFIG_DIR/dynamic.yml"

<<<<<<< HEAD
if [ -f "$CONFIG_DIR/tls.yml" ]; then
  printf '\n' >> "$CONFIG_DIR/dynamic.yml"
  cat "$CONFIG_DIR/tls.yml" >> "$CONFIG_DIR/dynamic.yml"
fi

=======
>>>>>>> origin/45-integration-branch

echo "Render complete."