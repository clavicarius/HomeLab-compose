# Traefik Stack (Homelab)

Dieser Ordner enthaelt den zentralen Traefik Reverse-Proxy-Stack fuer das Homelab.

Traefik veroeffentlicht Webservices ueber Hostnamen wie `service.homelab.internal` und nutzt Docker-Labels zur automatischen Service-Erkennung.

Weitere Architekturdetails: [docs/network-architecture.md](../docs/network-architecture.md)

---

## Inhalt

- `compose.yml` - Traefik-Stack fuer den regulären Betrieb
- `compose.ci.yml` - CI-Override
- `certs/` - Zertifikate
- `config/` - Laufzeitkonfiguration
- `scripts/` - Helper fuer Initialisierung/Validierung
- `templates/` - Vorlagen fuer gerenderte Konfigurationsdateien

---

## Voraussetzungen

1. Docker / Docker Compose v2 installiert
2. Gemeinsame Konfiguration erstellt:

```bash
cp .env.common.example .env.common
```

3. macvlan-Netzwerk vorhanden:

```bash
./scripts/create-macvlan.sh
```

4. Service-spezifische `.env` im Ordner `traefik/` anlegen (falls benoetigt)

---

## Starten

Aus dem Ordner `traefik/`:

```bash
../scripts/docker-up.sh
```

Stoppen:

```bash
../scripts/docker-down.sh
```

Update:

```bash
../scripts/docker-update.sh
```

---

## Reihenfolge im Homelab

Empfohlene Startreihenfolge:

1. `adguard` (DNS)
2. `traefik` (Reverse Proxy)
3. weitere Services mit Traefik-Labels

---

## Typische Validierung

```bash
# DNS-Rewrite pruefen
nslookup gitea.homelab.internal 192.168.178.252

# HTTP Redirect / Routing pruefen
curl -I http://gitea.homelab.internal
curl -k https://gitea.homelab.internal
```

Wenn ein Service nicht geroutet wird, zuerst die Traefik-Labels im jeweiligen `compose.yml` und die DNS-Rewrites in AdGuard pruefen.
