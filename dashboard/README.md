# Home Dashboard

Das Home Dashboard ist eine datenbanklose Startseite fuer alle Webservices, die
Traefik ueber Docker-Labels veroeffentlicht. Es besitzt keine eigene
Service-Liste. Der Backend-Adapter fragt die Traefik-API regelmaessig ab und
liefert der statischen Oberflaeche normalisierte Services.

## Voraussetzungen

- gemeinsames externes Netzwerk `homelab_macvlan`
- laufender Traefik-Stack
- DNS-Rewrite `dashboard.home.arpa -> TRAEFIK_IP` in AdGuard Home
- `.env.common` und eine lokale `.env` aus `.env.example`

## Start

```bash
../scripts/create-env.sh
docker compose up -d --build
```

Danach ist das Dashboard unter `https://dashboard.home.arpa` erreichbar.

Der Adapter ruft die Traefik-API intern ueber den Hostnamen `traefik.home.arpa`
auf. `api.insecure` wird nicht aktiviert und der Docker-Socket wird in dieser
MVP-Phase nicht an das Dashboard weitergereicht.

## Entwicklung und Tests

```bash
python -m unittest dashboard.test_server
```

Der MVP beruecksichtigt nur Docker-Provider-Router mit einer auswertbaren
`Host(...)`-Regel. Interne Services, File-Provider-Router, Wildcard-Regeln und
doppelte Hosts werden nicht als Karten angezeigt.

## Phase 2: Kategoriegruppen

Die API liefert fuer jeden Service das Feld `category`. Solange keine zusaetzliche
Metadatenquelle verwendet wird, ist der Wert deterministisch `Other`. Die UI
gruppiert nach diesem Feld und sortiert Kategorien sowie Services alphabetisch.

Das optionale Docker-Label `homelab.category` ist als spaeterer Datenvertrag
vorgesehen. Der Dashboard-Container verwendet dafuer in Phase 2 absichtlich
keinen Docker-Socket; eine echte Labelauswertung wird erst nach einer separaten
Sicherheitsentscheidung umgesetzt.