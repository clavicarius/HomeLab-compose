# Paperless-ngx

Docker Compose stack for Paperless-ngx with PostgreSQL and Redis. Paperless is
available through Traefik at `https://paperless.home.arpa` by default; its
application port is not published directly on the host.

## Configure

Copy `.env.example` to `.env`, set `PAPERLESS_IP` to an unused address on the
homelab macvlan network, and replace the database password and secret key with
private values before starting the stack. Generate a secret key with:

```bash
openssl rand -hex 32
```

The shared `.env.common` file supplies the homelab domain, timezone, Traefik
settings, and Docker network name. `PAPERLESS_SCRIPT_PATH` selects the host
directory mounted for the consume scripts; it defaults to `./scripts`.

## Start and maintain

From this directory:

```bash
mkdir -p data media export consume dbdata redisdata
docker compose pull
docker compose up -d
```

Paperless stores documents in `media/`, watched imports in `consume/`, and
exports in `export/`. Application data is in `data/`; PostgreSQL and Redis use
Docker-managed volumes. Back up these directories and volumes together.

The scripts in `scripts/` are mounted read-only and configured as Paperless's
pre- and post-consume hooks. The pre-consume hook is an empty placeholder; the
post-consume hook prints the consumed document's metadata to the container log.
Keep custom hook scripts executable so Paperless can run them.

To update, run `docker compose pull` followed by `docker compose up -d`. Stop
the stack with `docker compose down`; persistent data is retained.
