# create-env.sh

Das Helper-Skript `create-env.sh` erstellt eine lokale `.env`-Datei aus den vorhandenen Beispiel-Dateien. Dabei werden die Inhalte der gemeinsamen Konfiguration (`.env.common.example`) und der projektspezifischen Konfiguration (`.env.example`) zu einer einzigen `.env` zusammengeführt.

## Voraussetzungen

Das Skript sucht nach folgenden Dateien:

| Datei | Beschreibung |
| ------ | ------------ |
| `../.env.common.example` | Gemeinsame Konfiguration für mehrere Projekte (optional). |
| `.env.example` | Projektspezifische Konfiguration (optional). |

Mindestens eine der beiden Dateien muss vorhanden sein.

## Funktionsweise

1. Prüft, ob bereits eine `.env` existiert.
2. Fragt den Benutzer, ob die vorhandene Datei überschrieben werden soll.
3. Erstellt eine neue `.env`.
4. Fügt den Inhalt von `../.env.common.example` hinzu (falls vorhanden).
5. Fügt anschließend den Inhalt von `.env.example` hinzu (falls vorhanden).
6. Gibt die erzeugte `.env` auf der Konsole aus.

Zwischen den beiden Dateien wird jeweils eine Leerzeile eingefügt.

## Verwendung

### Interaktiv

```bash
./create-env.sh
```

Existiert bereits eine `.env`, erscheint folgende Abfrage:

```text
.env existiert bereits und wird überschrieben. Fortfahren? [y/N]
```

- `y` oder `yes` → Datei wird überschrieben.
- Jede andere Eingabe → Skript wird beendet.

### Ohne Rückfrage

Für automatisierte Umgebungen (z. B. CI/CD) kann die Rückfrage mit dem Parameter `--force` oder `-f` übersprungen werden.

```bash
./create-env.sh --force
```

oder

```bash
./create-env.sh -f
```

## Priorität der Konfiguration

Die Reihenfolge der zusammengeführten Dateien ist:

1. `../.env.common.example`
2. `.env.example`

Dadurch können projektspezifische Werte gemeinsame Standardwerte überschreiben, sofern dieselbe Variable mehrfach definiert ist. In den meisten Anwendungen wird dabei der zuletzt definierte Wert verwendet.

## Beispiel

### Verzeichnisstruktur

```text
project-root/
├── .env.common.example
└── app/
    ├── create-env.sh
    └── .env.example
```

### Ergebnis

Aus

```text
../.env.common.example
```

und

```text
.env.example
```

wird erzeugt:

```text
.env
```

mit folgendem Inhalt:

```env
# Inhalt aus .env.common.example

...

# Inhalt aus .env.example

...
```

## Fehlerbehandlung

Falls keine der beiden Quelldateien gefunden wird, beendet sich das Skript mit der Meldung:

```text
No environment file found.
```

und liefert den Exit-Code `1`.

## Exit-Codes

| Exit-Code | Bedeutung |
|-----------|-----------|
| `0` | Erfolgreich abgeschlossen oder Benutzer hat das Überschreiben abgebrochen. |
| `1` | Es wurde keine Eingabedatei gefunden. |
