# network-architecture.md

## Ziel

Dieses Dokument beschreibt die Netzwerk- und Docker-Architektur für das Heimnetzwerk auf Basis einer FRITZ!Box und einer Synology NAS.

Ziele der Architektur:

- stabile und wartbare Netzwerkstruktur
- feste IP-Adressen für Infrastruktur und LAN-sichtbare Container
- saubere lokale DNS-Auflösung über AdGuard Home
- Zugriff auf Docker-Services über sprechende Domainnamen
- einfache Erweiterbarkeit neuer Container
- zentrale Veröffentlichung über Traefik
- Verzicht auf unnötige Komplexität (VLANs, zusätzliche Router, separate Heimnetz-Subnetze)

---

# 1. Netzwerkübersicht

## Heimnetz

Das gesamte Heimnetz nutzt ein einzelnes IPv4-Subnetz.

```text
Netzwerk:      192.168.178.0/24
Subnetzmaske: 255.255.255.0
```

## Router

```text
FRITZ!Box: 192.168.178.1
```

## IP-Bereiche

| Bereich | Verwendung |
|---------|------------|
| `192.168.178.1` | Gateway (FRITZ!Box) |
| `192.168.178.2 – 99` | Physische Infrastruktur (NAS, Drucker, …) |
| `192.168.178.100 – 199` | DHCP dynamisch |
| `192.168.178.225 – 254` | Docker-Container via macvlan |

Der macvlan-Bereich `192.168.178.224/27` liegt **im gleichen LAN** — es werden keine zusätzlichen Routen oder VLANs benötigt.

---

# 2. DHCP-Konfiguration

Die FRITZ!Box bleibt zentraler DHCP-Server.

## DHCP-Bereich

```text
192.168.178.100 - 192.168.178.199
```

Dieser Bereich ist ausschließlich für dynamische Clients vorgesehen:

- Smartphones
- Tablets
- Notebooks
- Gäste
- WLAN-Geräte
- temporäre Geräte

---

# 3. Statische IP-Adressen

Feste Infrastruktur erhält statische IPs bzw. DHCP-Reservierungen.

## Physische Geräte

| Gerät | IP-Adresse |
|-------|------------|
| FRITZ!Box | 192.168.178.1 |
| Synology NAS | 192.168.178.99 |
| Drucker | 192.168.178.20 |

Reservierter Bereich für weitere physische Geräte:

```text
192.168.178.2 - 99
```

## Docker-Container (macvlan)

Container mit fester LAN-IP werden über `homelab_macvlan` angebunden. Die Adressen werden in `.env.common` definiert.

| Dienst | IP-Adresse | Status |
|--------|------------|--------|
| Traefik | 192.168.178.225 | implementiert (`traefik`) |
| Gickup | 192.168.178.246 | implementiert (`gickup`) |
| Forgejo | 192.168.178.247 | implementiert (`forgejo`) |
| Gitea | 192.168.178.248 | implementiert (`gitea`) |
| Paperless-ngx | 192.168.178.249 | implementiert (`paperless`) |
| phpMyAdmin | 192.168.178.234 | implementiert (`poly-php`) |
| PHP 5.6 | 192.168.178.235 | implementiert (`poly-php`) |
| PHP 7.4 | 192.168.178.237 | implementiert (`poly-php`) |
| PHP 8.5 | 192.168.178.238 | implementiert (`poly-php`) |
| Portainer | 192.168.178.250 | implementiert (`portainer`) |
| AdGuard Home | 192.168.178.252 | implementiert (`adguard`) |
| Home Dashboard | 192.168.178.253 | implementiert (`dashboard`) |

Die Tabelle beschreibt die Beispielbelegung aus den Service-`.env.example`-
Dateien. IP-Adressen muessen im eigenen Netzwerk eindeutig sein und koennen
ueber die jeweilige `.env` angepasst werden.

---

# 4. Synology NAS

Die Synology NAS ist zentraler Docker-Host.

## NAS-Adresse

```text
192.168.178.99
```

## Aufgaben der NAS

Die NAS hostet:

- Docker (Container Manager)
- AdGuard Home (DNS, macvlan)
- Traefik (Reverse Proxy, macvlan)
- Portainer
- WordPress (geplant)
- Paperless-ngx
- weitere Container

