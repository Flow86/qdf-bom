# BOM-FORMAT – Stücklisten-Erzeugung aus QDF-Dateien

Dieses Dokument beschreibt, wie `qdf-bom` die einzelnen QDF-Elemente dem
QUADRO-Teilekatalog (`data/parts.json`) zuordnet und eine Stückliste erstellt.
Es ergänzt [`3rdparty/quadro-3D/docs/QDF-FORMAT.md`](../3rdparty/quadro-3D/docs/QDF-FORMAT.md),
das das binäre QDF-Format an sich beschreibt.

**Konfidenz-Legende** (wie in QDF-FORMAT.md):
- ✔ direkt verifiziert (Quellcode-Analyse + echte Dateien)
- ~ wahrscheinlich korrekt (Konsistenz mit Korpus)
- ? unsicher / Vermutung

---

## 1 Quellen

| Quelle                                        | Verwendung                                  |
| --------------------------------------------- | ------------------------------------------- |
| `3rdparty/quadro-3D/docs/QDF-FORMAT.md`       | Feldstruktur aller QDF-Elemente             |
| `3rdparty/quadro-3D/web/js/qdfimport.js`      | Lochplatten-Erkennung, Arm-Geometrie        |
| `3rdparty/Quadro-Builder/web/js/qdfimport.js` | Platten-Größen-Lookup, Schiebe-Elemente     |
| `qdf/C0048.qdf` + `C0091.qdf` + `C0145.qdf`   | Hersteller-Referenzdateien (Header `0, 0;`) |
| `qdf/C0145-mod.qdf`                           | Lochplatten-Encoding (eigene Messung)       |

---

## 2 Teilekatalog (`data/parts.json`)

### 2.1 Aufbau

```
{
  "meta":           {...},
  "geometry":       { "connectorSize": 5.0, ... },
  "colors":         { "tube": [...], "connector": {...} },
  "connectors":     [...],
  "tubes":          [...],
  "panels":         [...],
  "accessories":    [...],
  "reinforcements": [...],
  "screws":         [...]
}
```

### 2.2 Felder je Teil

| Feld        | Typ          | Bedeutung                                       |
| ----------- | ------------ | ----------------------------------------------- |
| `id`        | string       | Interner Bezeichner (Primärschlüssel)           |
| `code`      | string       | Händler-Code (z.B. `"T35"`, `"CS3"`)            |
| `name`      | string       | Deutsche Bezeichnung für die Stückliste         |
| `price`     | number       | Preis in EUR                                    |
| `qdf`       | string\|null | QDF-Element-Keyword, das diesem Teil entspricht |
| `buildable` | bool         | Ob das Teil im Editor setzbar ist               |

Kategorie-spezifische Felder:
- **Rohre**: `length_cm`, `shape` (`"straight"` / `"curved"` / `"angled"`)
- **Platten**: `w`, `h` (in cm), `holes` (Anzahl; wenn vorhanden → Lochplatte)
- **Kupplungen**: `arms`, `kind` (`"space"` / `"planar"` / `"special"`), `angle`

### 2.3 Farbzuordnung

Die `colors`-Sektion enthält zwei Gruppen:

```json
"tube":      [{"id": "blue", "name": "Blau", ...}, ...]
"connector": {"id": "black", "name": "Schwarz", ...}
```

Die BOM ordnet QDF-Materialnamen (z.B. `"red"`, `"black"`) über diese Tabelle
deutschen Anzeigetexten zu. Unbekannte Namen werden unverändert übernommen.

### 2.4 `qdf`-Verknüpfung

Teile mit `qdf`-Feld werden direkt über den QDF-Element-Keyword gefunden
(`part_by_qdf(name)`). Teile ohne `qdf`-Feld (Rohre, Platten) werden über
Geometrie-Parameter (Länge in mm, Maße in mm) aufgelöst.

Ausnahmen: `round-tube2` → `TC1` und `clamp2` → `double_tube` und
`clip2` → `tube_clamp` sind im Tool als `_SPECIAL_ELEMENT_MAP` fest verdrahtet,
weil parts.json dafür kein `qdf`-Feld enthält.

---

## 3 QDF-Elemente und ihre BOM-Zuordnung

### 3.1 `material3` – Materialdefinition

```
material3{<id>, "<name>", <set>, <RGB...>, <lighting...>, "", <unknown>}
```

Wird in der BOM selbst nicht gezählt. Dient ausschließlich dazu, `mat_id`
auf Farbnamen zu mappen und Lochplatten-Materialien zu identifizieren
(→ §4 Lochplatten-Erkennung). ✔

### 3.2 `tube2` – Standardrohr

