# Traefik im Homelab

Diese Anleitung beschreibt den Betrieb des **Multi-PHP-Stacks** mit **Traefik als zentralen Reverse Proxy** im Homelab.

Traefik übernimmt die TLS-Terminierung und leitet Requests anhand des Hostnamens an die PHP-Container weiter.

Die Gesamtarchitektur ist in [docs/network-architecture.md](../../docs/network-architecture.md) dokumentiert.

---

# 1. Voraussetzungen

* macvlan-Netzwerk `homelab_macvlan` (siehe `./scripts/create-macvlan.sh`)
* `.env` via `../scripts/create-env.sh`
* AdGuard Home mit DNS-Rewrites für `*.homelab.internal → 192.168.178.225`

---

# 2. Traefik-Service

Traefik ist in `compose.yml` enthalten und erhält die feste LAN-IP `${TRAEFIK_IP}` (`192.168.178.225`).

```yaml
traefik:
  image: traefik:v3.0
  command:
    - "--providers.docker=true"
    - "--providers.docker.network=homelab_macvlan"
    - "--entrypoints.web.address=:80"
    - "--entrypoints.websecure.address=:443"
  ports:
    - "80:80"
    - "443:443"
    - "8088:8080"
  networks:
    homelab_macvlan:
      ipv4_address: ${TRAEFIK_IP}
```

---

# 3. Routing aktivieren

In `.env.common`:

```env
TRAEFIK_ENABLED=true
TRAEFIK_TLS_ENABLED=true
HOMELAB_DOMAIN=homelab.internal
```

Container neu starten:

```bash
docker compose up -d
```

Jeder PHP-Container trägt Traefik-Labels, z. B. für PHP 8.5:

```yaml
labels:
  - "traefik.enable=${TRAEFIK_ENABLED}"
  - "traefik.http.routers.php85.rule=Host(`php85.${HOMELAB_DOMAIN}`)"
  - "traefik.http.routers.php85.entrypoints=websecure"
  - "traefik.http.routers.php85.tls=${TRAEFIK_TLS_ENABLED}"
  - "traefik.http.services.php85.loadbalancer.server.port=80"
  - "traefik.docker.network=homelab_macvlan"
```

---

# 4. DNS (Homelab)

DNS-Rewrites in AdGuard Home anlegen:

```text
php56.homelab.internal      → 192.168.178.225
php74.homelab.internal      → 192.168.178.225
php85.homelab.internal      → 192.168.178.225
phpmyadmin.homelab.internal → 192.168.178.225
```

Die FRITZ!Box verteilt AdGuard (`192.168.178.252`) als DNS-Server an alle Clients.

---

# 5. Zugriff auf die Services

| Service | URL |
|---------|-----|
| PHP 5.6 | https://php56.homelab.internal |
| PHP 7.4 | https://php74.homelab.internal |
| PHP 8.5 | https://php85.homelab.internal |
| phpMyAdmin | https://phpmyadmin.homelab.internal |
| Traefik Dashboard | http://192.168.178.99:8088 |

---

# 6. Lokale Entwicklung ohne DNS

Für Tests ohne AdGuard-DNS stehen die direkten Host-Ports zur Verfügung:

| Service | URL |
|---------|-----|
| PHP 5.6 | http://localhost:8056 |
| PHP 7.4 | http://localhost:8074 |
| PHP 8.5 | http://localhost:8085 |
| phpMyAdmin | http://localhost:8080 |

Alternativ können Domains in der Hosts-Datei eingetragen werden:

```text
192.168.178.225 php56.homelab.internal
192.168.178.225 php74.homelab.internal
192.168.178.225 php85.homelab.internal
192.168.178.225 phpmyadmin.homelab.internal
```

Windows: `C:\Windows\System32\drivers\etc\hosts`  
Linux/macOS: `/etc/hosts`

---

# 7. Zertifikate

Für interne Domains erzeugt Traefik standardmäßig **selbstsignierte Zertifikate**. Browser zeigen daher eine Sicherheitswarnung.

Für vertrauenswürdige lokale Zertifikate kann später **mkcert** integriert werden.