---

# 5. Docker-Netzwerkstrategie

## Grundprinzip

Alle LAN-sichtbaren Container teilen sich ein externes **macvlan**-Netzwerk (`homelab_macvlan`). Container erhalten feste IPs aus dem Bereich `192.168.178.225 – 254` und sind für alle Geräte im Heimnetz direkt erreichbar.

Webservices werden über **Traefik** veröffentlicht. Traefik erkennt Container automatisch über Docker-Labels.

## Vorteile von macvlan im Heimnetz

- Container besitzen eigene LAN-IPs (z. B. AdGuard für DNS unabhängig von der NAS-IP)
- keine statischen Routen notwendig
- keine VLAN-Konfiguration
- einfache Erreichbarkeit von jedem Client im LAN
- Traefik routet per Hostname an die Container im selben Netzwerk

## Hinweis: Host ↔ Container

Der Docker-Host (Synology) kann macvlan-Container unter Umständen nicht direkt per Container-IP ansprechen. Für die Administration werden daher die LAN-IPs oder publizierte Host-Ports verwendet.

---

# 6. Gemeinsames Docker-Netzwerk (macvlan)

Alle Compose-Projekte nutzen ein einziges externes macvlan-Netzwerk.

## Netzwerk erstellen

Konfiguration in `.env.common` (Vorlage: `.env.common.example`), dann einmalig:

```bash
./scripts/create-macvlan.sh
```

## Netzwerkparameter

| Eigenschaft | Wert |
|-------------|------|
| Name | `homelab_macvlan` |
| Treiber | `macvlan` |
| Subnetz | `192.168.178.224/27` |
| Gateway | `192.168.178.1` |
| Parent-Interface | `eth0` (Synology: ggf. `ovs_eth0` / `bond0`) |

## Zweck

- Container erhalten feste LAN-IPs
- Traefik und Services kommunizieren im selben Layer-2-Netz
- AdGuard ist als DNS-Server für das gesamte LAN erreichbar

---

# 7. Docker Compose Standard

Jeder Service bindet das externe Netzwerk ein. Dienste mit fester IP erhalten `ipv4_address`.

## Netzwerkdefinition

```yaml
networks:
  homelab_macvlan:
    external: true
```

## Beispiel mit fester IP

```yaml
services:
  adguardhome:
    image: adguard/adguardhome:latest
    networks:
      homelab_macvlan:
        ipv4_address: ${ADGUARD_IP}

networks:
  homelab_macvlan:
    external: true
```

## Beispiel ohne feste IP

```yaml
services:
  paperless:
    image: ghcr.io/paperless-ngx/paperless-ngx
    networks:
      - homelab_macvlan

networks:
  homelab_macvlan:
    external: true
```

---

# 8. Reverse Proxy

## Lösung

Es wird **Traefik** als zentraler Reverse Proxy verwendet.

## Gründe

- automatische Service-Erkennung über Docker-Labels
- zentrale TLS-Terminierung
- deklarative Routing-Konfiguration in Compose-Dateien
- ein Reverse Proxy für alle Compose-Projekte

## Aktivierung

Traefik-Routing pro Service wird über Labels gesteuert. In `.env.common`:

```env
TRAEFIK_ENABLED=true
```

`TRAEFIK_ENABLED=false` deaktiviert das Traefik-Routing. Traefik ist fuer
Let's-Encrypt-Zertifikate per Hetzner-DNS-Challenge konfiguriert. Dafuer muessen
`HOMELAB_DOMAIN` auf eine eigene oeffentliche Domain und
`HETZNER_API_TOKEN` in `traefik/.env` gesetzt sein. Fuer interne Domains wie
`home.arpa` kann stattdessen ein lokal vertrautes mkcert-Zertifikat verwendet
werden.

---

# 9. Traefik

## Container

Traefik läuft als eigener Stack in `traefik/compose.yml`.

## LAN-IP

```text
192.168.178.225
```

## Ports

| Port | Zweck |
|------|-------|
| 80/tcp | HTTP |
| 443/tcp | HTTPS |
| 8088/tcp | publizierter Host-Port fuer Container-Port 8080 (Standardwert) |

## Zugriffe

