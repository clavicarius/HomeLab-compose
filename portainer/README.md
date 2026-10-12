# Portainer

Standalone Docker Compose stack for managing the homelab's Docker environment
with Portainer CE.

## Requirements

* Docker Engine and Docker Compose
* The shared `homelab_macvlan` network (see
  [network-architecture.md](../docs/network-architecture.md))
* A merged `.env` file in this directory

Create the environment file from the shared and Portainer-specific examples:

```bash
cd portainer
../scripts/create-env.sh
```

The local `.env.example` sets `PORTAINER_HOST` and `PORTAINER_IP`; adjust the IP
if needed. Shared settings, including `NETWORK_NAME`, `HOMELAB_DOMAIN`, and
Traefik options, come from `.env.common`.

## Start

```bash
docker compose pull
docker compose up -d
```

Portainer is available directly at `https://${PORTAINER_IP}:9443` or, when
Traefik is enabled and DNS points to the Traefik IP, at
`https://${PORTAINER_HOST}.${HOMELAB_DOMAIN}`.

The Traefik route forwards to Portainer's HTTP interface on port 9000. For
direct access from the LAN, the HTTPS interface listens on port 9443.

## Persistent data

Portainer's configuration and database are stored in the named Docker volume
`portainer_data`. The Docker socket is mounted to let Portainer manage the
local Docker Engine.
