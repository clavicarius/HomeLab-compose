# Traefik Homelab

This directory contains the standalone Traefik reverse-proxy stack for the
homelab. Traefik uses Docker labels to route HTTPS requests to enabled services
on the shared external network.

## Configuration

Copy the repository-level `.env.common.example` to `.env.common` and set the
network, Traefik IP, dashboard port, and domain values. The service-specific
`.env` is optional and can be created from `.env.example`.

## Start and stop

Create the shared macvlan network once, then start stacks in this order:

1. `adguard/`
2. `traefik/`
3. application stacks such as `gitea/` and `poly-php/`

From this directory, use the shared helper scripts:

```bash
../scripts/docker-up.sh
../scripts/docker-down.sh
../scripts/docker-update.sh
```

Traefik publishes HTTP on port 80, HTTPS on port 443, and its dashboard on
`${TRAEFIK_DASHBOARD_PORT}` (8088 by default).