| Zweck | URL |
|-------|-----|
| Technisches Traefik-Dashboard | `https://traefik.home.arpa/dashboard/` (Hostname in `traefik/config/dashboard.yml`) |
| Home Dashboard | `https://dashboard.<HOMELAB_DOMAIN>` |
| HTTPS-Services | `https://<service>.<HOMELAB_DOMAIN>` |

Das technische Dashboard wird ueber die konfigurierte HTTPS-Route bereitgestellt;
`api.insecure` ist deaktiviert. Der DNS-Rewrite fuer `traefik.home.arpa` muss
auf die Traefik-IP zeigen. Fuer eine andere Domain muss auch die feste Host-Regel
in `traefik/config/dashboard.yml` angepasst werden. HTTPS-Services laufen ueber
die Traefik-LAN-IP, sobald die passenden DNS-Rewrites gesetzt sind.

Optional kann fuer interne Domains ein mkcert-Wildcard-Zertifikat ueber `traefik/certs/` und `traefik/config/tls.yml` bereitgestellt werden, um Browser-Warnungen zu vermeiden.

---

# 10. DSM-Portanpassung

DSM darf nicht die Standardports 80/443 blockieren, da Traefik diese auf dem Docker-Host bindet.

## DSM-Konfiguration

DSM-Weboberfläche wird verschoben:

| Dienst | Port |
|--------|------|
| HTTP | 5000 |
| HTTPS | 5001 |

## Ergebnis

Ports 80 und 443 stehen vollständig für Traefik zur Verfügung.

---

# 11. DNS-Strategie

## Zentraler DNS-Server

AdGuard Home wird als lokaler DNS-Server für das gesamte Heimnetz verwendet.

## Ziel

Alle Geräte im Heimnetz sollen lokale Domains automatisch auflösen können. AdGuard läuft als Docker-Container mit fester LAN-IP und ist unabhängig von der NAS-IP als DNS erreichbar.

---

# 12. FRITZ!Box DNS-Konfiguration

Die FRITZ!Box verteilt per DHCP folgenden DNS-Server:

```text
192.168.178.252
```

Dadurch nutzen alle Clients automatisch:

- AdGuard Home (DNS-Filter, Rewrites)
- lokale Namensaufloesung fuer Hosts unter `HOMELAB_DOMAIN`

---

# 13. Home-Dashboard-DNS-Rewrite

Bis eine automatisierte AdGuard-Integration vorhanden ist, muss in AdGuard Home
ein DNS-Rewrite angelegt werden:

| Domain | Ziel |
|--------|------|
| `dashboard.<HOMELAB_DOMAIN>` | `192.168.178.225` |

Das Ziel ist die LAN-IP von Traefik, nicht die Dashboard-IP. Traefik routet die
Anfrage anhand des Hostnamens an den Dashboard-Container.

---

# 14. Lokale Domainstruktur

## Domain

Domain und E-Mail werden zentral in `.env.common` konfiguriert. Der
Beispielwert in `.env.common.example` ist `home.example.com`; fuer Let's Encrypt
muss hier eine eigene oeffentliche Domain verwendet werden. `home.arpa` eignet
sich fuer ein rein internes Setup mit lokal vertrautem Zertifikat.

```env
HOMELAB_DOMAIN=home.example.com
HOMELAB_EMAIL=admin@home.example.com
```

## Service-Hosts

| Host | Ziel | Status |
|------|------|--------|
| `adguard.<HOMELAB_DOMAIN>` | Traefik → AdGuard | konfiguriert |
| `dashboard.<HOMELAB_DOMAIN>` | Traefik → Home Dashboard | konfiguriert |
| `forgejo.<HOMELAB_DOMAIN>` | Traefik → Forgejo | konfiguriert |
| `gitea.<HOMELAB_DOMAIN>` | Traefik → Gitea | konfiguriert |
| `paperless.<HOMELAB_DOMAIN>` | Traefik → Paperless-ngx | konfiguriert |
| `php56`, `php74`, `php85`, `phpmyadmin` | Traefik → poly-php | konfiguriert |
| `portainer.<HOMELAB_DOMAIN>` | Traefik → Portainer | konfiguriert |
| `drucker.<HOMELAB_DOMAIN>` | Drucker (direkt) | beispielhaft |

---

# 15. DNS-Rewrites in AdGuard

