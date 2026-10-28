# WordPress

Independent Docker Compose stack for WordPress and MariaDB. WordPress is
available through Traefik at `https://${WORDPRESS_HOST}.${HOMELAB_DOMAIN}` and
is also reachable at its static macvlan address. The database is only reachable
on the stack's private network.

## Configure

Copy `.env.example` to `.env`, set `WORDPRESS_IP` to an unused address on the
homelab macvlan network, and replace both database passwords with private
values. Generate passwords with:

```bash
openssl rand -hex 32
```

The shared `.env.common` file supplies the homelab domain, timezone, Traefik
settings, and Docker network name. WordPress files and MariaDB data are stored
at the paths selected by `WORDPRESS_DATA_PATH` and
`WORDPRESS_DB_DATA_PATH`.

## Start and maintain

From this directory:

```bash
docker compose pull
docker compose up -d
```

Complete the WordPress setup at `https://${WORDPRESS_HOST}.${HOMELAB_DOMAIN}`.
Back up both persistent data paths together. To update, run `docker compose
pull` followed by `docker compose up -d`. Stop the stack with `docker compose
down`; persistent data is retained.
