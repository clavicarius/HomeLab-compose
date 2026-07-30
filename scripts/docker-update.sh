#!/bin/bash
# docker-update.sh
# Pulls the latest Docker images, stops the stack, and restarts it.
#
# Usage:
#   ./scripts/docker-update.sh
#   (run from the service directory, e.g. adguard/ or gitea/)
#
# Dependencies:
#   - Docker Compose v2
#   - .env.common in the repository root
#   - .env in the current service directory
#
# Workflow:
#   1. docker compose pull  — fetch the latest image versions
#   2. docker compose down  — stop and remove running containers
#   3. docker compose up -d — start containers with updated images
#
# See also:
#   docker-up.sh    — start the stack without pulling
#   docker-down.sh  — stop the stack only
#   docs/scripts.md — overview of all helper scripts

docker compose --env-file ../.env.common --env-file .env pull
docker compose --env-file ../.env.common --env-file .env down
docker compose --env-file ../.env.common --env-file .env up -d
