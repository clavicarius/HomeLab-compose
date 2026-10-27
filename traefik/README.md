# Traefik Stack (Homelab)

Dieser Ordner enthaelt den zentralen Traefik Reverse-Proxy-Stack fuer das Homelab.

Traefik veroeffentlicht Webservices ueber Hostnamen wie `service.home.arpa` und nutzt Docker-Labels zur automatischen Service-Erkennung.

Weitere Architekturdetails: [docs/network-architecture.md](../docs/network-architecture.md)

---

## Inhalt

- `compose.yml` - Traefik-Stack fuer den regulaeren Betrieb
- `compose.ci.yml` - CI-Override
- `.env.example` - Beispielkonfiguration fuer servicespezifische Variablen
- `certs/` - optionale lokale Zertifikate
- `config/` - Laufzeitkonfiguration
- `letsencrypt/` - ACME-Zertifikatsspeicher

---

## Konfiguration

Gemeinsame Konfiguration aus `.env.common.example` kopieren und Netzwerkwerte
sowie eine eigene Domain setzen. Erzeuge anschliessend die service-spezifische
`.env` mit `create-env.sh` und trage dort einen Hetzner-DNS-API-Token mit
Berechtigung zum Aendern der Domainzone ein. Die `.env` ist fuer den Stack
erforderlich.

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

Traefik veroeffentlicht HTTP auf Port 80 und HTTPS auf Port 443. Der Host-Port
`${TRAEFIK_DASHBOARD_PORT}` (Standard: 8088) wird auf Container-Port 8080
gemappt; die API ist jedoch nicht insecure freigeschaltet. Das Dashboard wird
ueber die HTTPS-Route `https://traefik.home.arpa/dashboard/` bereitgestellt.
Diese Host-Regel ist derzeit in `config/dashboard.yml` fest eingetragen. Wenn
du eine andere Domain verwendest, passe sie dort ebenfalls an und richte einen
DNS-Rewrite auf die Traefik-IP ein.

## Let's Encrypt

Der Compose-Stack ist fuer ein Wildcard-Zertifikat per DNS-Challenge bei
Hetzner konfiguriert. Setze `HOMELAB_DOMAIN` auf eine eigene oeffentliche
Domain, `HOMELAB_EMAIL` auf eine erreichbare Adresse und `HETZNER_API_TOKEN`
in `traefik/.env`. Traefik speichert ACME-Daten unter
`TRAEFIK_LETSENCRYPT_PATH`; halte diesen Pfad persistent und sichere ihn.

Eine interne Domain wie `home.arpa` kann nicht von Let's Encrypt zertifiziert
werden. Verwende dafuer stattdessen ein lokal vertrautes mkcert-Zertifikat.

---

## Typische Validierung

```bash
# DNS-Rewrite pruefen
nslookup gitea.home.arpa 192.168.178.252

# HTTP Redirect / Routing pruefen
curl -I http://adguard.home.arpa
curl -k https://adguard.home.arpa
```

Wenn ein Service nicht geroutet wird, zuerst die Traefik-Labels im jeweiligen `compose.yml` und die DNS-Rewrites in AdGuard pruefen.

---

## Mkcert TLS (optional)

Fuer eine interne Wildcard-Zertifikatskette ohne Browser-Warnungen kann
`mkcert` verwendet werden. Die lokale CA muss auf allen Clients vertraut sein.
Die mitgelieferte `config/tls.yml` referenziert `certs/wildcard.pem` und
`certs/wildcard-key.pem` als Standardzertifikat. Diese Dateien muessen daher
vorhanden sein; ohne sie meldet der Traefik-File-Provider einen Ladefehler.
Wenn ausschliesslich Let's Encrypt verwendet wird, entferne oder passe den
`defaultCertificate`-Abschnitt in `config/tls.yml` an.

1. Zertifikate erzeugen:

```bash
mkcert home.arpa "*.home.arpa"
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
