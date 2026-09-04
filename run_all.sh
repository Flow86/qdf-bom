#!/usr/bin/env bash
# Erzeugt Stücklisten für alle .qdf-Dateien im qdf/-Verzeichnis.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QDF_DIR="$SCRIPT_DIR/qdf"

if [[ ! -d "$QDF_DIR" ]]; then
    echo "Verzeichnis nicht gefunden: $QDF_DIR" >&2
    exit 1
fi

shopt -s nullglob
files=("$QDF_DIR"/*.qdf)

if [[ ${#files[@]} -eq 0 ]]; then
    echo "Keine .qdf-Dateien in $QDF_DIR gefunden." >&2
    exit 1
fi

echo "Verarbeite ${#files[@]} QDF-Datei(en) ..."
python -m qdf_bom "${files[@]}"
