# network-architecture.md

## Ziel

Dieses Dokument beschreibt die geplante Netzwerk- und Docker-Architektur für das Heimnetzwerk auf Basis einer FRITZ!Box und einer Synology NAS.

Ziele der Architektur:

- stabile und wartbare Netzwerkstruktur
- feste IP-Adressen für Infrastruktur
- saubere lokale DNS-Auflösung
- Zugriff auf Docker-Services über sprechende Domainnamen
- einfache Erweiterbarkeit neuer Container
- zentrale Verwaltung über Reverse Proxy
- Verzicht auf unnötige Komplexität (VLANs, mehrere Heimnetz-Subnetze, macvlan)

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

## Geplante Struktur

| Gerät              | IP-Adresse        |
|-------------------|------------------|
| FRITZ!Box         | 192.168.178.1   |
| Synology NAS      | 192.168.178.99  |
| Drucker           | 192.168.178.20  |

Weitere Infrastrukturgeräte werden im Bereich reserviert:

```text
192.168.178.2 - 99
```

---

# 4. Synology NAS

Die Synology NAS ist zentraler Docker-Host.

## NAS-Adresse

```text
192.168.178.99
```

## Aufgaben der NAS

Die NAS hostet:

- Docker
- AdGuard Home
- Nginx Proxy Manager
- Portainer
- WordPress
- Paperless
- zukünftige Container

---

# 5. Docker-Netzwerkstrategie

## Grundprinzip

Es werden KEINE zusätzlichen Heimnetz-Subnetze eingerichtet.

Container laufen in internen Docker-Netzen und werden über Reverse Proxy veröffentlicht.

## Vorteile

- keine statischen Routen notwendig
- keine VLAN-Konfiguration
- keine macvlan-Komplexität
- einfache Wartbarkeit
- saubere Trennung
- geringes Konfliktpotenzial

---

# 6. Gemeinsames Docker-Proxy-Netzwerk

Alle öffentlich erreichbaren Container werden an ein gemeinsames externes Docker-Netzwerk angebunden.

## Netzwerk erstellen

```bash
docker network create homelab_proxy
```

## Zweck

Dieses Netzwerk ermöglicht:

- Kommunikation zwischen Reverse Proxy und Services
- servicebasierte Namensauflösung innerhalb Docker
- Trennung von internen Container-Netzen

---

# 7. Docker Compose Standard

Jeder Service bindet zusätzlich das externe Netzwerk ein.

## Beispiel

```yaml
networks:
  homelab_proxy:
    external: true
```

## Beispiel-Service

```yaml
services:
  paperless:
    image: ghcr.io/paperless-ngx/paperless-ngx

    networks:
      - homelab_proxy

networks:
  homelab_proxy:
    external: true
```

---

# 8. Reverse Proxy

## Lösung

Es wird Nginx Proxy Manager verwendet.

## Gründe

- einfache GUI
- unkomplizierte Verwaltung
- ideal für Heimnetz
- einfache HTTPS-Unterstützung
- zentrale Verwaltung aller Dienste

---

# 9. Nginx Proxy Manager

## Containerports

```text
80/tcp
81/tcp
443/tcp
```

## Zugriffe

| Zweck              | URL |
|-------------------|-----|
| Admin-Interface    | http://192.168.178.99:81 |

---

# 10. DSM-Portanpassung

DSM darf nicht die Standardports 80/443 blockieren.

## DSM-Konfiguration

DSM-Weboberfläche wird verschoben:

| Dienst | Port |
|--------|------|
| HTTP   | 5000 |
| HTTPS  | 5001 |

## Ergebnis

Ports 80 und 443 stehen vollständig für den Reverse Proxy zur Verfügung.

---

# 11. DNS-Strategie

## Zentraler DNS-Server

AdGuard Home wird als lokaler DNS-Server verwendet.

## Ziel

Alle Geräte im Heimnetz sollen lokale Domains automatisch auflösen können.

---

# 12. FRITZ!Box DNS-Konfiguration

Die FRITZ!Box verteilt per DHCP folgenden DNS-Server:

```text
192.168.178.99
```

Dadurch nutzen alle Clients automatisch:

- AdGuard Home
- lokale DNS-Rewrites
- zentrale Namensauflösung

---

# 13. Lokale Domainstruktur

## Interne Domain

```text
homelab.internal
```

## Geplante Services

| Domain | Ziel |
|--------|------|
| adguard.homelab.internal | Synology Reverse Proxy |
| portainer.homelab.internal | Synology Reverse Proxy |
| paperless.homelab.internal | Synology Reverse Proxy |
| wordpress.homelab.internal | Synology Reverse Proxy |
| drucker.homelab.internal | Drucker |

---

# 14. DNS-Rewrites in AdGuard

Alle Webservices zeigen auf die NAS-IP.

## DNS-Einträge

