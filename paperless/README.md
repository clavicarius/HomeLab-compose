# Paperless-ngx

Docker Compose stack for Paperless-ngx with PostgreSQL and Redis. Paperless is
available through Traefik at `https://paperless.home.arpa` by default; its
application port is not published directly on the host.

## Configure

Copy `.env.example` to `.env` and replace the database password and secret key
with private values before starting the stack. Generate a secret key with:

```bash
openssl rand -hex 32
```

The shared `.env.common` file supplies the homelab domain, timezone, Traefik
settings, and Docker network name.

## Start and maintain

From this directory:

```bash
docker compose pull
docker compose up -d
```

Paperless stores documents in `media/`, watched imports in `consume/`, and
exports in `export/`. Application data is in `data/`; PostgreSQL and Redis use
Docker-managed volumes. Back up these directories and volumes together.

To update, run `docker compose pull` followed by `docker compose up -d`. Stop
the stack with `docker compose down`; persistent data is retained.
