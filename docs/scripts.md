# Helper Scripts

All helper scripts are located in the `scripts/` directory at the repository root.
Each script contains a documentation header with description, usage, and related resources.

---

## Overview

| Script | Description |
|--------|-------------|
| [`create-macvlan.sh`](#create-macvlansh) | Creates the shared external macvlan Docker network |
| [`remove-macvlan.sh`](#remove-macvlansh) | Removes the shared external macvlan Docker network |
| [`list-container-ips.sh`](#list-container-ipssh) | Lists IP addresses of containers in the macvlan network |
| [`create-env.sh`](#create-envsh) | Creates a `.env` file by merging example configuration files |
| [`docker-up.sh`](#docker-upsh) | Starts a Docker Compose stack in detached mode |
| [`docker-down.sh`](#docker-downsh) | Stops a running Docker Compose stack |
| [`docker-update.sh`](#docker-updatesh) | Pulls latest images and restarts a Docker Compose stack |
| [`git-author-env.sh`](#git-author-envsh) | Loads git identity variables from `.git-author` into the shell |

---

## Network Scripts

### create-macvlan.sh

Creates the shared external macvlan Docker network (`homelab_macvlan`) on the Docker host.
This network is used by all Compose stacks in the repository and only needs to be created once.

**Usage** (run from the repository root):

```bash
./scripts/create-macvlan.sh
```

**Configuration** (read from `.env.common` and `.env`, with defaults):

| Variable | Default | Description |
|----------|---------|-------------|
| `NETWORK_NAME` | `homelab_macvlan` | Name of the Docker network |
| `SUBNET` | `192.168.178.224/27` | macvlan subnet CIDR |
| `GATEWAY` | `192.168.178.1` | Default gateway |
| `NETWORK_ADAPTER` | `eth0` | Host network interface |

The script exits without error if the network already exists.

**See also:** [remove-macvlan.sh](#remove-macvlansh) · [list-container-ips.sh](#list-container-ipssh) · [docs/network-architecture.md](network-architecture.md)

---

### remove-macvlan.sh

Removes the shared external macvlan Docker network (`homelab_macvlan`) from the Docker host.

**Usage** (run from the repository root):

```bash
./scripts/remove-macvlan.sh
```

**Configuration** (read from `.env.common` and `.env`, with defaults):

| Variable | Default | Description |
|----------|---------|-------------|
| `NETWORK_NAME` | `homelab_macvlan` | Name of the Docker network to remove |

The script exits without error if the network does not exist.
All containers using the network must be stopped before removal.

**See also:** [create-macvlan.sh](#create-macvlansh) · [docs/network-architecture.md](network-architecture.md)

---

### list-container-ips.sh

Lists the IP addresses of all running containers attached to the shared macvlan Docker network.

**Usage** (run from the repository root or any service directory):

```bash
./scripts/list-container-ips.sh
```

**Configuration** (read from `.env.common` and `.env`, with defaults):

| Variable | Default | Description |
|----------|---------|-------------|
| `NETWORK_NAME` | `homelab_macvlan` | Network to inspect |

**Example output:**

```text
CONTAINER                      NETWORK            IP ADDRESS
------------------------------ ------------------ ---------------
adguard-homelab                homelab_macvlan    192.168.178.252
gitea                          homelab_macvlan    192.168.178.248
```

**See also:** [create-macvlan.sh](#create-macvlansh) · [docs/network-architecture.md](network-architecture.md)

---

## Environment Scripts

### create-env.sh

Creates a local `.env` file by merging `.env.common.example` (repository root) and the
service-specific `.env.example` (current directory).

Use this when a stack expects a local `.env` file. The preferred runtime workflow is still
`docker compose --env-file ../.env.common --env-file .env ...` as used by `docker-up.sh`.

**Usage** (run from the service directory, e.g. `adguard/` or `gitea/`):

```bash
# Interactive — asks before overwriting an existing .env
../scripts/create-env.sh

# Non-interactive — overwrites without confirmation (CI/CD)
../scripts/create-env.sh --force
../scripts/create-env.sh -f
```

**Input files** (at least one must exist):

| File | Description |
|------|-------------|
| `../.env.common.example` | Shared configuration for all services |
| `.env.example` | Service-specific configuration |

**Exit codes:**

| Code | Meaning |
|------|---------|
| `0` | Success, or user aborted the overwrite prompt |
| `1` | No input file found |

**See also:** [docs/create-env.md](create-env.md)

---

## Docker Compose Scripts

These three scripts are convenience wrappers around Docker Compose commands.
Run them from the service directory (e.g. `adguard/`, `gitea/`, `poly-php/`).

### docker-up.sh

Starts the Docker Compose stack in detached mode using `.env.common` and the local `.env`.

```bash
cd adguard
../scripts/docker-up.sh
```

Recommended startup order for homelab routing:
1. `adguard`
2. `traefik`
3. routed services (`gitea`, `forgejo`, `poly-php`, ...)

**See also:** [docker-down.sh](#docker-downsh) · [docker-update.sh](#docker-updatesh)

---

### docker-down.sh

Stops the running Docker Compose stack and removes containers.

```bash
cd adguard
../scripts/docker-down.sh
```

Current implementation uses `docker-compose down`.

**See also:** [docker-up.sh](#docker-upsh)

---

### docker-update.sh

Pulls the latest Docker images, stops the stack, and restarts it with the updated images.

```bash
cd adguard
../scripts/docker-update.sh
```

**Workflow:**
1. `docker-compose pull` — fetch latest image versions
2. `docker-compose down` — stop and remove containers
3. `docker compose up -d` — start containers with updated images

Current implementation uses the local `.env` for `pull/down` and explicit dual env-file loading for `up`.

**See also:** [docker-up.sh](#docker-upsh) · [docker-down.sh](#docker-downsh)

---

## Git Scripts

### git-author-env.sh

Loads `GIT_AUTHOR_*` and `GIT_COMMITTER_*` environment variables from the `.git-author`
file in the repository root into the current shell session.

**Usage** (must be sourced, not executed):

```bash
source ./scripts/git-author-env.sh
git commit -m "your message"
```

**Input file:**

```text
.git-author  — personal identity file in the repository root (gitignored)
```

Copy from `.git-author.example` and fill in your values:

```bash
cp .git-author.example .git-author
```

**Exported variables:**

| Variable | Description |
|----------|-------------|
| `GIT_AUTHOR_NAME` | Commit author name |
| `GIT_AUTHOR_EMAIL` | Commit author email |
| `GIT_COMMITTER_NAME` | Committer name (falls back to `GIT_AUTHOR_NAME`) |
| `GIT_COMMITTER_EMAIL` | Committer email (falls back to `GIT_AUTHOR_EMAIL`) |

**Exit codes:**

| Code | Meaning |
|------|---------|
| `0` | Variables successfully exported |
| `1` | `.git-author` not found, or required variables are missing |

**See also:** [docs/git-author.md](git-author.md) · [.cursor/rules/git-commit-author.mdc](../.cursor/rules/git-commit-author.mdc)