Webservices zeigen auf die Traefik-IP. Der Drucker wird direkt angesprochen.

## DNS-Einträge

```text
adguard.<HOMELAB_DOMAIN>       -> 192.168.178.225
dashboard.<HOMELAB_DOMAIN>     -> 192.168.178.225
forgejo.<HOMELAB_DOMAIN>       -> 192.168.178.225
gitea.<HOMELAB_DOMAIN>         -> 192.168.178.225
paperless.<HOMELAB_DOMAIN>     -> 192.168.178.225
portainer.<HOMELAB_DOMAIN>     -> 192.168.178.225
php56.<HOMELAB_DOMAIN>         -> 192.168.178.225
php74.<HOMELAB_DOMAIN>         -> 192.168.178.225
php85.<HOMELAB_DOMAIN>         -> 192.168.178.225
phpmyadmin.<HOMELAB_DOMAIN>    -> 192.168.178.225
drucker.<HOMELAB_DOMAIN>       -> 192.168.178.20
```

---

# 15. Traefik Routing

Traefik leitet anhand des Hostnamens und der Docker-Labels an den Zielcontainer weiter.

## Beispiel: AdGuard

Labels in `adguard/compose.yml`:

```yaml
labels:
  - "traefik.enable=${TRAEFIK_ENABLED}"
  - "traefik.http.routers.adguard.rule=Host(`${ADGUARD_HOST}.${HOMELAB_DOMAIN}`)"
  - "traefik.http.routers.adguard.entrypoints=websecure"
  - "traefik.http.services.adguard.loadbalancer.server.port=9080"
```

## Routing-Übersicht

| Domain | Zielcontainer | Port |
|--------|-----------------|------|
| `adguard.<HOMELAB_DOMAIN>` | adguard-homelab | 9080 |
| `dashboard.<HOMELAB_DOMAIN>` | dashboard-homelab | 8080 |
| `forgejo.<HOMELAB_DOMAIN>` | forgejo | 3000 |
| `gitea.<HOMELAB_DOMAIN>` | gitea-homelab | 3000 |
| `paperless.<HOMELAB_DOMAIN>` | paperless-homelab | 8000 |
| `portainer.<HOMELAB_DOMAIN>` | portainer-homelab | 9000 |
| `php56`, `php74`, `php85` unter `<HOMELAB_DOMAIN>` | jeweiliger PHP-Container | 80 |
| `phpmyadmin.<HOMELAB_DOMAIN>` | lamp-phpmyadmin | 80 |

---

# 16. Sicherheitsprinzipien

## Grundsätze

- DNS und Webservices über feste, dokumentierte IPs
- Veröffentlichung von Webservices nur über Traefik
- Traefik-Routing nur fuer Services aktivieren, die darueber erreichbar sein sollen
- nur benötigte Ports exponieren
- feste Infrastruktur-IP-Adressen

## AdGuard-Administration

Die AdGuard-Weboberfläche ist unabhängig von Traefik erreichbar:

```text
http://192.168.178.252:3000
```

---

# 17. Erweiterbarkeit

Neue Container werden wie folgt integriert:

1. Compose-Datei erstellen
2. Service an `homelab_macvlan` anbinden (optional mit fester IP)
3. Traefik-Labels setzen
4. DNS-Rewrite in AdGuard anlegen (→ Traefik-IP)
5. DNS-Rewrite auf die Traefik-IP anlegen, wenn der Service geroutet wird
6. Healthcheck und Routing testen

---

# 18. Nicht vorgesehene Technologien

Folgende Technologien werden bewusst NICHT eingesetzt:

- mehrere Heimnetz-Subnetze
- VLANs
- statische Routen
- zusätzliche Router
- komplexe Firewallregeln
- Nginx Proxy Manager

Grund:

Für die vorhandene Infrastruktur nicht notwendig und unnötig wartungsintensiv.

---

# 19. Zielarchitektur

```text
                         Internet
                             |
                        FRITZ!Box
                      192.168.178.1
                             |
         ------------------------------------------------
         |                      |                       |
    WLAN / Clients         Synology NAS            Drucker
    DNS → .252             192.168.178.99          .20
         |                      |
         |               Docker (macvlan)
         |                      |
         |         ------------------------------------
         |         |                  |               |
         |    AdGuard (.252)     Traefik (.225)   weitere
         |         |                  |
         |         |         -------------------------
         |         |         |         |             |
         |         |    Portainer  Paperless   Dashboard
         |         |      Gitea     Forgejo     poly-php
         |         |
         +---- DNS-Abfragen
```