```
tube2{<mat_id>, {<quat_x_y_z>}, <flag>, <length_mm>., <addition>., <birth_step>}
```

BOM-Zuordnung: `length_mm` → `tube_by_mm(length_mm)` → Katalog-ID.

| Länge (mm) | Katalog-ID | Code |
| ---------- | ---------- | ---- |
| 100        | T10        | T10  |
| 150        | T15        | T15  |
| 200        | T20        | T20  |
| 250        | T25        | T25  |
| 350        | T35        | T35  |
| 520        | T52        | T52  |
| 750        | T75        | T75  |

Konfidenz: ✔ (verifiziert an C0048, C0091, C0145)

**Hinweis Schrägwinkelrohre (TS1–TS7):** Das QDF-Format enthält kein
Winkel- oder Lochfeld für Rohre. TS1–TS7 erscheinen als gewöhnliche `tube2`-
Einträge und sind von T15/T35 gleicher Länge nicht unterscheidbar. Sie werden
daher als T15/T35 gezählt. Da `buildable: false` und die Herstellersoftware
sie nie setzt, ist der Fall in der Praxis nicht relevant. ~

### 3.3 `round-tube2` – Bogenrohr (TC1)

```
round-tube2{<mat_id>, {<quat_x_y_z>}, <flag>, <length_mm>., <addition>., <birth_step>}
```

Eigenes Element-Keyword → direkte Zuordnung zu `TC1` (Bogenrohr) via
`_SPECIAL_ELEMENT_MAP`. Das `length_mm`-Feld enthält 350 (Halbkreis-Radius),
wird für die BOM-Zählung aber nicht benötigt. ✔

### 3.4 `alu2` / `alu-connector2` – Alu-Profile (veraltet)

Eigenes Element-Keyword, kein Katalogeintrag. Erscheint als `SONSTIGE` in
der BOM. Die Alu-Profile der Herstellersoftware sind nicht mehr erhältlich. ~

### 3.5 `connector3` – Standardkupplung

```
connector3{<mat_id>, {<quat_x_y_z>}, <flag>, <field3>, <arm_mask>, <complement>, <face_mask>, <birth_step>}
```

BOM-Zuordnung über `arm_mask` (Feld 4, 0-indiziert nach mat_id):

| Bits (0-11)          | arms | Z-Anteil? | Katalog-ID        | Code | Name                           |
| -------------------- | ---- | --------- | ----------------- | ---- | ------------------------------ |
| 0b111111 (6 Kard.)   | 6    | ja        | 6way              | CS6  | Raumkupplung 6-armig           |
| 5 Kard. gesetzt      | 5    | ja        | 5way              | CS5  | Raumkupplung 5-armig           |
| 4 Kard., ≥1 Z        | 4    | ja        | 4way              | CS4  | Raumkupplung 4-armig           |
| 4 Kard., kein Z      | 4    | nein      | cross             | CF4  | Flächenkupplung 4-armig        |
| 3 Kard., ≥1 Z        | 3    | ja        | 3way              | CS3  | Raumkupplung 3-armig           |
| 3 Kard., kein Z      | 3    | nein      | t                 | CF3  | Flächenkupplung 3-armig        |
| 2 Bits, gegenüber    | 2    | –         | straight          | CF2  | Flächenkupplung 2-armig (180°) |
| 2 Bits, rechtwinklig | 2    | –         | elbow             | CS2  | Flächenkupplung 2-armig (90°)  |
| 0                    | 0    | –         | connector_unknown | –    | Kupplung (unbekannt)           |

Socket-Richtungen (Sockets 0–11):
```
0:(+1,0,0)  1:(-1,0,0)  2:(0,+1,0)  3:(0,-1,0)  4:(0,0,+1)  5:(0,0,-1)
6:(+1,+1,0) 7:(+1,-1,0) 8:(-1,+1,0) 9:(-1,-1,0) 10:(+1,0,+1) 11:(-1,0,+1)
```

Konfidenz: ✔ (klassifiziert alle Kupplungen in C0048/C0091/C0145 korrekt)

Arm-Maske 0 (80× im Korpus): gelöschte/inaktive Kupplungen, werden als
`connector_unknown` gezählt, aber nicht in C0048 beobachtet.

### 3.6 `connector45_2` – 45°-Winkelkupplung (C45)

```
connector45_2{<mat_id>, {<quat_x_y_z>}, <flag>, <field3>, <birth_step>}
```

Feste Zuordnung: jede `connector45_2`-Zeile → `diagonal` (C45,
Winkelkupplung 45 Grad). Der C45 wird als Aufsteck-Adapter
**zusätzlich** zur Basiskupplung gezählt (der Basiskupplung-Stutzen
ist in der `connector3`-Zeile an gleicher Position erfasst). ✔

