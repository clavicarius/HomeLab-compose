# Traefik Stack (Homelab)

Dieser Ordner enthaelt den zentralen Traefik Reverse-Proxy-Stack fuer das Homelab.

Traefik veroeffentlicht Webservices ueber Hostnamen wie `service.home.arpa` und nutzt Docker-Labels zur automatischen Service-Erkennung.

Weitere Architekturdetails: [docs/network-architecture.md](../docs/network-architecture.md)

---

## Inhalt

- `compose.yml` - Traefik-Stack fuer den regulaeren Betrieb
- `compose.ci.yml` - CI-Override
- `.env.example` - Beispielkonfiguration fuer servicespezifische Variablen
- `letsencrypt/` - persistenter ACME-Status und Zertifikate (nicht versioniert)
- `certs/` - optionale Zertifikate
- `config/` - Laufzeitkonfiguration

---

## Konfiguration

Gemeinsame Konfiguration aus `.env.common.example` kopieren und Werte fuer Netzwerk, Traefik-IP, Dashboard-Port und Domain eintragen. Die servicespezifische `.env` ist optional und kann aus `.env.example` erstellt werden.

Fuer Let’s Encrypt:

1. `HOMELAB_TLD` in `.env.common` auf die eigene Domain setzen (z. B. `example.de`). Daraus ergibt sich `HOMELAB_DOMAIN=home.${HOMELAB_TLD}`.
2. In Hetzner DNS einen API-Token mit Lese- und Schreibzugriff auf die DNS-Zone anlegen und ausschliesslich in `traefik/.env` als `HETZNER_API_TOKEN` eintragen. Den Token niemals committen.
3. Den persistenten ACME-Speicher vorbereiten:

   ```bash
   mkdir -p letsencrypt
   touch letsencrypt/acme.json
   chmod 600 letsencrypt/acme.json
   ```

Traefik verwendet Hetzner fuer die DNS-01-Challenge und fordert automatisch ein Zertifikat fuer `home.${HOMELAB_TLD}` und `*.home.${HOMELAB_TLD}` an. Fuer die Challenge muessen die passenden DNS-Eintraege in Hetzner verwaltet werden koennen. `letsencrypt/acme.json` enthaelt den ACME-Zustand und ist vom Git-Repository ausgeschlossen; das Verzeichnis muss bei Backups und Host-Migrationen erhalten bleiben.

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
nslookup adguard.home.example.de 192.168.178.252

# HTTPS-Routing und Zertifikatskette pruefen (ohne -k)
curl -I https://adguard.home.example.de
openssl s_client -showcerts -connect adguard.home.example.de:443 -servername adguard.home.example.de </dev/null 2>/dev/null | openssl x509 -noout -ext subjectAltName
```

Beim ersten HTTPS-Aufruf stellt Traefik das Zertifikat aus. Die Ausgabe von `openssl` muss `home.example.de` und `*.home.example.de` als Subject Alternative Names enthalten. Traefik verwaltet die Erneuerung automatisch; der persistente ACME-Speicher muss daher auch bei Container-Updates und Neustarts eingebunden bleiben. Wenn ein Service nicht geroutet wird, zuerst die Traefik-Labels im jeweiligen `compose.yml` und die DNS-Rewrites in AdGuard pruefen.

---

## Mkcert TLS (optional)

Fuer eine interne Wildcard-Zertifikatskette ohne Browser-Warnungen kann `mkcert` verwendet werden.

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
