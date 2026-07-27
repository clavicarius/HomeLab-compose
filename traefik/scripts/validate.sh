#!/bin/sh

set -eu

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Checking environment..."

test -f "$BASE_DIR/.env" \
 || { echo ".env missing"; exit 1; }


for VAR in HOMELAB_DOMAIN TRAEFIK_HOST TRAEFIK_ENTRYPOINT
do
    grep -q "^${VAR}=" "$BASE_DIR/.env" \
    || {
        echo "Missing variable: $VAR"
        exit 1
    }
done


echo "Checking generated config..."

test -f "$BASE_DIR/config/traefik.yml" \
 || exit 1

test -f "$BASE_DIR/config/dynamic.yml" \
 || exit 1


echo "Checking compose..."

cd "$BASE_DIR"

docker compose config >/dev/null \
 || {
    echo "docker compose validation failed"
    exit 1
 }


echo "Validation OK"
