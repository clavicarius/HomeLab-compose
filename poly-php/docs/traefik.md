# HTTPS für den Multi‑PHP Docker Stack

Diese Anleitung beschreibt kurz, wie HTTPS für die lokale Entwicklungsumgebung mit **Traefik als Reverse‑Proxy** aktiviert wird.

Traefik übernimmt dabei die TLS‑Terminierung und leitet die Requests an die jeweiligen PHP‑Container weiter.

---

# 1. Reverse Proxy hinzufügen

Im `docker-compose.yml` wird ein **Traefik‑Service** ergänzt.

Dieser stellt die Ports **80 (HTTP)** und **443 (HTTPS)** bereit und erkennt automatisch Docker‑Container über Labels.

Beispiel:

```
traefik:
  image: traefik:v3.0
  command:
    - "--api.insecure=true"
    - "--providers.docker=true"
    - "--entrypoints.web.address=:80"
    - "--entrypoints.websecure.address=:443"
  ports:
    - "80:80"
    - "443:443"
    - "8088:8080"
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
```

---

# 2. Routing für PHP‑Container definieren

Jeder PHP‑Container erhält **Traefik‑Labels**, die definieren:

- unter welchem Hostnamen der Service erreichbar ist
- dass HTTPS verwendet wird
- auf welchen internen Port Traefik weiterleitet

Beispiel für PHP 8.5:

```
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.php85.rule=Host(`php85.localhost`)"
  - "traefik.http.routers.php85.entrypoints=websecure"
  - "traefik.http.routers.php85.tls=true"
  - "traefik.http.services.php85.loadbalancer.server.port=80"
```

Analog können Labels für:

- `php56`
- `php74`
- `php85`
- `phpmyadmin`

gesetzt werden.

---

# 3. Lokale Hostnamen konfigurieren

Damit die lokalen Domains funktionieren, müssen sie in der **Hosts‑Datei** eingetragen werden.

Linux / macOS

```
/etc/hosts
```

Windows

```
C:\Windows\System32\drivers\etc\hosts
```

Einträge hinzufügen:

```
127.0.0.1 php56.localhost
127.0.0.1 php74.localhost
127.0.0.1 php85.localhost
127.0.0.1 pma.localhost
```

---

# 4. Container starten

Den Stack bauen und starten:

```
docker compose up -d --build
```

---

# 5. Zugriff auf die Services

Danach sind die Anwendungen über HTTPS erreichbar:

PHP 5.6  
https://php56.localhost

PHP 7.4  
https://php74.localhost

PHP 8.5  
https://php85.localhost

phpMyAdmin  
https://pma.localhost

---

# 6. Traefik Dashboard

Das Traefik Dashboard ist erreichbar unter:

```
http://localhost:8088
```

Dort können Router, Services und Container‑Status eingesehen werden.

---

# Hinweis zu Zertifikaten

Für lokale Domains erzeugt Traefik standardmäßig **Self‑Signed Zertifikate**.  
Browser zeigen daher eine Sicherheitswarnung an.

Für eine komfortablere lokale Entwicklung können später **vertrauenswürdige Zertifikate mit mkcert** integriert werden.
