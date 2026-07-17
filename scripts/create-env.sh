#!/bin/bash
# create-env.sh
# Creates a local .env file by merging .env.common.example (repository root)
# and the service-specific .env.example (current directory).
#
# Usage:
#   ../scripts/create-env.sh           — interactive (asks before overwriting)
#   ../scripts/create-env.sh --force   — overwrite without confirmation (CI/CD)
#   ../scripts/create-env.sh -f        — same as --force
#
# Input files (at least one must exist):
#   ../.env.common.example   — shared configuration for all services
#   .env.example             — service-specific configuration
#
# Output:
#   .env  — merged configuration file in the current directory
#
# Exit codes:
#   0 — success, or user aborted the overwrite prompt
#   1 — no input file found
#
# See also:
#   docs/create-env.md  — detailed usage documentation
#   docs/scripts.md     — overview of all helper scripts

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