### 3.7 `panel2` – Platte

```
panel2{<mat_id>, {<quat_x_y_z>}, <flag>, <w_mm>., <w_add>., <h_mm>., <h_add>., <birth_step>}
```

- **Maße**: `w_mm` und `h_mm` sind PART-Größen (§3.4 QDF-FORMAT.md).
  Für den Katalog-Lookup wird `connectorSize` (50 mm) addiert:
  `lookup_mm = part_mm + 50`. ✔
- **Lochplatten-Erkennung**: über Materialname (§4 dieses Dokuments). ✔
- **Fallback**: existiert kein Lochplatten-Eintrag für die Maße, wird die
  gleichgroße Vollplatte verwendet. ~

| Part-Maße (mm) | Grid-Maße (mm) | Katalog-ID       | Code |
| -------------- | -------------- | ---------------- | ---- |
| 350×350        | 400×400        | panel_40x40      | PA4  |
| 150×350        | 200×400        | panel_40x20      | PA2  |
| 250×250        | 300×300        | panel_30x30      | PA3  |
| 350×350 (Loch) | 400×400        | hole_panel_40x40 | PO4  |

### 3.8 `textil2` / `lattice2` / `display2` – Flächen-Sonderteile

Gleiche Feldstruktur wie `panel2`, aber eigenes Element-Keyword.
Zuordnung über `qdf`-Feld im Katalog: `textil2` → `textile` (Textil),
`lattice2` → `lattice` (Netz). `display2` ist nicht in parts.json → `SONSTIGE`. ~

### 3.9 `clamp2` – Doppelrohrverbinder (CDT)

```
clamp2{<mat_id>, {<quat_x_y_z>}, <flag>, <birth_step>}
```

Feste Zuordnung: `double_tube` (CDT, Doppelrohrverbinder). Kein `qdf`-Feld
in parts.json (→ `_SPECIAL_ELEMENT_MAP`). Erscheint unter
`KUPPLUNGEN / VERBINDER`. ✔

### 3.10 `clip2` – Rohrklammer (CCL)

Feste Zuordnung: `tube_clamp` (CCL, Rohrklammer). Kein `qdf`-Feld
in parts.json (→ `_SPECIAL_ELEMENT_MAP`). Erscheint unter
`KUPPLUNGEN / VERBINDER`. ~

### 3.11 `flexi-connector3` / `bolt2` – Flexigelenk

```
flexi-connector3{<mat_id>, {<quat_x_y_z>}, <flag>, <...>, <birth_step>}
bolt2{<mat_id>, {<quat_x_y_z>}, <flag>, <len_mm>., <addition>., <birth_step>}
```

- `flexi-connector3` → `flexi_hinge` (CXB, Flexikupplung Scharnier) ✔
- `bolt2` → `flexi_bolt` (CXA, Flexikupplung Bolzen) ✔

Je Flexigelenk stehen zwei `flexi-connector3` und ein `bolt2` in der Datei.
Das Gelenk selbst (`flexi`, CX4) wird nicht direkt gezählt. ✔

### 3.12 `hole-connector4` – Lochzapfenkupplung (CH3)

Zuordnung über `qdf`-Feld: → `hole_t` (CH3, 3-armig). Das Arm-Mask-Feld
wird für die BOM nicht ausgewertet; alle Varianten landen bei CH3. ?

### 3.13 `bearing-connector4` – Lagerkupplung (CBR)

Zuordnung über `qdf`-Feld: → `bearing` (CBR, Lagerkupplung). ~

### 3.14 Zubehör-Elemente (via `qdf`-Feld)

| QDF-Element       | Katalog-ID     | Kategorie |
| ----------------- | -------------- | --------- |
| `bearing2`        | wheel_bearing  | ZUBEHÖR   |
| `multi-wheel2`    | wheel          | ZUBEHÖR   |
| `floating-wheel2` | wheel_floating | ZUBEHÖR   |
| `hub-cap2`        | hub_cap        | ZUBEHÖR   |
| `casters2`        | caster         | ZUBEHÖR   |
| `steering-lock2`  | steering_lock  | ZUBEHÖR   |
| `adapter2`        | wheel_adapter  | ZUBEHÖR   |
| `tube-cap2`       | tube_cap       | ZUBEHÖR   |
| `open-connector2` | open_end       | ZUBEHÖR   |
| `bag2`            | bag            | ZUBEHÖR   |
| `textil-round2`   | textile_round  | TEXTILIEN |
| `textil2`         | textile        | TEXTILIEN |
| `lattice2`        | lattice        | TEXTILIEN |
| `roof-large2`     | roof_large     | TEXTILIEN |
| `slide2`          | slide_module   | RUTSCHEN  |
| `slide-end2`      | slide_end      | RUTSCHEN  |
| `slide-new2`      | slide_integral | RUTSCHEN  |
| `curved-slide2`   | slide_curved   | RUTSCHEN  |

