#!/bin/bash
# docker-down.sh
# Stops the running Docker Compose stack.
#
# Usage:
#   ./scripts/docker-down.sh
#   (run from the service directory, e.g. adguard/ or gitea/)
#
# Dependencies:
#   - Docker Compose v1 / v2
#
# See also:
#   docker-up.sh      — start the stack
#   docker-update.sh  — pull latest images and restart
#   docs/scripts.md   — overview of all helper scripts

docker-compose down
