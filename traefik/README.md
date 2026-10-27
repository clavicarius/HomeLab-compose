# Traefik Stack (Homelab)

Dieser Ordner enthaelt den zentralen Traefik Reverse-Proxy-Stack fuer das Homelab.

Traefik veroeffentlicht Webservices ueber Hostnamen wie `service.${HOMELAB_DOMAIN}` und nutzt Docker-Labels zur automatischen Service-Erkennung.

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

1. `HOMELAB_DOMAIN` in `.env.common` auf die eigene Homelab-Domain setzen (z. B. `home.example.com`).
2. Fuer ein gueltiges Let’s-Encrypt-Zertifikat muss die Domain `example.com` dem Benutzer gehoeren bzw. muessen die benoetigten DNS-Berechtigungen fuer diese Zone vorliegen. In Hetzner DNS einen API-Token mit Lese- und Schreibzugriff auf die DNS-Zone `example.com` anlegen und ausschliesslich in `traefik/.env` als `HETZNER_API_TOKEN` eintragen. Den Token niemals committen.
3. Den persistenten ACME-Speicher vorbereiten:

   ```bash
   mkdir -p letsencrypt
   touch letsencrypt/acme.json
   chmod 600 letsencrypt/acme.json
   ```

Traefik verwendet Hetzner fuer die DNS-01-Challenge und fordert automatisch ein Zertifikat fuer `${HOMELAB_DOMAIN}` und `*.${HOMELAB_DOMAIN}` an. Fuer die Challenge muessen die passenden DNS-Eintraege in Hetzner verwaltet werden koennen. `letsencrypt/acme.json` enthaelt den ACME-Zustand und ist vom Git-Repository ausgeschlossen; das Verzeichnis muss bei Backups und Host-Migrationen erhalten bleiben.

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

Vor den Befehlen den gleichen Domain-Wert wie in `.env.common` in der Shell setzen, zum Beispiel `export HOMELAB_DOMAIN=home.example.com`.

```bash
# DNS-Rewrite pruefen
nslookup adguard.${HOMELAB_DOMAIN} 192.168.178.252

# HTTPS-Routing und Zertifikatskette pruefen (ohne -k)
curl -I https://adguard.${HOMELAB_DOMAIN}
openssl s_client -showcerts -connect adguard.${HOMELAB_DOMAIN}:443 -servername adguard.${HOMELAB_DOMAIN} </dev/null 2>/dev/null | openssl x509 -noout -ext subjectAltName
```

Beim ersten HTTPS-Aufruf stellt Traefik das Zertifikat aus. Die Ausgabe von `openssl` muss `${HOMELAB_DOMAIN}` und `*.${HOMELAB_DOMAIN}` als Subject Alternative Names enthalten. Traefik verwaltet die Erneuerung automatisch; der persistente ACME-Speicher muss daher auch bei Container-Updates und Neustarts eingebunden bleiben. Wenn ein Service nicht geroutet wird, zuerst die Traefik-Labels im jeweiligen `compose.yml` und die DNS-Rewrites in AdGuard pruefen.

---

## Mkcert TLS (optional)

Fuer rein interne Domains kann mkcert als Alternative zu Let’s Encrypt verwendet werden. Vor dem Befehl muss `HOMELAB_DOMAIN` wie oben in der Shell gesetzt sein. Die mkcert-Root-CA muss auf den zugreifenden Clients installiert werden.

1. Zertifikate erzeugen:

```bash
mkcert "${HOMELAB_DOMAIN}" "*.${HOMELAB_DOMAIN}"
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
