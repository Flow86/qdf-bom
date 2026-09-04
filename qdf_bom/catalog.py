"""Parts catalog: loads and indexes parts.json."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

HOLE_SUFFIX = " (hole)"


@dataclass
class CatalogPart:
    id: str
    code: str
    name: str
    price: float
    category: str  # tubes | panels | connectors | accessories | reinforcements | screws | slides | textiles | pools
    qdf_name: str | None = None
    length_cm: float | None = None
    w: float | None = None
    h: float | None = None
    has_holes: bool = False
    arms: int | None = None
    kind: str | None = None   # space | planar | special
    arm_angle: int | None = None
    buildable: bool = True


class PartsCatalog:
    """Loads parts.json and provides indexed lookups."""

    def __init__(self, parts_json: dict) -> None:
        self._parts: dict[str, CatalogPart] = {}
        self._by_tube_mm: dict[int, CatalogPart] = {}
        self._by_panel_mm: dict[tuple[int, int, bool], CatalogPart] = {}
        self._by_qdf: dict[str, CatalogPart] = {}
        self._by_arms: dict[int, list[CatalogPart]] = {}
        self._color_names: dict[str, str] = {}
        self._build(parts_json)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _add(self, part: CatalogPart) -> None:
        """Register a part; first registration wins (connectors before accessories)."""
        if part.id in self._parts:
            return
        self._parts[part.id] = part
        if part.qdf_name:
            self._by_qdf.setdefault(part.qdf_name, part)

    def _build(self, parts: dict) -> None:
        # Colors
        for group in parts.get("colors", {}).values():
            if not isinstance(group, list):
                group = [group]
            for entry in group:
                self._color_names[entry["id"]] = entry["name"]

        # Connectors (registered first so duplicate IDs in accessories are skipped)
        for c in parts.get("connectors", []):
            p = CatalogPart(
                id=c["id"], code=c.get("code", ""), name=c["name"],
                price=c.get("price", 0.0), category="connectors",
                qdf_name=c.get("qdf"),
                arms=c.get("arms"),
                kind=c.get("kind"),
                arm_angle=c.get("angle"),
                buildable=c.get("buildable", True),
            )
            self._add(p)
            if p.arms is not None:
                self._by_arms.setdefault(p.arms, []).append(p)

        # Tubes
        for t in parts.get("tubes", []):
            p = CatalogPart(
                id=t["id"], code=t.get("code", ""), name=t["name"],
                price=t.get("price", 0.0), category="tubes",
                qdf_name=t.get("qdf"),
                length_cm=t.get("length_cm"),
                buildable=t.get("buildable", True),
            )
            self._add(p)
            shape = t.get("shape", "straight")
            if p.length_cm is not None and shape == "straight":
                mm = int(round(p.length_cm * 10))
                self._by_tube_mm.setdefault(mm, p)

        # Panels
        for pa in parts.get("panels", []):
            p = CatalogPart(
                id=pa["id"], code=pa.get("code", ""), name=pa["name"],
                price=pa.get("price", 0.0), category="panels",
                qdf_name=pa.get("qdf"),
                w=pa.get("w"), h=pa.get("h"),
                has_holes=bool(pa.get("holes")),
                buildable=pa.get("buildable", True),
            )
            self._add(p)
            if p.w is not None and p.h is not None:
                w_mm = int(round(p.w * 10))
                h_mm = int(round(p.h * 10))
                key = (min(w_mm, h_mm), max(w_mm, h_mm), p.has_holes)
                self._by_panel_mm[key] = p

        # Accessories (after connectors so duplicate IDs like double_tube, tube_clamp skip)
        for acc in parts.get("accessories", []):
            cat = _acc_category(acc)
            p = CatalogPart(
                id=acc["id"], code=acc.get("code", ""), name=acc["name"],
                price=acc.get("price", 0.0), category=cat,
                qdf_name=acc.get("qdf"),
                buildable=acc.get("buildable", True),
            )
            self._add(p)

        # Reinforcements
        for r in parts.get("reinforcements", []):
            p = CatalogPart(
                id=r["id"], code=r.get("code", ""), name=r["name"],
                price=r.get("price", 0.0), category="reinforcements",
                qdf_name=r.get("qdf"),
                length_cm=r.get("length_cm"),
                buildable=r.get("buildable", True),
            )
            self._add(p)

        # Screws
        for s in parts.get("screws", []):
            p = CatalogPart(
                id=s["id"], code=s.get("code", ""), name=s["name"],
                price=s.get("price", 0.0), category="screws",
                qdf_name=s.get("qdf"),
                buildable=s.get("buildable", True),
            )
            self._add(p)

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------

    def part_by_id(self, part_id: str) -> CatalogPart | None:
        return self._parts.get(part_id)

    def part_by_qdf(self, qdf_name: str) -> CatalogPart | None:
        return self._by_qdf.get(qdf_name)

    def tube_by_mm(self, length_mm: int) -> CatalogPart | None:
        return self._by_tube_mm.get(length_mm)

    def panel_by_mm(self, short_mm: int, long_mm: int, has_holes: bool) -> CatalogPart | None:
        key = (min(short_mm, long_mm), max(short_mm, long_mm), has_holes)
        part = self._by_panel_mm.get(key)
        if part is None and has_holes:
            # Fallback to solid panel of same dimensions
            fallback = (min(short_mm, long_mm), max(short_mm, long_mm), False)
            part = self._by_panel_mm.get(fallback)
        return part

    def connectors_by_arms(self, arms: int) -> list[CatalogPart]:
        return self._by_arms.get(arms, [])

    def color_name(self, material_name: str) -> str:
        """Map QDF material name (e.g. 'black') to display name (e.g. 'Schwarz').

        Strips the hole suffix if present before lookup.
        """
        name = material_name
        if name.endswith(HOLE_SUFFIX):
            name = name[: -len(HOLE_SUFFIX)]
        return self._color_names.get(name, name)

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_file(cls, path: Path) -> "PartsCatalog":
        with open(path, encoding="utf-8") as f:
            return cls(json.load(f))

    @classmethod
    def from_default(cls) -> "PartsCatalog":
        """Load from data/parts.json.

        Supports both normal install and PyInstaller one-file bundles
        (where sys._MEIPASS points to the unpacked temp directory).
        """
        import sys
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            base = Path(sys._MEIPASS)
        else:
            base = Path(__file__).parent.parent
        return cls.from_file(base / "data" / "parts.json")


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _acc_category(acc: dict) -> str:
    if "pool" in acc:
        return "pools"
    name = acc.get("name", "").lower()
    if any(k in name for k in ("textil", "netz", "rundwand", "dachtextil")):
        return "textiles"
    if any(k in name for k in ("rutsche", "auslauf", "bogenrutschen")):
        return "slides"
    return "accessories"
