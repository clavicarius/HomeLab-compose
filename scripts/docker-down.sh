#!/bin/bash
# docker-down.sh
# Stops the running Docker Compose stack.
#
# Usage:
#   ./scripts/docker-down.sh
#   (run from the service directory, e.g. adguard/ or gitea/)
#
# Dependencies:
#   - Docker Compose v2
#   - .env.common in the repository root
#   - .env in the current service directory
#
# See also:
#   docker-up.sh      — start the stack
#   docker-update.sh  — pull latest images and restart
#   docs/scripts.md   — overview of all helper scripts

docker compose --env-file ../.env.common --env-file .env down
