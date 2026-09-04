"""BomTool: orchestrates parsing, classification, and report generation."""

from __future__ import annotations

import sys
from pathlib import Path

from .bom import BomCounter, BomReport
from .catalog import PartsCatalog
from .classifier import ConnectorClassifier
from .parser import (
    Connector45Record,
    ConnectorRecord,
    MaterialRecord,
    PanelRecord,
    QdfParser,
    SpecialPartRecord,
    TubeRecord,
    UnknownRecord,
)

# QDF element names that map directly to a catalog part_id (no qdf field in parts.json)
_SPECIAL_ELEMENT_MAP: dict[str, str] = {
    "clamp2":       "double_tube",   # Doppelrohrverbinder (CDT)
    "clip2":        "tube_clamp",    # Rohrklammer (CCL)
    "round-tube2":  "TC1",           # Bogenrohr
}

# Connector size contribution per connector end (mm), added to part size for grid lookup
_DEFAULT_CONNECTOR_SIZE_MM = 50


class BomTool:
    """End-to-end BOM processor for a single QDF file."""

    def __init__(
        self,
        catalog: PartsCatalog,
        connector_size_mm: int = _DEFAULT_CONNECTOR_SIZE_MM,
    ) -> None:
        self._catalog = catalog
        self._connector_size_mm = connector_size_mm
        self._parser = QdfParser()
        self._classifier = ConnectorClassifier(catalog)
        self._reporter = BomReport(catalog)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, qdf_text: str) -> tuple[BomCounter, dict[int, str]]:
        """Parse QDF text and return (BomCounter, mat_id→color_name mapping)."""
        records = self._parser.parse(qdf_text)

        # First pass: collect materials
        hole_mat_ids: set[int] = set()
        mat_colors: dict[int, str] = {}
        for rec in records:
            if isinstance(rec, MaterialRecord):
                mat_colors[rec.mat_id] = rec.color_name
                if rec.is_hole_material:
                    hole_mat_ids.add(rec.mat_id)

        counter = BomCounter()

        # Second pass: count parts
        for rec in records:
            if isinstance(rec, MaterialRecord):
                continue

            if isinstance(rec, TubeRecord):
                self._count_tube(rec, counter)

            elif isinstance(rec, PanelRecord):
                self._count_panel(rec, hole_mat_ids, counter)

            elif isinstance(rec, ConnectorRecord):
                self._count_connector3(rec, counter)

            elif isinstance(rec, Connector45Record):
                self._count_connector45(rec, counter)

            elif isinstance(rec, SpecialPartRecord):
                self._count_special(rec, counter)

            elif isinstance(rec, UnknownRecord):
                counter.add_unknown(rec.element_name, rec.mat_id)

        return counter, mat_colors

    def run_file(self, path: Path) -> str:
        """Read a QDF file, process it, and return the formatted report."""
        text = path.read_text(encoding="utf-8", errors="replace")
        counter, mat_colors = self.process(text)
        return self._reporter.render(counter, path.name, mat_colors)

    # ------------------------------------------------------------------
    # Part counting helpers
    # ------------------------------------------------------------------

    def _count_tube(self, rec: TubeRecord, counter: BomCounter) -> None:
        # Special-map for round-tube2 (TC1, Bogenrohr)
        direct_id = _SPECIAL_ELEMENT_MAP.get(rec.element)
        if direct_id:
            part = self._catalog.part_by_id(direct_id)
            if part:
                counter.add(part.category, part.id, rec.mat_id)
                return

        # Lookup by qdf name (alu2, alu-connector2 could have qdf entries in future)
        part = self._catalog.part_by_qdf(rec.element)
        if part is None:
            part = self._catalog.tube_by_mm(rec.length_mm)

        if part:
            counter.add(part.category, part.id, rec.mat_id)
        else:
            counter.add_unknown(rec.element, rec.mat_id)

    def _count_panel(
        self, rec: PanelRecord, hole_mat_ids: set[int], counter: BomCounter
    ) -> None:
        has_holes = rec.mat_id in hole_mat_ids
        cs = self._connector_size_mm
        short = min(rec.w_mm, rec.h_mm) + cs
        long = max(rec.w_mm, rec.h_mm) + cs
        part = self._catalog.panel_by_mm(short, long, has_holes)
        if part:
            counter.add(part.category, part.id, rec.mat_id)
        else:
            counter.add_unknown("panel2", rec.mat_id)

    def _count_connector3(self, rec: ConnectorRecord, counter: BomCounter) -> None:
        part_id = self._classifier.classify(rec.arm_mask)
        part = self._catalog.part_by_id(part_id)
        category = part.category if part else "connectors"
        counter.add(category, part_id, rec.mat_id)

    def _count_connector45(self, rec: Connector45Record, counter: BomCounter) -> None:
        part = self._catalog.part_by_id("diagonal")
        if part:
            counter.add(part.category, part.id, rec.mat_id)
        else:
            counter.add_unknown("connector45_2", rec.mat_id)

    def _count_special(self, rec: SpecialPartRecord, counter: BomCounter) -> None:
        # Direct map (clamp2, clip2, round-tube2)
        direct_id = _SPECIAL_ELEMENT_MAP.get(rec.element_name)
        if direct_id:
            part = self._catalog.part_by_id(direct_id)
            if part:
                counter.add(part.category, part.id, rec.mat_id)
                return

        # Lookup by qdf name
        part = self._catalog.part_by_qdf(rec.element_name)
        if part:
            counter.add(part.category, part.id, rec.mat_id)
        else:
            counter.add_unknown(rec.element_name, rec.mat_id)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print("Verwendung: python -m qdf_bom <datei.qdf> [<datei2.qdf> ...]")
        return 2

    catalog = PartsCatalog.from_default()
    tool = BomTool(catalog)

    for arg in argv:
        path = Path(arg)
        if not path.is_file():
            print(f"Datei nicht gefunden: {path}", file=sys.stderr)
            continue

        report = tool.run_file(path)
        print(report)

        out = path.with_name(path.stem + "_partslist.txt")
        out.write_text(report + "\n", encoding="utf-8")
        print(f"Gespeichert: {out}", file=sys.stderr)

    return 0
