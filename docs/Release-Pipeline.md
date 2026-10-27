# Compose Verification Pipeline

## Ziel

Der Workflow `verify-stack.yml` validiert die Compose-Konfigurationen und startet
jeden erkannten Stack auf einem eigenen GitHub-Actions-Runner. Er läuft bei
Pull Requests nach `main` und bei Pushes auf `main`.

## Anforderungen

- Stack-Verzeichnisse mit `compose.yml` oder `docker-compose.yml` werden
	automatisch erkannt.
- Jeder erkannte Stack erhält einen eigenen Matrix-Job; `fail-fast` ist
	deaktiviert, damit andere Jobs nach einem Fehler weiterlaufen.
- CI erzeugt eine Test-Umgebung aus `.env.common.example` und dem jeweiligen
	`.env.example` und ersetzt Netzwerk- und Pfadwerte durch CI-Werte.

## Umsetzung

### 1. Stacks automatisch erkennen

Die Suche reicht zwei bis drei Verzeichnisebenen tief und berücksichtigt
Verzeichnisse, die eine der unterstützten Compose-Hauptdateien enthalten.

### 2. Matrix-Strategie verwenden

Aus den gefundenen Stacks wird eine Build-Matrix erzeugt. Für jeden Stack startet GitHub Actions einen separaten Job.

### 3. Validierung je Stack

Jeder Job führt folgende Schritte aus:

1. Repository auschecken.
2. In das Stack-Verzeichnis wechseln.
3. `docker compose config` ausführen.
4. Prüfen, dass jeder Container-Service einen aktivierten Healthcheck besitzt.
5. Den Stack mit `docker compose up -d --wait` starten.
6. Prüfen, dass alle Container den Status `running` haben.
7. Beim Dashboard-Stack zusätzlich die Unit-Tests ausführen.

### 4. Health Checks

Compose-Healthchecks sind verpflichtend und werden vor dem Start auf
Vorhandensein und Aktivierung geprüft. `up --wait` wartet auf den Zustand
dieser Checks.

## Ablauf

Der Workflow besteht aus diesen Stufen:

```text
Discover stacks
 └── Compose-Dateien finden

↓

Verify (parallel)
 ├── Compose-Konfiguration und Healthchecks prüfen
 ├── Stack starten und Status prüfen
 └── Dashboard-Unit-Tests ausführen

↓

Verify Compose Stacks
 └── Gesamtstatus auswerten
```

Dieser Workflow erstellt kein GitHub Release und fährt die Stacks nicht
explizit herunter. Die separate Tag-Erstellung ist in
[VERSIONING.md](VERSIONING.md) beschrieben.

## Vorteile

- Unabhängige Validierung jedes Compose-Stacks.
- Fehler lassen sich eindeutig einem Service zuordnen.
- Neue Compose-Stacks werden automatisch in die Matrix aufgenommen.
- Fehler einzelner Stacks verhindern nicht den Start der übrigen Matrix-Jobs.
