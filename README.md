# qdf-bom – QUADRO Stücklisten-Generator

Liest `.qdf`-Dateien (proprietäres Format der QUADRO 3D-Software) und erzeugt
eine strukturierte Stückliste (Bill of Materials) aller verwendeten QUADRO-Bauteile.

---

## Installation

```bash
# Im Projekt-Verzeichnis
pip install -e .

# Nur für die Tests
pip install pytest
```

> Python ≥ 3.10 erforderlich. Keine weiteren Abhängigkeiten.

---

## Verwendung

### Kommandozeile

```bash
python -m qdf_bom qdf/C0048.qdf
# oder nach Installation:
qdf-bom qdf/C0048.qdf
```

Ausgabe auf `stdout` plus Speicherung als `<stem>_partslist.txt` im selben
Verzeichnis wie die QDF-Datei. Mehrere Dateien können auf einmal angegeben werden.

### Als Bibliothek

```python
from pathlib import Path
from qdf_bom.catalog import PartsCatalog
from qdf_bom.tool import BomTool

catalog = PartsCatalog.from_default()          # lädt data/parts.json
tool = BomTool(catalog)

report = tool.run_file(Path("qdf/C0048.qdf"))  # gibt Stückliste als String zurück
print(report)

# Oder mit mehr Kontrolle:
text = Path("qdf/C0048.qdf").read_text(encoding="utf-8")
counter, mat_colors = tool.process(text)       # BomCounter + Farbzuordnung
print(counter.grand_total())                   # Gesamtzahl Teile
```

---

## Ausgabeformat

```
QUADRO-Stückliste: C0048.qdf
================================================================

Link: https://quadroworld.com/de/designs/C0048

ROHRE
----------------------------------------------------------------
T15    Rohr 15 cm                               Rot        x   4
T35    Rohr 35 cm                               Rot        x  20
...

KUPPLUNGEN / VERBINDER
----------------------------------------------------------------
CS3    Raumkupplung 3-armig                     Schwarz    x  19
CDT    Doppelrohrverbinder                      Rot        x   2
...

ERKANNTE BAUTEIL-OBJEKTE GESAMT: 194
```

Kategorien in fester Reihenfolge (werden nur ausgegeben, wenn Teile vorhanden):
`ROHRE`, `PLATTEN`, `KUPPLUNGEN / VERBINDER`, `ZUBEHÖR`, `VERSTEIFUNGEN`,
`TEXTILIEN`, `RUTSCHEN`, `POOLS / FOLIEN`, `SCHRAUBEN`, `SONSTIGE`

---

## Teilekatalog

`data/parts.json` enthält alle bekannten QUADRO-Teile mit Preisen, Codes und
Geometrie-Parametern. Ohne diese Datei funktioniert das Tool nicht.

Quellen: [quadro-3D](https://github.com/thecodingdad/quadro-3D/blob/main/data/parts.json),
[Quadro-Builder](https://github.com/k3mpaxl/Quadro-Builder/blob/main/data/parts.json).

---

## Tests

```bash
pytest tests/ -v
```

---

## Architektur

| Modul                   | Zweck                                                    |
| ----------------------- | -------------------------------------------------------- |
| `qdf_bom/catalog.py`    | `PartsCatalog` – lädt und indiziert `parts.json`         |
| `qdf_bom/parser.py`     | `QdfParser` – parst QDF-Text, filtert tote Zeilen (§3.5) |
| `qdf_bom/classifier.py` | `ConnectorClassifier` – Arm-Bitmaske → Katalog-ID        |
| `qdf_bom/bom.py`        | `BomCounter` / `BomReport` – Zählung und Ausgabe         |
| `qdf_bom/tool.py`       | `BomTool` – Orchestrierung, CLI-Einstiegspunkt           |

---

## Bekannte Limitierungen

- **Schrägwinkelrohre TS1–TS7** sind im QDF-Format nicht von geraden Rohren
  unterscheidbar (kein Winkel-/Lochfeld). Sie werden als T15 bzw. T35 der
  gleichen Länge gezählt. Da `buildable: false` und in der Herstellersoftware
  nie gesetzt, tritt der Fall in der Praxis nicht auf.
- **Alu-Profile** (`alu2`) sind nicht mehr erhältlich und werden in `SONSTIGE`
  gelistet.
- **Pool-Elemente** (`pool2`, `pool-small2`) werden in `SONSTIGE` gelistet,
  da die Zuordnung zu Poolfolie-Produkten von den Maßen abhängt.

Ausführliche Format-Dokumentation: [`docs/BOM-FORMAT.md`](docs/BOM-FORMAT.md)
