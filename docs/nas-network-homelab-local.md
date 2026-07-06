# Docker-Netzwerk `homelab.local` erstellen

Für die Kommunikation zwischen Reverse Proxy und Docker-Services wird ein gemeinsames externes Docker-Netzwerk verwendet.

Dieses Netzwerk ermöglicht:

- containerübergreifende Kommunikation
- zentrale Reverse-Proxy-Anbindung
- DNS-Auflösung zwischen Containern
- Nutzung getrennter Compose-Dateien

---

# Netzwerk erstellen

Per SSH auf der Synology anmelden:

```bash
ssh user@192.168.178.99
```

Docker-Netzwerk erzeugen:

```bash
docker network create homelab.local
```

---

# Netzwerk prüfen

Vorhandene Netzwerke anzeigen:

```bash
docker network ls
```

Erwartete Ausgabe:

```text
NETWORK ID     NAME             DRIVER    SCOPE
xxxxxxxxxxxx   homelab.local    bridge    local
```

---

# Netzwerkdetails anzeigen

```bash
docker network inspect homelab.local
```

---

# Verwendung in Compose-Dateien

Das Netzwerk wird als externes Netzwerk eingebunden.

## Beispiel

```yaml
networks:
  homelab.local:
    external: true
```

---

# Beispiel-Service

```yaml
services:
  portainer:
    image: portainer/portainer-ce

    networks:
      - homelab.local

networks:
  homelab.local:
    external: true
```

---

# Vorteil dieser Struktur

Alle Services können dadurch intern über ihren Containernamen kommunizieren.

Beispiele:

```text
http://portainer:9000
http://paperless:8000
http://wordpress:80
```

Dadurch sind:
- keine festen Container-IPs nötig
- keine zusätzlichen Subnetze erforderlich
- keine komplexen Netzwerkkonfigurationen notwendig