---

# 20. Ergebnis

Die Architektur bietet:

- zentrale DNS-Verwaltung über AdGuard mit fester LAN-IP
- zentrale Reverse-Proxy-Verwaltung über Traefik
- einfache Docker-Erweiterbarkeit über Labels
- stabile Netzwerkstruktur mit dokumentierten IP-Bereichen
- ein konfigurierbarer Domain-Suffix fuer die Services
- einfache Wartung
- geringe Komplexität

---

# 21. Erstinstallation

Dieses Kapitel beschreibt die empfohlene Reihenfolge der Grundinstallation.

## Reihenfolge

1. FRITZ!Box konfigurieren
2. Synology feste IP vergeben
3. DSM-Ports auf 5000/5001 umstellen
4. Docker aktivieren
5. `.env.common` anlegen (aus `.env.common.example`) und `HOMELAB_DOMAIN`
  setzen; fuer Let's Encrypt zusaetzlich den Hetzner-DNS-API-Token in
  `traefik/.env` konfigurieren
6. macvlan-Netzwerk erstellen (`./scripts/create-macvlan.sh`)
7. AdGuard deployen
8. AdGuard einrichten (DNS Port 53)
9. FRITZ!Box DNS auf AdGuard-IP umstellen
10. DNS-Rewrites anlegen
11. Traefik-Stack deployen (`traefik`)
12. `TRAEFIK_ENABLED=true` setzen
13. weitere Services deployen

---

# 22. FRITZ!Box konfigurieren

## DHCP-Bereich einstellen

FRITZ!Box:

```text
Heimnetz → Netzwerk → Netzwerkeinstellungen
```

DHCP-Bereich:

```text
192.168.178.100 - 192.168.178.199
```

---

## Synology feste IP zuweisen

```text
192.168.178.99
```

Aktivieren:

```text
Diesem Netzwerkgerät immer die gleiche IPv4-Adresse zuweisen
```

---

## DNS-Server verteilen

Nach erfolgreichem AdGuard-Setup:

```text
192.168.178.252
```

---

# 23. Synology vorbereiten

## Docker installieren

DSM:

```text
Paketzentrum → Container Manager installieren
```

(je nach DSM-Version „Docker“ oder „Container Manager“)

---

## SSH aktivieren

```text
Systemsteuerung → Terminal & SNMP → SSH aktivieren
```

---

## SSH-Verbindung

```bash
ssh user@192.168.178.99
```

## Parent-Interface entscheiden (Blocker)

Vor der Produktivnutzung muss das korrekte Synology-Parent-Interface live geprüft und in `.env.common` gesetzt werden.

Beispielprüfung:

```bash
ip -o link show
```

Typische Kandidaten:

- `eth0`
- `ovs_eth0`
- `bond0`

Danach in `.env.common` final festlegen:

```env
NETWORK_ADAPTER=<finales-interface>
```

---

# 24. Docker-Netzwerk erstellen

## Konfiguration

`.env.common` im Repository-Root anlegen:

```bash
cp .env.common.example .env.common
```

Wichtige Werte prüfen:

```env
SUBNET=192.168.178.224/27
GATEWAY=192.168.178.1
NETWORK_ADAPTER=eth0
ADGUARD_IP=192.168.178.252
TRAEFIK_IP=192.168.178.225
```

Auf der Synology das korrekte Parent-Interface setzen (z. B. `ovs_eth0`).

## Netzwerk anlegen

```bash
./scripts/create-macvlan.sh
```

Prüfen:

```bash
docker network ls
```

Erwartetes Ergebnis:

```text
homelab_macvlan
```

---

# 25. Repository-Struktur

```text
.
├── scripts/
│   ├── create-macvlan.sh
│   └── remove-macvlan.sh
├── adguard/
│   ├── compose.yml
│   └── README.md
├── traefik/
│   ├── compose.yml
│   └── README.md
├── poly-php/
│   ├── compose.yml
│   └── README.md
├── .env.common
└── .env.common.example
```

