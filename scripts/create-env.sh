#!/bin/bash

# Prüfen, ob das Skript mit --force oder -f aufgerufen wurde
FORCE=false

if [ "$1" = "--force" ] || [ "$1" = "-f" ]; then
  FORCE=true
fi

# Warnung ausgeben, wenn .env bereits existiert
if [ -f ".env" ] && [ "$FORCE" = false ]; then
  read -p ".env existiert bereits und wird überschrieben. Fortfahren? [y/N] " confirm
  case "$confirm" in
    [yY]|[yY][eE][sS])
      ;;
    *)
      echo "Abgebrochen."
      exit 0
      ;;
  esac
fi

# Alte .env entfernen
rm -f .env

FOUND=0

# Gemeinsame Konfiguration übernehmen
if [ -f "../.env.common.example" ]; then
  cat ../.env.common.example >> .env
  echo "" >> .env
  FOUND=1
fi

# Projektspezifische Konfiguration übernehmen
if [ -f ".env.example" ]; then
  cat .env.example >> .env
  echo "" >> .env
  FOUND=1
fi

# Prüfen, ob mindestens eine Quelldatei gefunden wurde
if [ "$FOUND" -eq 0 ]; then
  echo "No environment file found."
  exit 1
fi

echo "Using environment:"
cat .env
