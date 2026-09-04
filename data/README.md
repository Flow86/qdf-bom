# data/parts.json

Vollständiger QUADRO-Teilekatalog mit Preisen, Codes und Geometrie-Parametern.

## Quellen

- https://github.com/thecodingdad/quadro-3D/blob/main/data/parts.json
- https://github.com/k3mpaxl/Quadro-Builder/blob/main/data/parts.json

## Aufbau

```
{
  "meta":           { name, source, currency, units, note }
  "geometry":       { connectorSize, tubeRadius, ... }
  "colors":         { "tube": [...], "connector": {...} }
  "connectors":     [ { id, code, name, arms, kind, angle?, qdf?, price, buildable } ]
  "tubes":          [ { id, code, name, length_cm, shape, price, buildable } ]
  "panels":         [ { id, code, name, w, h, holes?, price, buildable } ]
  "accessories":    [ { id, code, name, price, qdf?, buildable?, pool? } ]
  "reinforcements": [ { id, code, name, length_cm, material, price } ]
  "screws":         [ { id, code, name, price, pack } ]
}
```

## Wichtige Felder

| Feld        | Bedeutung                                               |
| ----------- | ------------------------------------------------------- |
| `id`        | Interner Bezeichner (Primärschlüssel)                   |
| `code`      | Händler-Code für die Stückliste (z.B. `"T35"`, `"CS3"`) |
| `qdf`       | QDF-Element-Keyword, das dieses Teil repräsentiert      |
| `holes`     | Anzahl Löcher (Lochplatte, wenn vorhanden)              |
| `buildable` | Ob das Teil im Builder setzbar ist                      |

## Verknüpfung mit QDF-Dateien

Das `qdf`-Feld verbindet Katalogeigenschaften mit QDF-Elementen. Teile ohne
`qdf`-Feld werden über Geometrie aufgelöst (Rohrlänge in mm, Plattenmaße in mm).

Ausführliche Zuordnungslogik: [`docs/BOM-FORMAT.md`](../docs/BOM-FORMAT.md)