```text
adguard.homelab.internal     -> 192.168.178.99
portainer.homelab.internal   -> 192.168.178.99
paperless.homelab.internal   -> 192.168.178.99
wordpress.homelab.internal   -> 192.168.178.99
drucker.homelab.internal     -> 192.168.178.20
```

---

# 15. Reverse Proxy Routing

Der Reverse Proxy entscheidet anhand des Hostnamens über die Weiterleitung.

## Beispiele

| Domain | Zielcontainer |
|--------|---------------|
| adguard.homelab.internal | adguard:3000 |
| portainer.homelab.internal | portainer:9000 |
| paperless.homelab.internal | paperless:8000 |
| wordpress.homelab.internal | wordpress:80 |

---

# 16. Sicherheitsprinzipien

## Grundsätze

- keine direkten Container-IPs im LAN
- keine unnötigen offenen Ports
- zentrale Veröffentlichung nur über Reverse Proxy
- nur benötigte Ports exponieren
- feste Infrastruktur-IP-Adressen

---

# 17. Erweiterbarkeit

Neue Container werden wie folgt integriert:

1. Compose-Datei erstellen
2. Service an `homelab_proxy` anbinden
3. DNS-Record in AdGuard anlegen
4. Proxy-Host im Nginx Proxy Manager definieren
5. Service testen

---

# 18. Nicht vorgesehene Technologien

Folgende Technologien werden bewusst NICHT eingesetzt:

- mehrere Heimnetz-Subnetze
- VLANs
- macvlan
- statische Routen
- zusätzliche Router
- komplexe Firewallregeln

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
        --------------------------------
        |                              |
   WLAN / Clients                Synology NAS
                                 192.168.178.99
                                        |
                         --------------------------------
                         |              |               |
                    AdGuard      Nginx Proxy      Docker
                                        |
                ------------------------------------------------
                |               |               |              |
            Portainer      WordPress       Paperless      weitere
```

---

# 20. Ergebnis

Die Architektur bietet:

- zentrale DNS-Verwaltung
- zentrale Reverse-Proxy-Verwaltung
- einfache Docker-Erweiterbarkeit
- stabile Netzwerkstruktur
- saubere lokale Domains
- einfache Wartung
- geringe Komplexität
- hohe Zukunftssicherheit

---

# 21. Erstinstallation

Dieses Kapitel beschreibt die empfohlene Reihenfolge der Grundinstallation.

## Reihenfolge

1. FRITZ!Box konfigurieren
2. Synology feste IP vergeben
3. Docker aktivieren
4. gemeinsames Docker-Netzwerk erstellen
5. Nginx Proxy Manager deployen
6. AdGuard deployen
7. DNS in der FRITZ!Box umstellen
8. DNS-Rewrites anlegen
9. weitere Services deployen
10. Reverse Proxy Hosts konfigurieren

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

FRITZ!Box so konfigurieren, dass Clients AdGuard verwenden.

Später setzen auf:

```text
192.168.178.99
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

# 24. Docker-Netzwerke erstellen

## Gemeinsames Reverse-Proxy-Netzwerk

Einmalig ausführen:

```bash
docker network create homelab_proxy
```

Prüfen:

```bash
docker network ls
```

Erwartetes Ergebnis:

```text
homelab_proxy
```

---

# 25. Verzeichnisstruktur

Empfohlene Struktur auf der NAS:

```text
/docker
├── adguard
├── nginx-proxy-manager
├── portainer
├── paperless
├── wordpress
└── backups
```

---

# 26. Nginx Proxy Manager Deployment

## Verzeichnis erstellen

```bash
mkdir -p /docker/nginx-proxy-manager
cd /docker/nginx-proxy-manager
```

---

## docker-compose.yml

```yaml
services:
  npm:
    image: jc21/nginx-proxy-manager:latest
    container_name: nginx-proxy-manager

    restart: unless-stopped

    ports:
      - "80:80"
      - "81:81"
      - "443:443"

    volumes:
      - ./data:/data
      - ./letsencrypt:/etc/letsencrypt

    networks:
      - homelab_proxy

networks:
  homelab_proxy:
    external: true
```

---

## Starten

```bash
docker compose up -d
```

---

## Zugriff

```text
http://192.168.178.99:81
```

---

## Standard-Login

```text
E-Mail:    admin@example.com
Passwort:  changeme
```

Passwort sofort ändern.

---

# 27. AdGuard Deployment

## Verzeichnis erstellen

```bash
mkdir -p /docker/adguard
cd /docker/adguard
```

---

## docker-compose.yml

```yaml
services:
  adguard:
    image: adguard/adguardhome:latest
    container_name: adguard

    restart: unless-stopped

    ports:
      - "53:53/tcp"
      - "53:53/udp"
      - "3000:3000"

    volumes:
      - ./work:/opt/adguardhome/work
      - ./conf:/opt/adguardhome/conf

    networks:
      - homelab_proxy

networks:
  homelab_proxy:
    external: true
```

---

## Starten

```bash
docker compose up -d
```

---

## Webinterface

```text
http://192.168.178.99:3000
```