---

# 26. AdGuard Deployment

Siehe [adguard/README.md](../adguard/README.md).

## Starten

```bash
cd adguard
docker compose up -d
```

## Webinterface (Ersteinrichtung)

```text
http://192.168.178.252:3000
```

## Ersteinrichtung

| Einstellung | Wert |
|-------------|------|
| Admin-Webinterface | 3000 |
| DNS-Port | 53 |
| Upstream DNS | Quad9 / Cloudflare |

---

# 27. FRITZ!Box DNS umstellen

Nach erfolgreichem AdGuard-Setup:

```text
Heimnetz → Netzwerk → Netzwerkeinstellungen
```

Lokalen DNS setzen:

```text
192.168.178.252
```

Danach:

- Clients neu verbinden
- DHCP erneuern
- DNS testen

---

# 28. DNS-Rewrites konfigurieren

## AdGuard öffnen

```text
Filters → DNS rewrites
```

## Einträge

| Domain | Ziel |
|--------|------|
| `adguard.<HOMELAB_DOMAIN>` | `192.168.178.225` |
| `dashboard.<HOMELAB_DOMAIN>` | `192.168.178.225` |
| `forgejo.<HOMELAB_DOMAIN>` | `192.168.178.225` |
| `gitea.<HOMELAB_DOMAIN>` | `192.168.178.225` |
| `paperless.<HOMELAB_DOMAIN>` | `192.168.178.225` |
| `portainer.<HOMELAB_DOMAIN>` | `192.168.178.225` |
| `php56`, `php74`, `php85`, `phpmyadmin` unter `<HOMELAB_DOMAIN>` | `192.168.178.225` |
| `drucker.<HOMELAB_DOMAIN>` | `192.168.178.20` |

---

# 29. Traefik deployen

## Starten

```bash
cd traefik
docker compose up -d
```

## Traefik aktivieren

In `.env.common`:

```env
TRAEFIK_ENABLED=true
```

Container neu starten:

```bash
docker compose up -d
```

Weitere Details: [traefik/README.md](../traefik/README.md)

---

# 30. Beispiel Compose-Standard für neue Services

```yaml
services:
  service-name:
    image: image-name
    container_name: service-name
    restart: unless-stopped
    volumes:
      - ${SERVICE_DATA_PATH}:/data
    networks:
      homelab_macvlan:
        ipv4_address: ${SERVICE_IP}
    labels:
      - "traefik.enable=${TRAEFIK_ENABLED}"
      - "traefik.http.routers.service-name.rule=Host(`${SERVICE_HOST}.${HOMELAB_DOMAIN}`)"
      - "traefik.http.routers.service-name.entrypoints=websecure"
      - "traefik.http.services.service-name.loadbalancer.server.port=8080"
    # Jeder Service braucht einen aktivierten, zum Image passenden Healthcheck.
    # Stack-CI weist fehlende oder deaktivierte Healthchecks zurueck.

networks:
  homelab_macvlan:
    external: true
```

Der Healthcheck muss als Compose-Abschnitt `healthcheck` definiert sein und
einen tatsaechlichen Dienstzustand pruefen. Der genaue Befehl und Endpunkt
haengen vom verwendeten Image ab.

---

# 31. Backup-Strategie

## Zu sichernde Daten

Compose-Verzeichnisse mit persistenten Volumes:

```text
Die zu sichernden Host-Pfade stehen in den jeweiligen `*_PATH`-Variablen.
Im Beispiel umfassen sie unter anderem AdGuard-Konfiguration und -Daten,
Gitea-/Forgejo-Daten, Paperless-Daten und den Gickup-Backup-Ordner.
```

## Backup-Ziele

Empfohlen:

- externe USB-Festplatte
- zweite NAS
- verschlüsseltes Cloud-Backup

## Backup-Frequenz

Empfohlene Zielwerte (keine automatisch durchgesetzte Policy):

| Klasse | Beispiele | Ziel-RPO | Ziel-RTO |
|--------|-----------|----------|----------|
| Infrastruktur | AdGuard, Traefik, Gitea-Basiskonfiguration | 12h | 2h |
| Produktive Daten | Gitea-Repositories und Paperless-Daten | 4h | 1h |
| Niedrige Kritikalität | reproduzierbare Entwicklungs- oder Testdaten | 24h | 4h |

