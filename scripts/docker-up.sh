#!/bin/bash
docker compose --env-file ../.env.common --env-file .env up -d
