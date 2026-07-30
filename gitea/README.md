# Gitea

Docker-Compose-Projekt für den Betrieb von **Gitea** im Homelab.

## Voraussetzungen

* Docker Engine
* Docker Compose
* Netzwerk mit statischer IP-Konfiguration
* `.env`-Datei im Projektverzeichnis

## Projektstruktur

```text
gitea/
├── compose.yml
├── .env
├── data/
└── README.md
```

## Umgebungsvariablen

Alle projektspezifischen Einstellungen befinden sich in der `.env`.

### Benutzer

```env
PUID=1000
PGID=1000
TZ=Europe/Berlin
```

### Netzwerk

```env
SUBNET=192.168.178.224/27
GATEWAY=192.168.178.1
```

### Homelab

```env
HOMELAB_DOMAIN=homelab.internal
HOMELAB_EMAIL=admin@homelab.internal
```

### Gitea

```env
GITEA_HOST=gitea
GITEA_IP=192.168.178.248
GITEA_PORT=3000
GITEA_SSH_PORT=222
```

## Verzeichnisse

| Verzeichnis | Beschreibung                  |
| ----------- | ----------------------------- |
| `./data`    | Repositorys, Konfiguration, Datenbank |

Die Daten bleiben dadurch auch nach einem Container-Update erhalten.

## Ports

| Port               | Beschreibung                          |
| ------------------ | ------------------------------------- |
| 3000               | Weboberfläche im Container            |
| 22                 | SSH im Container                      |
| `${GITEA_PORT}`    | veröffentlichter Webport auf dem Host |
| `${GITEA_SSH_PORT}`| veröffentlichter SSH-Port auf dem Host|

Die Weboberfläche ist anschließend erreichbar unter

```
http://<Docker-Host>:${GITEA_PORT}
```

beispielsweise

```
http://192.168.178.248:3000
```

## Netzwerk

Der Container erhält eine feste IP-Adresse aus der `.env`.

```text
${GITEA_IP}
```

Das Docker-Netzwerk wird mit folgenden Parametern erstellt:

```text
Subnet : ${SUBNET}
Gateway: ${GATEWAY}
```

## Container starten

```bash
docker compose pull
docker compose up -d
```

Containerstatus prüfen

```bash
docker compose ps
```

Logs anzeigen

```bash
docker compose logs -f
```

Container stoppen

```bash
docker compose down
```

## Ersteinrichtung

Nach dem ersten Start den Einrichtungsassistenten öffnen:

```
http://<Docker-Host>:${GITEA_PORT}
```

Empfohlene Einstellungen:

* Datenbanktyp: SQLite3 (Standard, für kleine Installationen ausreichend)
* Admin-Benutzer anlegen
* SSH-Port konfigurieren

## Updates

Container aktualisieren:

```bash
docker compose pull
docker compose up -d
```

Nicht benötigte Images entfernen:

```bash
docker image prune
```

## Backup

Folgendes Verzeichnis sichern:

```text
data/
```

Dieses enthält:

* Repositorys
* Konfiguration
* Datenbank
* Benutzer

## Wiederherstellung

1. Container stoppen.
2. `data/` zurückkopieren.
3. Container erneut starten.

## Healthcheck

Der Container prüft alle 30 Sekunden die Erreichbarkeit des Webinterfaces.

## Geplante Traefik-Integration

Die `.env` enthält bereits alle benötigten Variablen.

```env
HOMELAB_DOMAIN=homelab.internal
GITEA_HOST=gitea
```

Später kann Gitea beispielsweise unter

```
https://gitea.homelab.internal
```

über Traefik veröffentlicht werden.

## Hinweise

* Gitea wird standardmäßig mit SQLite3 als Datenbank betrieben. Für größere Installationen empfiehlt sich ein externer Datenbankserver (z. B. PostgreSQL oder MySQL).
* Alle projektspezifischen Einstellungen (Ports, IP-Adressen, Domains und Benutzerinformationen) werden zentral über die `.env` verwaltet.