Zusätzlich:

- Restore-Test mindestens monatlich für jede Klasse
- Backup-Ziele redundant halten (mindestens 2 Ziele)

---

# 32. Update-Strategie

## Container aktualisieren

Im jeweiligen Verzeichnis:

```bash
../scripts/docker-update.sh
```

Die Hilfsskripte laden `.env.common` und die lokale `.env` gemeinsam.

## Nicht automatisch updaten

Automatische Updates vermeiden bei:

- Datenbanken
- Paperless
- WordPress
- produktiven Services

## Empfohlener Ablauf

1. Backup erstellen
2. Release Notes prüfen
3. Images aktualisieren
4. Container neu starten
5. Funktion testen

---

# 33. Troubleshooting

## DNS funktioniert nicht

Prüfen:

```bash
nslookup portainer.<HOMELAB_DOMAIN> 192.168.178.252
```

Erwartet:

```text
192.168.178.225
```

## Traefik liefert 502

Prüfen:

- Container läuft?
- im `homelab_macvlan`-Netzwerk?
- `TRAEFIK_ENABLED=true`?
- richtiger Zielport in Labels?
- Containername korrekt?

## Docker-Netzwerk prüfen

```bash
docker network inspect homelab_macvlan
```

IP-Adressen aller Container anzeigen:

```bash
./scripts/list-container-ips.sh
```

## Containerlogs anzeigen

```bash
docker logs container-name
```

---

# 34. Sicherheitsmaßnahmen

## Empfohlen

- starke Passwörter
- 2FA wo möglich
- regelmäßige Updates
- Traefik-Routing nur fuer beabsichtigte Services aktivieren
- SSH nur intern erreichbar
- Default-Scope: nur LAN, keine direkte externe Veröffentlichung
- Externe Erreichbarkeit nur explizit via VPN oder separat freigegebenem Zugriffspfad

## Nicht empfohlen

- direkte Portfreigaben ins Internet
- ungesicherte Admin-Oberflächen
- Standardpasswörter

---

# 35. Erweiterung neuer Services

Neue Dienste werden standardisiert integriert.

## Ablauf

1. Compose-Datei mit aktiviertem, image-gerechtem Healthcheck erstellen
2. `homelab_macvlan` einbinden, wenn eine LAN-IP oder Traefik benoetigt wird
3. Traefik-Labels und DNS-Rewrite einrichten, wenn der Service geroutet wird
4. Service starten und Healthcheck sowie Routing pruefen

---

# 36. Langfristige Zielarchitektur

Die Architektur soll langfristig:

- einfach wartbar
- modular erweiterbar
- reproduzierbar
- backupfähig
- dokumentiert

bleiben.

Komplexität wird bewusst minimiert. macvlan wird gezielt für LAN-sichtbare Container eingesetzt, nicht als generisches Netzwerk für alle denkbaren Szenarien.

---

# 37. Betriebsentscheidungen

| Entscheidungspunkt | Entscheidung | Ergebnis |
|---|---|---|
| Synology Parent-Interface für macvlan | Per Live-Test auf NAS ermitteln, danach fest in `.env.common` setzen | Blocker dokumentiert, Vorgehen festgelegt |
| Aktive Services | `adguard`, `dashboard`, `forgejo`, `gickup`, `gitea`, `paperless`, `poly-php`, `portainer` und `traefik` | Compose-Stacks sind im Repository vorhanden |
| TLS-Strategie | Hetzner-DNS-Challenge mit Let's Encrypt; mkcert optional fuer interne Domains | Entspricht der Traefik-Konfiguration |
| Backup- und Restore-Ziele | Serviceklassen mit RPO/RTO-Zielen | Zielwerte in Backup-Kapitel definiert |
| Exponierung nach außen | LAN-only als Default; extern nur explizit per VPN/gesonderter Freigabe | Sicherheitsprinzip erweitert |

## Betriebspruefung

1. `NETWORK_ADAPTER` fuer den Docker-Host pruefen
2. Service-IP-Adressen auf Eindeutigkeit pruefen
3. Nur benoetigte Services ueber Traefik veroeffentlichen
4. Persistente Daten und ACME-Speicher in Backups aufnehmen
