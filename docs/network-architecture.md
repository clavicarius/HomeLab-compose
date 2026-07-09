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
| Traefik | 192.168.178.225 | implementiert (`poly-php`) |
| Portainer | 192.168.178.250 | geplant |
| AdGuard Home | 192.168.178.252 | implementiert (`adguard`) |

Weitere Container-IPs im Bereich `192.168.178.225 – 254` vergeben.

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
- Portainer (geplant)
- WordPress (geplant)
- Paperless (geplant)
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
TRAEFIK_TLS_ENABLED=true
```

Standardmäßig sind beide Werte `false` — Services sind dann nur direkt über ihre LAN-IP bzw. Host-Ports erreichbar.

---

# 9. Traefik

## Container

Traefik läuft im `poly-php`-Stack (`poly-php/compose.yml`).

## LAN-IP

```text
192.168.178.225
```

## Ports

| Port | Zweck |
|------|-------|
| 80/tcp | HTTP |
| 443/tcp | HTTPS |
| 8088/tcp | Dashboard (Host-Port → Container 8080) |

## Zugriffe

| Zweck | URL |
|-------|-----|
| Dashboard | http://192.168.178.99:8088 |
| HTTPS-Services | https://<service>.homelab.internal |

Das Dashboard ist über den auf dem Host publizierten Port erreichbar. HTTPS-Services laufen über die Traefik-LAN-IP, sobald DNS-Rewrites gesetzt sind.

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
- lokale Namensauflösung für `*.homelab.internal`

---

# 13. Lokale Domainstruktur

## Interne Domain

```text
homelab.internal
```

Domain und E-Mail werden zentral in `.env.common` konfiguriert:

```env
HOMELAB_DOMAIN=homelab.internal
HOMELAB_EMAIL=admin@homelab.internal
```

## Geplante Services

| Domain | Ziel |
|--------|------|
| adguard.homelab.internal | Traefik → AdGuard |
| portainer.homelab.internal | Traefik → Portainer |
| paperless.homelab.internal | Traefik → Paperless |
| wordpress.homelab.internal | Traefik → WordPress |
| php56.homelab.internal | Traefik → PHP 5.6 |
| php74.homelab.internal | Traefik → PHP 7.4 |
| php85.homelab.internal | Traefik → PHP 8.5 |
| phpmyadmin.homelab.internal | Traefik → phpMyAdmin |
| drucker.homelab.internal | Drucker (direkt) |

---

# 14. DNS-Rewrites in AdGuard

Webservices zeigen auf die Traefik-IP. Der Drucker wird direkt angesprochen.

## DNS-Einträge

```text
adguard.homelab.internal       -> 192.168.178.225
portainer.homelab.internal     -> 192.168.178.225
paperless.homelab.internal     -> 192.168.178.225
wordpress.homelab.internal     -> 192.168.178.225
php56.homelab.internal         -> 192.168.178.225
php74.homelab.internal         -> 192.168.178.225
php85.homelab.internal         -> 192.168.178.225
phpmyadmin.homelab.internal    -> 192.168.178.225
drucker.homelab.internal       -> 192.168.178.20
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
  - "traefik.http.routers.adguard.tls=${TRAEFIK_TLS_ENABLED}"
  - "traefik.http.services.adguard.loadbalancer.server.port=3000"
