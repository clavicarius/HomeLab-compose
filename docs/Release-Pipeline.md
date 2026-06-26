# Release Pipeline

## Ziel

Für jeden Docker Compose Stack soll automatisiert überprüft werden, ob dieser erfolgreich gestartet werden kann. Jeder Stack wird dabei unabhängig von den anderen validiert, sodass Fehler eindeutig einem einzelnen Service zugeordnet werden können.

## Anforderungen

- GitHub Actions als CI/CD-Plattform verwenden.
- Jeder Compose-Stack erhält einen eigenen Workflow-Job.
- Die Jobs werden parallel ausgeführt.
- Ein Fehler in einem Stack darf die Ausführung der übrigen Stacks nicht verhindern.
- Nach Abschluss der Pipeline muss eindeutig ersichtlich sein, welcher Stack erfolgreich validiert wurde und welcher fehlgeschlagen ist.

## Umsetzung

### 1. Stacks automatisch erkennen

Die Pipeline soll alle Verzeichnisse im Repository (mit Ausnahme von `.github` und weiteren Infrastrukturverzeichnissen) als eigenständige Compose-Stacks erkennen.

### 2. Matrix-Strategie verwenden

Aus den gefundenen Stacks wird eine Build-Matrix erzeugt. Für jeden Stack startet GitHub Actions einen separaten Job.

### 3. Validierung je Stack

Jeder Job führt folgende Schritte aus:

1. Repository auschecken.
2. In das Stack-Verzeichnis wechseln.
3. Docker Compose Stack starten.
4. Auf den erfolgreichen Start der Container warten.
5. Den Zustand der Container prüfen.
6. Optional einen stack-spezifischen Health Check ausführen.
7. Bei Fehlern die Container-Logs ausgeben.
8. Den Stack vollständig wieder herunterfahren und aufräumen.

### 4. Health Checks

Jeder Stack kann optional ein Skript `healthcheck.sh` bereitstellen.

Ist dieses vorhanden, wird es automatisch ausgeführt. Dadurch können servicespezifische Prüfungen implementiert werden, beispielsweise:

- HTTP-Endpunkte prüfen
- Datenbankverbindungen testen
- Login-Seiten erreichen
- API-Health-Endpunkte aufrufen

Fehlt das Skript, erfolgt lediglich die Überprüfung, ob alle Container erfolgreich gestartet wurden.

## Release-Prozess

Der Workflow besteht aus drei Phasen:

```text
Lint
 ├── compose config
 ├── YAML-Validierung
 └── Shell-Skripte prüfen

↓

Verify
 ├── Stack A
 ├── Stack B
 ├── Stack C
 └── ...

↓

Release
 └── GitHub Release (nur wenn alle Verify-Jobs erfolgreich waren)
```

## Vorteile

- Unabhängige Validierung jedes Compose-Stacks.
- Fehler lassen sich eindeutig einem Service zuordnen.
- Gute Skalierbarkeit bei wachsender Anzahl an Services.
- Einfache Erweiterung um individuelle Health Checks.
- Saubere Trennung zwischen Konfigurationsprüfung, Deployment-Test und Release.