---

## Ersteinrichtung

Empfohlene Einstellungen:

| Einstellung | Wert |
|-------------|------|
| Admin-Webinterface | 3000 |
| DNS-Port | 53 |
| Upstream DNS | Quad9 / Cloudflare |

---

# 28. FRITZ!Box DNS umstellen

Nach erfolgreichem AdGuard-Setup:

```text
Heimnetz → Netzwerk → Netzwerkeinstellungen
```

Lokalen DNS setzen:

```text
192.168.178.99
```

Danach:
- Clients neu verbinden
- DHCP erneuern
- DNS testen

---

# 29. DNS-Rewrites konfigurieren

## AdGuard öffnen

```text
Filters → DNS rewrites
```

---

## Einträge

| Domain | Ziel |
|--------|------|
| adguard.homelab.internal | 192.168.178.99 |
| portainer.homelab.internal | 192.168.178.99 |
| paperless.homelab.internal | 192.168.178.99 |
| wordpress.homelab.internal | 192.168.178.99 |
| drucker.homelab.internal | 192.168.178.20 |

---

# 30. Proxy Hosts konfigurieren

## Beispiel: Portainer

### Domain

```text
portainer.homelab.internal
```

### Ziel

```text
http://portainer:9000
```

---

## Beispiel: Paperless

### Domain

```text
paperless.homelab.internal
```

### Ziel

```text
http://paperless:8000
```

---

## Beispiel: WordPress

### Domain

```text
wordpress.homelab.internal
```

### Ziel

```text
http://wordpress:80
```

---

# 31. Beispiel Compose-Standard

Empfohlene Basisstruktur für neue Services.

## Beispiel

```yaml
services:
  service-name:
    image: image-name

    container_name: service-name

    restart: unless-stopped

    volumes:
      - ./data:/data

    networks:
      - homelab_proxy

networks:
  homelab_proxy:
    external: true
```

---

# 32. Portainer Deployment

## Verzeichnis

```bash
mkdir -p /docker/portainer
cd /docker/portainer
```

---

## docker-compose.yml

```yaml
services:
  portainer:
    image: portainer/portainer-ce:latest

    container_name: portainer

    restart: unless-stopped

    ports:
      - "9000:9000"

    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./data:/data

    networks:
      - homelab_proxy

networks:
  homelab_proxy:
    external: true
```

---

## Starten

```bash
docker compose up -d
```

---

# 33. Backup-Strategie

## Zu sichernde Daten

Folgende Verzeichnisse sichern:

```text
/docker
```

Insbesondere:

```text
/docker/adguard
/docker/nginx-proxy-manager
/docker/portainer
/docker/paperless
/docker/wordpress
```

---

## Backup-Ziele

Empfohlen:

- externe USB-Festplatte
- zweite NAS
- verschlüsseltes Cloud-Backup

---

## Backup-Frequenz

| Daten | Frequenz |
|-------|-----------|
| Konfiguration | täglich |
| Dokumente | täglich |
| Medien | wöchentlich |

---

# 34. Update-Strategie

## Container aktualisieren

Im jeweiligen Verzeichnis:

```bash
docker compose pull
docker compose up -d
```

---

## Nicht automatisch updaten

Automatische Updates vermeiden bei:

- Datenbanken
- Paperless
- WordPress
- produktiven Services

---

## Empfohlener Ablauf

1. Backup erstellen
2. Release Notes prüfen
3. Images aktualisieren
4. Container neu starten
5. Funktion testen

---

# 35. Troubleshooting

## DNS funktioniert nicht

Prüfen:

```bash
nslookup portainer.homelab.internal
```

Erwartet:

```text
192.168.178.99
```

---

## Reverse Proxy liefert 502

Prüfen:

- Container läuft?
- gleicher Docker-Network?
- richtiger Zielport?
- Containername korrekt?

---

## Docker-Netzwerk prüfen

```bash
docker network inspect homelab_proxy
```

---

## Containerlogs anzeigen

```bash
docker logs container-name
```

---

# 36. Sicherheitsmaßnahmen

## Empfohlen

- starke Passwörter
- 2FA wo möglich
- regelmäßige Updates
- keine unnötigen offenen Ports
- SSH nur intern erreichbar

---

## Nicht empfohlen

- direkte Portfreigaben ins Internet
- ungesicherte Admin-Oberflächen
- Standardpasswörter

---

# 37. Erweiterung neuer Services

Neue Dienste werden standardisiert integriert.

## Ablauf

1. Compose-Datei erstellen
2. `homelab_proxy` einbinden
3. Service starten
4. DNS-Rewrite anlegen
5. Proxy-Host definieren
6. Funktion testen

---

# 38. Langfristige Zielarchitektur

Die Architektur soll langfristig:

- einfach wartbar
- modular erweiterbar
- reproduzierbar
- backupfähig
- dokumentiert
- ausfallsicher

bleiben.

Komplexität wird bewusst minimiert.
