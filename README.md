# HomeLab Compose

A collection of Docker Compose configurations for self-hosted services and homelab environments.

## Overview

This repository contains Docker Compose stacks for deploying and maintaining various self-hosted applications. Each service is organized in its own directory and can be deployed independently.

The goals of this repository are to provide:

- Clean and maintainable Docker Compose configurations
- Reusable service definitions
- Simple deployment and updates
- A centralized collection of homelab infrastructure
- Consistent documentation and configuration standards

---

## Repository Structure

```text
.
├── scripts/
│   ├── create-mcvlan.sh
│   ├── remove-mcvlan.sh
│   └── ...
├── service-a/
│   ├── compose.yaml
│   ├── .env.example
│   └── README.md
├── service-b/
│   ├── compose.yaml
│   └── README.md
└── README.md
```

Each service directory should contain:

- `compose.yaml` – Docker Compose configuration
- `.env.example` – Example environment variables (optional)
- `README.md` – Service-specific documentation

The `scripts/` directory contains helper scripts for managing the shared infrastructure.

---

## Networking

All Compose projects share a single external Docker **macvlan** network.

### Network Configuration

| Property | Value |
|----------|-------|
| Network Name | `homelab_mcvlan` |
| Driver | `macvlan` |
| Subnet | 192.168.178.224/27 |
| Gateway | 192.168.178.1 |

The network is created **once** and then shared by all Compose projects and can be configured via `.env.common`.

Example:

```yaml
networks:
  homelab_mcvlan:
    external: true
```

### Static IP Addresses

Services connected to the macvlan network should use fixed IP addresses (`192.168.178.225 - 192.168.178.254`).

Example:

```yaml
services:
  example:
    networks:
      homelab_mcvlan:
        ipv4_address: 192.168.178.235
```

Using static IP addresses ensures that services remain permanently reachable and avoids IP conflicts across different Compose projects.

---

## Included Compose Configurations

| Service | Description | Documentation |
|---------|-------------|---------------|
| `poly-php` | Portable Docker-based development environment for testing multiple PHP versions simultaneously. | [poly-php/README.md](poly-php/README.md) |
| `adguard` | Docker Compose project for running AdGuard Home in a homelab environment. | [adguard/README.md](adguard/README.md) |

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/clavicarius/homelab-compose.git
cd homelab-compose
```

### 2. Create the shared macvlan network

Configure the network settings in your `.env` file and run:

```bash
./scripts/create-mcvlan.sh
```

This only needs to be done once.

### 3. Navigate to the desired service

```bash
cd <service>
```

### 4. Copy the example environment file

If the service provides one:

```bash
cp .env.example .env
```

### 5. Start the service

```bash
docker compose up -d
```

---

## Conventions

- One service per directory
- One `README.md` per service
- Store secrets outside version control
- Prefer named volumes for persistent data
- Pin image versions whenever possible
- Use the shared external `homelab_mcvlan` network
- Assign static IP addresses to services connected to the macvlan network

---

## License

This repository is licensed under the MIT License.
