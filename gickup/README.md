# Gickup

Docker Compose stack for backing up repositories from the Gitea service with
[Gickup](https://github.com/cooperspencer/gickup).

## Setup

Gickup and Gitea must use the shared `homelab_macvlan` network. Start Gitea
before Gickup so the `gitea` network alias is available.

From the repository root, create the shared environment file if needed:

```bash
cp .env.common.example .env.common
```

Then, from this directory, create and configure the Gickup environment:

```bash
cp .env.example .env
```

Set `GITEA_TOKEN` to a Gitea access token that can read the repositories to
back up. Keep the token in the ignored `.env` file; do not commit it. Change
`GITEA_URL` if Gitea is reachable at a different URL.

Start Gickup:

```bash
../scripts/docker-up.sh
```

## Backups

Gickup creates local mirror clones in `./backups`, organized by Gitea host,
owner, and repository. Backups run daily at 23:00 (11 p.m.) by default; set
`GICKUP_CRON` to change the schedule. The container uses the `TZ` value from
the shared environment file (UTC if unset).

To restore a repository, clone its mirror from `backups/` or push it to a Git
server. Logs are available with `docker compose logs -f`.
