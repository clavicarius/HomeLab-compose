# AdGuard Home

Docker-Compose-Projekt für den Betrieb von **AdGuard Home** im Homelab.

## Voraussetzungen

* Docker Engine
* Docker Compose
* externes macvlan-Netzwerk `homelab_mcvlan` (siehe [docs/network-architecture.md](../docs/network-architecture.md))
* `.env`-Datei im Projektverzeichnis (via `create-env.sh`)

## Projektstruktur

```text
adguard/
├── compose.yml
├── .env                 # erzeugt via scripts/create-env.sh
├── conf/
├── work/
└── README.md
```

## Umgebungsvariablen

Die Konfiguration wird aus `.env.common.example` (Repository-Root) und optional `adguard/.env.example` zusammengeführt:

```bash
cd adguard
../scripts/create-env.sh
```

Zentrale Werte liegen in `.env.common` bzw. `.env.common.example`:

### Benutzer

```env
PUID=1000
PGID=1000
TZ=Europe/Berlin
```

### Netzwerk (macvlan)

```env
SUBNET=192.168.178.224/27
GATEWAY=192.168.178.1
NETWORK_ADAPTER=eth0
```

Das Netzwerk wird einmalig im Repository-Root angelegt:

```bash
./scripts/create-mcvlan.sh
```

### Homelab

```env
HOMELAB_DOMAIN=homelab.internal
HOMELAB_EMAIL=admin@homelab.internal
```

### AdGuard

```env
ADGUARD_HOST=adguard
ADGUARD_IP=192.168.178.252
ADGUARD_PORT=8252
```

### Traefik

```env
TRAEFIK_ENABLED=false
TRAEFIK_TLS_ENABLED=false
```

## Verzeichnisse

| Verzeichnis | Beschreibung                  |
| ----------- | ----------------------------- |
| `./conf`    | Konfiguration                 |
| `./work`    | Datenbank, Filterlisten, Logs |

Die Daten bleiben dadurch auch nach einem Container-Update erhalten.

## Netzwerk

Der Container erhält eine feste LAN-IP über macvlan:

```text
${ADGUARD_IP}   →  192.168.178.252
```

Alle Geräte im Heimnetz nutzen diese IP als DNS-Server. Die FRITZ!Box verteilt sie per DHCP (siehe [network-architecture.md](../docs/network-architecture.md)).

## Ports

| Port | Beschreibung |
| ---- | ------------ |
| 53/tcp, 53/udp | DNS (über LAN-IP `.252` erreichbar) |
| 9080 | Weboberfläche im Container |
| `${ADGUARD_PORT}` | Weboberfläche auf dem Host (Port-Mapping → 9080) |

Die Weboberfläche ist erreichbar unter:

```text
http://192.168.178.252:8252
```

Alternativ über den Host-Port-Mapping:

```text
http://<Docker-Host>:${ADGUARD_PORT}
```

## Container starten

Voraussetzung: `homelab_mcvlan` existiert (`./scripts/create-mcvlan.sh`).

```bash
docker compose pull
docker compose up -d
```

Containerstatus prüfen:

```bash
docker compose ps
```

Logs anzeigen:

```bash
docker compose logs -f
```

Container stoppen:

```bash
docker compose down
```

## Ersteinrichtung

Nach dem ersten Start den Einrichtungsassistenten öffnen:

```text
http://192.168.178.252:8252
```

Empfohlene Einstellungen:

* DNS-Port: 53
* Webinterface: 9080
* Admin-Benutzer anlegen
* Upstream-DNS konfigurieren (z. B. Quad9, Cloudflare oder Unbound)

## DNS-Rewrites

Lokale Domains für Webservices werden in AdGuard als DNS-Rewrites angelegt und zeigen auf die Traefik-IP (`192.168.178.225`). Details: [network-architecture.md](../docs/network-architecture.md#14-dns-rewrites-in-adguard).

## Traefik-Integration

Die `compose.yml` enthält Traefik-Labels. Sobald Traefik läuft und `TRAEFIK_ENABLED=true` gesetzt ist, ist AdGuard zusätzlich erreichbar unter:

```text
https://adguard.homelab.internal
```

Voraussetzungen:

* Traefik-Stack läuft (`poly-php/compose.yml`)
* DNS-Rewrite `adguard.homelab.internal → 192.168.178.225` in AdGuard
* `TRAEFIK_ENABLED=true` in `.env.common`

## Updates

```bash
docker compose pull
docker compose up -d
```

Nicht benötigte Images entfernen:

```bash
docker image prune
```

## Backup

Folgende Verzeichnisse sichern:

```text
conf/
work/
```

Diese enthalten:

* Konfiguration
* Benutzer
* DNS-Einstellungen
* Filterlisten
* Statistiken

## Wiederherstellung

1. Container stoppen.
2. `conf/` und `work/` zurückkopieren.
3. Container erneut starten.

## Healthcheck

Der Container prüft alle 30 Sekunden die Erreichbarkeit des Webinterfaces.

## Hinweise

* Das offizielle AdGuard-Image verwendet `PUID` und `PGID` derzeit nicht aktiv. Die Variablen sind dennoch vorbereitet.
* IP-Adressen, Domains und Netzwerkparameter werden zentral in `.env.common` verwaltet.
* Die vollständige Netzwerkarchitektur ist in [docs/network-architecture.md](../docs/network-architecture.md) dokumentiert.
