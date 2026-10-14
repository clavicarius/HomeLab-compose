#!/bin/bash
# docker-up.sh
# Starts the Docker Compose stack in detached mode.
#
# Usage:
#   ./scripts/docker-up.sh
#   ./scripts/docker-up.sh --build
#   (run from the service directory, e.g. adguard/ or gitea/)
#
# Dependencies:
#   - Docker Compose v2
#   - Python 3
#   - .env.common in the repository root
#   - .env in the current service directory
#
# See also:
#   docker-down.sh    — stop the stack
#   docker-update.sh  — pull latest images and restart
#   docs/scripts.md   — overview of all helper scripts

python3 ../scripts/docker_compose.py --env-file ../.env.common --env-file .env up -d "$@"
