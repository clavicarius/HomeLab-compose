#!/bin/bash
docker-compose pull
docker-compose down
docker compose --env-file ../.env.common --env-file .env up -d
