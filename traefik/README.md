# Traefik Stack (Homelab)

Dieser Ordner enthaelt den zentralen Traefik Reverse-Proxy-Stack fuer das Homelab.

Traefik veroeffentlicht Webservices ueber Hostnamen wie `service.homelab.internal` und nutzt Docker-Labels zur automatischen Service-Erkennung.

Weitere Architekturdetails: [docs/network-architecture.md](../docs/network-architecture.md)

---

## Inhalt

- `compose.yml` - Traefik-Stack fuer den regulaeren Betrieb
- `compose.ci.yml` - CI-Override
- `.env.example` - Beispielkonfiguration fuer servicespezifische Variablen
- `certs/` - Zertifikate
- `config/` - Laufzeitkonfiguration

---

## Konfiguration

Gemeinsame Konfiguration aus `.env.common.example` kopieren und Werte fuer Netzwerk, Traefik-IP, Dashboard-Port und Domain eintragen. Die servicespezifische `.env` ist optional und kann aus `.env.example` erstellt werden.

---

## Voraussetzungen

1. Docker / Docker Compose v2 installiert
2. Gemeinsame Konfiguration erstellt:

```bash
cp .env.common.example .env.common
```

3. macvlan-Netzwerk vorhanden:

```bash
../scripts/create-macvlan.sh
```

4. Service-spezifische `.env` im Ordner `traefik/` anlegen:

```bash
../scripts/create-env.sh
```

---

## Reihenfolge im Homelab

Empfohlene Startreihenfolge:

1. `adguard/` (DNS)
2. `traefik/` (Reverse Proxy)
3. Weitere Services mit Traefik-Labels (z. B. `gitea/`, `poly-php/`)

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

Traefik veroeffentlicht HTTP auf Port 80, HTTPS auf Port 443 und das Dashboard auf `${TRAEFIK_DASHBOARD_PORT}` (Standard: 8088).

---

## Typische Validierung

```bash
# DNS-Rewrite pruefen
nslookup gitea.homelab.internal 192.168.178.252

# HTTP Redirect / Routing pruefen
curl -I http://adguard.homelab.internal
curl -k https://adguard.homelab.internal
```

Wenn ein Service nicht geroutet wird, zuerst die Traefik-Labels im jeweiligen `compose.yml` und die DNS-Rewrites in AdGuard pruefen.

---

## Mkcert TLS (optional)

Fuer eine interne Wildcard-Zertifikatskette ohne Browser-Warnungen kann `mkcert` verwendet werden.

1. Zertifikate erzeugen:

```bash
mkcert homelab.internal "*.homelab.internal"
```

2. Die erzeugten Dateien nach `traefik/certs/` kopieren:

- `wildcard.pem`
- `wildcard-key.pem`

3. [traefik/config/tls.yml](config/tls.yml) bindet diese Dateien als Standardzertifikat ein.

4. Den Stack neu starten:

```bash
../scripts/docker-up.sh
```

5. Die mkcert-Root-CA auf den Clients importieren, die die Domains aufrufen sollen.