```

## Routing-Übersicht

| Domain | Zielcontainer | Port |
|--------|-----------------|------|
| adguard.homelab.internal | adguard-homelab | 3000 |
| portainer.homelab.internal | portainer | 9000 |
| paperless.homelab.internal | paperless | 8000 |
| wordpress.homelab.internal | wordpress | 80 |
| php85.homelab.internal | lamp-php85 | 80 |

---

# 16. Sicherheitsprinzipien

## Grundsätze

- DNS und Webservices über feste, dokumentierte IPs
- Veröffentlichung von Webservices nur über Traefik
- `TRAEFIK_ENABLED=false` bis ein Service bewusst freigegeben wird
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
5. `TRAEFIK_ENABLED=true` setzen (wenn über Traefik erreichbar)
6. Service testen

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
         |         |    Portainer  Paperless   WordPress
         |         |    (geplant)  (geplant)   (geplant)
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
- saubere lokale Domains unter `homelab.internal`
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
5. `.env.common` anlegen (aus `.env.common.example`)
6. macvlan-Netzwerk erstellen (`./scripts/create-macvlan.sh`)
7. AdGuard deployen
8. AdGuard einrichten (DNS Port 53)
9. FRITZ!Box DNS auf AdGuard-IP umstellen
10. DNS-Rewrites anlegen
11. Traefik-Stack deployen (`poly-php`)
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
├── poly-php/
│   ├── compose.yml
│   └── docs/traefik.md
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
| adguard.homelab.internal | 192.168.178.225 |
| portainer.homelab.internal | 192.168.178.225 |
| paperless.homelab.internal | 192.168.178.225 |
| wordpress.homelab.internal | 192.168.178.225 |
| php56.homelab.internal | 192.168.178.225 |
| php74.homelab.internal | 192.168.178.225 |
| php85.homelab.internal | 192.168.178.225 |
| phpmyadmin.homelab.internal | 192.168.178.225 |
| drucker.homelab.internal | 192.168.178.20 |

---

# 29. Traefik deployen

## Starten

```bash
cd poly-php
docker compose up -d
```

## Traefik aktivieren

In `.env.common`:

```env
TRAEFIK_ENABLED=true
TRAEFIK_TLS_ENABLED=true
```

Container neu starten:

```bash
docker compose up -d
```

Weitere Details: [poly-php/docs/traefik.md](../poly-php/docs/traefik.md)

---

# 30. Beispiel Compose-Standard für neue Services

```yaml
services:
  service-name:
    image: image-name
    container_name: service-name
    restart: unless-stopped
    volumes:
      - ./data:/data
    networks:
      homelab_macvlan:
        ipv4_address: ${SERVICE_IP}
    labels:
      - "traefik.enable=${TRAEFIK_ENABLED}"
      - "traefik.http.routers.service-name.rule=Host(`${SERVICE_HOST}.${HOMELAB_DOMAIN}`)"
      - "traefik.http.routers.service-name.entrypoints=websecure"
      - "traefik.http.routers.service-name.tls=${TRAEFIK_TLS_ENABLED}"
      - "traefik.http.services.service-name.loadbalancer.server.port=8080"

networks:
  homelab_macvlan:
    external: true
```

---

# 31. Backup-Strategie

## Zu sichernde Daten

Compose-Verzeichnisse mit persistenten Volumes:

```text
adguard/conf/
adguard/work/
poly-php/
```

## Backup-Ziele

Empfohlen:

- externe USB-Festplatte
- zweite NAS
- verschlüsseltes Cloud-Backup

## Backup-Frequenz

| Daten | Frequenz |
|-------|----------|
| Konfiguration | täglich |
| Dokumente | täglich |
| Medien | wöchentlich |

---

# 32. Update-Strategie

## Container aktualisieren

Im jeweiligen Verzeichnis:

```bash
docker compose pull
docker compose up -d
```

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
nslookup portainer.homelab.internal 192.168.178.252
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
- `TRAEFIK_ENABLED=false` bis Service freigegeben
- SSH nur intern erreichbar

## Nicht empfohlen

- direkte Portfreigaben ins Internet
- ungesicherte Admin-Oberflächen
- Standardpasswörter

---

# 35. Erweiterung neuer Services

Neue Dienste werden standardisiert integriert.

## Ablauf

1. Compose-Datei erstellen
2. `homelab_macvlan` einbinden
3. Traefik-Labels setzen
4. Service starten
5. DNS-Rewrite anlegen (→ `192.168.178.225`)
6. `TRAEFIK_ENABLED=true` setzen
7. Funktion testen

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
