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
auf. `api.insecure` wird nicht aktiviert. Der read-only Docker-Socket wird fuer
optionale Metadaten und Laufzeitinformationen verwendet.

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

## Phase 3: Erweiterte Metadaten

Veroeffentlichte Services koennen folgende optionale Docker-Labels verwenden:

```yaml
- "homelab.name=Gitea"
- "homelab.icon=Git"
- "homelab.category=Development"
- "homelab.description=Self-hosted Git-Service"
```

Der Dashboard-Adapter liest diese Labels ueber den Docker-Socket mit read-only
Berechtigung. Sie beeinflussen weder Traefik-Routing noch Ziel-URL. Fehlende
Labels fallen auf den Hostnamen, ein Initialen-Icon, `Other` und eine leere
Beschreibung zurueck. Werte werden vor der Ausgabe begrenzt.

## API-Schreibweise

Traefiks API-Felder werden ohne Annahme einer bestimmten Gross-/Kleinschreibung
gelesen. Die Felder `name`, `provider`, `rule`, `service` und `tls` werden daher
in lowercase, PascalCase oder CamelCase akzeptiert, beispielsweise `name`,
`Name` oder `routerName`. Dasselbe gilt fuer Containerfelder und die
`homelab.*`-Labelnamen. Die Schreibweise der Werte selbst bleibt unveraendert.

## Phase 4: Statusinformationen

Die Karten zeigen TLS-Aktivierung, Containerstatus, Containername, Image und
Version. Der Containername wird angezeigt, sofern Docker ihn liefert. Der
Backendstatus wird bevorzugt aus Traefiks HTTP-Service-API
abgeleitet. Falls diese Information nicht verfügbar ist, wird der Docker-
Containerstatus verwendet:
`running` wird als `Online`, ein vorhandener gestoppter Container als `Offline`
und fehlende oder nicht erreichbare Metadaten als `Status unbekannt` angezeigt.
Der Dashboard-Adapter fragt dafuer `/containers/json?all=1` ueber den read-only
Docker-Socket ab. Ausfaelle dieser Abfrage lassen die Traefik-Services sichtbar
und fallen nur bei den Laufzeitdaten auf unbekannt zurueck.

Die Docker-API-Antwort wird ueber den Unix-Socket als HTTP gelesen und
unterstuetzt sowohl `Content-Length` als auch `Transfer-Encoding: chunked`.

## Phase 5: Suche

Die Oberflaeche bietet eine clientseitige Suche nach Anzeigename, Kategorie und
Hostname. Die Suche verwendet die bereits geladene API-Antwort und benoetigt
keine zusaetzliche Serverlogik oder Konfiguration.