### 3.15 Nicht zugeordnete Elemente → `SONSTIGE`

Alle QDF-Zeilen, deren Element-Keyword nicht erkannt wird, erscheinen in der
Kategorie `SONSTIGE` mit dem Keyword als Bezeichnung.

Bekannte Elemente ohne Katalogeintrag:
- `alu2`, `alu-connector2` (Alu-Profile, nicht mehr erhältlich)
- `display2` (Anzeige-Panel)
- `roof2` (Dachkonstruktion)
- `pool2`, `pool-small2` (Pool-Rahmen; Folie separat zu bestimmen)

---

## 4 Lochplatten-Erkennung

### 4.1 Methode

Die Erkennung von Lochplatten erfolgt **ausschließlich über den Materialnamen**,
nicht über ein Flag-Feld in `panel2`. ✔

Materialien, deren Name auf `" (hole)"` endet, werden als Lochplatten-Material
markiert. Trägt eine `panel2`-Zeile eine solche `mat_id`, wird die Lochplatten-
Variante der Platte in der Stückliste gezählt.

```
material3{15,"red (hole)", 2, 1.,0.,0., ...}   → is_hole_material = True
panel2{15, {0., 2., 0., 2., 200., 1000., -400.}, 1, 350., 0., 350., 0., 0}
  → mat_id 15 ∈ hole_materials → panel_by_mm(400, 400, has_holes=True) → PO4
```

### 4.2 Herkunft der Kodierung

Lochplatten werden nur von Dateien erzeugt, die der **quadro-3D Web-Exporter**
exportiert hat. Hersteller-QDF-Dateien (wie C0048, C0091, C0145) enthalten
keine Lochplatten-Materialien und daher keine Lochplatten in der Stückliste.

Quellen: `3rdparty/quadro-3D/web/js/qdfimport.js` (HOLE_SUFFIX-Konstante
und holeMaterials-Set), eigene Messung an `qdf/C0145-mod.qdf`. ✔

### 4.3 Material-IDs in C0145-mod.qdf (Beispiel)

```
material3{15,"red (hole)", 2, ...}    → mat_id 15 = Lochplatte Rot
material3{16,"green (hole)", 2, ...}  → mat_id 16 = Lochplatte Grün
material3{17,"blue (hole)", 2, ...}   → mat_id 17 = Lochplatte Blau
material3{18,"yellow (hole)", 2, ...} → mat_id 18 = Lochplatte Gelb
material3{19,"black (hole)", 2, ...}  → mat_id 19 = Lochplatte Schwarz
```

---

## 5 Dead-Line-Filter (§3.5)

Teile, die in einer Step-History gelöscht wurden, erscheinen mit zwei
abschließenden ganzzahligen Step-Nummern (Geburts- und Todeszeitpunkt):

```
tube2{2, {...}, 1, 350., 0., 1, 3}   ← dead (Schritt 1 erzeugt, Schritt 3 gelöscht)
tube2{2, {...}, 1, 350., 0., 0}      ← live (nur Geburtsstep)
```

Der Parser erkennt dead lines über die Feldanzahl: wenn die tatsächliche Anzahl
nicht-tuple-Felder die erwartete Anzahl (`_LIVE_FIELDS[element]`) überschreitet,
wird die Zeile übersprungen. ✔

In Dateien mit Header `0, 0;` (kein History-Modus) gibt es keine dead lines.
Dies betrifft alle Hersteller-QDF-Dateien im Korpus. ✔

---

## 6 Bekannte Limitierungen und offene Fragen

| Punkt                                    | Status                                                               |
| ---------------------------------------- | -------------------------------------------------------------------- |
| TS1–TS7 nicht von T15/T35 unterscheidbar | Dokumentierte Limitation; in Praxis irrelevant (buildable: false)    |
| `hole-connector4` immer als CH3          | Arm-Varianten CH2/CH1 nicht unterschieden (qdf-Feld nur bei hole_t)  |
| `pool2` / `pool-small2` → SONSTIGE       | Poolfolie-Zuordnung erfordert Dimensions-Lookup, nicht implementiert |
| `display2` / `roof2` → SONSTIGE          | Kein Katalogeintrag                                                  |
| `alu2` → SONSTIGE                        | Alu-Profile nicht mehr erhältlich                                    |
| Farbname für unbekannte mat_ids          | Zeigt `"Mat.<id>"` statt Farbnamen                                   |
