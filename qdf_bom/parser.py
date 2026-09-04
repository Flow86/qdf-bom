"""QDF file parser.

Parses QDF lines into typed record objects and filters dead lines (§3.5).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Union

# ---------------------------------------------------------------------------
# Record types
# ---------------------------------------------------------------------------


@dataclass
class MaterialRecord:
    mat_id: int
    color_name: str       # raw name from QDF, e.g. "black" or "red (hole)"
    is_hole_material: bool


@dataclass
class TubeRecord:
    mat_id: int
    length_mm: int
    element: str          # "tube2" | "round-tube2" | "alu2" | "alu-connector2"


@dataclass
class PanelRecord:
    mat_id: int
    w_mm: int             # part size (without connector contribution)
    h_mm: int


@dataclass
class ConnectorRecord:
    mat_id: int
    arm_mask: int


@dataclass
class Connector45Record:
    mat_id: int


@dataclass
class SpecialPartRecord:
    mat_id: int
    element_name: str     # QDF element keyword, e.g. "flexi-connector3"


@dataclass
class UnknownRecord:
    mat_id: int | None
    element_name: str


QdfRecord = Union[
    MaterialRecord,
    TubeRecord,
    PanelRecord,
    ConnectorRecord,
    Connector45Record,
    SpecialPartRecord,
    UnknownRecord,
]

# ---------------------------------------------------------------------------
# Known live-line field counts (non-tuple fields, including mat_id + birth_step)
# Used for dead-line detection (§3.5): if actual count > expected, it's dead.
# ---------------------------------------------------------------------------

_LIVE_FIELDS: dict[str, int] = {
    "tube2":              5,  # mat, flag, len_mm, addition, step
    "round-tube2":        5,
    "alu2":               5,
    "alu-connector2":     5,
    "connector3":         7,  # mat, flag, ?, arm_mask, complement, face_mask, step
    "connector45_2":      4,  # mat, flag, ?, step
    "panel2":             7,  # mat, flag, w_mm, w_add, h_mm, h_add, step
    "display2":           7,
    "textil2":            7,
    "lattice2":           7,
    "hole-connector4":    8,  # mat, flag, ?, mask, ?, ?, ?, step
    "bearing-connector4": 5,
    "flexi-connector3":   8,  # mat, flag, ?, ?, ?, ?, ?, step
    "bolt2":              5,  # mat, flag, len_mm, ?, step
    "bearing2":           5,  # mat, flag, 50., 0., step
    "clamp2":             3,  # mat, flag, step
    "clip2":              4,  # mat, flag, ?, step
    "textil-round2":      4,
    "pool2":              3,  # mat, flag, step
    "pool-small2":        3,
    "slide2":             3,
    "slide-end2":         3,
    "slide-new2":         3,
    "curved-slide2":      3,
    "roof2":              3,
    "roof-large2":        3,
    "open-connector2":    3,
    "adapter2":           3,
    "tube-cap2":          3,
    "multi-wheel2":       3,
    "floating-wheel2":    3,
    "hub-cap2":           3,
    "casters2":           3,
    "steering-lock2":     3,
    "bag2":               3,
}

# Elements handled via dedicated record types (not SpecialPartRecord)
_DEDICATED = frozenset(
    ["material3", "tube2", "round-tube2", "alu2", "alu-connector2",
     "connector3", "connector45_2", "panel2", "clamp2", "clip2"]
)

# Elements that produce a SpecialPartRecord (recognised but not dedicated)
_SPECIAL = frozenset([
    "flexi-connector3", "bolt2", "hole-connector4", "bearing-connector4",
    "bearing2", "textil2", "textil-round2", "lattice2", "display2",
    "slide2", "slide-end2", "slide-new2", "curved-slide2",
    "roof2", "roof-large2", "multi-wheel2", "floating-wheel2",
    "hub-cap2", "casters2", "steering-lock2", "adapter2",
    "tube-cap2", "open-connector2", "bag2",
    "pool2", "pool-small2",
])

# Elements that are not parts and should be silently skipped
_SKIP = frozenset([
    "camera2",
])

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

_HOLE_SUFFIX = " (hole)"
_ELEMENT_RE = re.compile(r"^([A-Za-z][\w-]*)\{(.*)\}\s*;?\s*$")
_INNER_TUPLE_RE = re.compile(r"\{([^{}]*)\}")
_STRING_RE = re.compile(r'"([^"]*)"')


def _tokenize(body: str) -> tuple[list | None, list]:
    """Extract optional inner tuple and remaining scalar fields from a QDF body.

    Returns (tuple_values_or_None, scalar_fields).
    Scalar fields contain int for integers without dot, float for reals, str for strings.
    """
    # Extract inner tuple {…}
    tm = _INNER_TUPLE_RE.search(body)
    tuple_vals: list | None = None
    if tm:
        tuple_vals = [float(x.strip()) for x in tm.group(1).split(",") if x.strip()]
        body = body[: tm.start()] + body[tm.end():]

    fields: list = []
    # Tokenize remaining body by comma, preserving quoted strings
    i = 0
    tokens: list[str] = []
    start = 0
    in_quote = False
    for i, ch in enumerate(body):
        if ch == '"':
            in_quote = not in_quote
        elif ch == ',' and not in_quote:
            tokens.append(body[start:i].strip())
            start = i + 1
    tokens.append(body[start:].strip())

    for tok in tokens:
        tok = tok.strip()
        if not tok:
            continue
        sm = _STRING_RE.match(tok)
        if sm:
            fields.append(sm.group(1))
            continue
        if re.match(r"^-?\d+$", tok):
            fields.append(int(tok))
        else:
            try:
                fields.append(float(tok))
            except ValueError:
                fields.append(tok)

    return tuple_vals, fields


def _is_dead(element: str, fields: list) -> bool:
    """Return True if this line describes a deleted part (§3.5).

    A dead line has one extra trailing field (the death step) compared to a live line.
    """
    expected = _LIVE_FIELDS.get(element)
    if expected is None:
        return False
    return len(fields) > expected


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class QdfParser:
    """Parses a QDF text and returns a list of typed records.

    Dead lines (§3.5) and non-part lines (camera, header) are excluded.
    Unrecognised elements produce UnknownRecord — nothing is silently dropped.
    """

    def parse(self, text: str) -> list[QdfRecord]:
        records: list[QdfRecord] = []
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line[0].isdigit():
                # Header line ("0, 0;") or blank
                continue
            rec = self._parse_line(line)
            if rec is not None:
                records.append(rec)
        return records

    def _parse_line(self, line: str) -> QdfRecord | None:
        m = _ELEMENT_RE.match(line)
        if not m:
            return None
        element = m.group(1)
        body = m.group(2)

        if element in _SKIP:
            return None

        _, fields = _tokenize(body)

        if element == "material3":
            return self._parse_material(fields)

        if _is_dead(element, fields):
            return None

        if element in ("tube2", "round-tube2", "alu2", "alu-connector2"):
            return self._parse_tube(element, fields)

        if element == "connector3":
            return self._parse_connector3(fields)

        if element == "connector45_2":
            return self._parse_connector45(fields)

        if element == "panel2":
            return self._parse_panel(fields)

        if element == "clamp2":
            return self._parse_simple_special("clamp2", fields)

        if element == "clip2":
            return self._parse_simple_special("clip2", fields)

        if element in _SPECIAL:
            return self._parse_simple_special(element, fields)

        return UnknownRecord(mat_id=_first_int(fields), element_name=element)

    # ------------------------------------------------------------------
    # Individual parsers
    # ------------------------------------------------------------------

    def _parse_material(self, fields: list) -> MaterialRecord | None:
        if len(fields) < 2:
            return None
        mat_id = fields[0] if isinstance(fields[0], int) else None
        color_name = fields[1] if isinstance(fields[1], str) else None
        if mat_id is None or color_name is None:
            return None
        is_hole = color_name.endswith(_HOLE_SUFFIX)
        return MaterialRecord(mat_id=mat_id, color_name=color_name, is_hole_material=is_hole)

    def _parse_tube(self, element: str, fields: list) -> TubeRecord | None:
        # fields: mat_id, flag, length_mm, addition, birth_step
        if len(fields) < 3:
            return None
        mat_id = fields[0] if isinstance(fields[0], int) else None
        length_raw = fields[2]
        if mat_id is None:
            return None
        try:
            length_mm = int(round(float(length_raw)))
        except (TypeError, ValueError):
            return None
        return TubeRecord(mat_id=mat_id, length_mm=length_mm, element=element)

    def _parse_connector3(self, fields: list) -> ConnectorRecord | None:
        # fields: mat_id, flag, ?, arm_mask, complement, face_mask, birth_step
        if len(fields) < 4:
            return None
        mat_id = fields[0] if isinstance(fields[0], int) else None
        arm_mask_raw = fields[3]
        if mat_id is None:
            return None
        try:
            arm_mask = int(arm_mask_raw)
        except (TypeError, ValueError):
            return None
        return ConnectorRecord(mat_id=mat_id, arm_mask=arm_mask)

    def _parse_connector45(self, fields: list) -> Connector45Record | None:
        if not fields:
            return None
        mat_id = fields[0] if isinstance(fields[0], int) else None
        if mat_id is None:
            return None
        return Connector45Record(mat_id=mat_id)

    def _parse_panel(self, fields: list) -> PanelRecord | None:
        # fields: mat_id, flag, w_mm, w_add, h_mm, h_add, birth_step
        if len(fields) < 5:
            return None
        mat_id = fields[0] if isinstance(fields[0], int) else None
        if mat_id is None:
            return None
        try:
            w_mm = int(round(float(fields[2])))
            h_mm = int(round(float(fields[4])))
        except (TypeError, ValueError):
            return None
        return PanelRecord(mat_id=mat_id, w_mm=w_mm, h_mm=h_mm)

    def _parse_simple_special(self, element: str, fields: list) -> SpecialPartRecord | None:
        mat_id = _first_int(fields)
        if mat_id is None:
            return None
        return SpecialPartRecord(mat_id=mat_id, element_name=element)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _first_int(fields: list) -> int | None:
    for f in fields:
        if isinstance(f, int):
            return f
    return None
