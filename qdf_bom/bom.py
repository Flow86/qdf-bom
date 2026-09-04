"""BOM counter and report renderer."""

from __future__ import annotations

from collections import defaultdict

from .catalog import PartsCatalog

CATEGORY_ORDER = [
    "tubes",
    "panels",
    "connectors",
    "accessories",
    "reinforcements",
    "textiles",
    "slides",
    "pools",
    "screws",
    "other",
]

CATEGORY_LABELS: dict[str, str] = {
    "tubes":          "ROHRE",
    "panels":         "PLATTEN",
    "connectors":     "KUPPLUNGEN / VERBINDER",
    "accessories":    "ZUBEHÖR",
    "reinforcements": "VERSTEIFUNGEN",
    "textiles":       "TEXTILIEN",
    "slides":         "RUTSCHEN",
    "pools":          "POOLS / FOLIEN",
    "screws":         "SCHRAUBEN",
    "other":          "SONSTIGE",
}


class BomCounter:
    """Accumulates part counts keyed by (part_id, mat_id)."""

    def __init__(self) -> None:
        # category → {(part_id, mat_id): count}
        self._counts: dict[str, dict[tuple[str, int | None], int]] = defaultdict(dict)

    def add(self, category: str, part_id: str, mat_id: int | None, count: int = 1) -> None:
        key = (part_id, mat_id)
        bucket = self._counts[category]
        bucket[key] = bucket.get(key, 0) + count

    def add_unknown(self, element_name: str, mat_id: int | None) -> None:
        key = (element_name, mat_id)
        bucket = self._counts["other"]
        bucket[key] = bucket.get(key, 0) + 1

    def category_totals(self) -> dict[str, int]:
        return {cat: sum(v.values()) for cat, v in self._counts.items()}

    def grand_total(self) -> int:
        return sum(sum(v.values()) for v in self._counts.values())

    def items(self, category: str) -> list[tuple[tuple[str, int | None], int]]:
        return sorted(self._counts.get(category, {}).items())


class BomReport:
    """Renders a BomCounter to a human-readable text report."""

    def __init__(self, catalog: PartsCatalog) -> None:
        self._catalog = catalog

    def render(
        self,
        counter: BomCounter,
        filename: str,
        mat_colors: dict[int, str] | None = None,
    ) -> str:
        """Render the BOM report.

        Args:
            counter:    Populated BomCounter.
            filename:   QDF file name shown in the header (e.g. "C0048.qdf").
            mat_colors: Optional mapping of mat_id → raw color name from material3 lines.
                        Falls back to catalog.color_name("") when absent.
        """
        stem = filename.rpartition(".")[0] or filename
        lines: list[str] = []
        lines.append(f"QUADRO-Stückliste: {filename}")
        lines.append("=" * max(64, len(lines[-1])))
        lines.append("")
        lines.append(f"Link: https://quadroworld.com/de/designs/{stem}")
        lines.append("")

        for category in CATEGORY_ORDER:
            items = counter.items(category)
            if not items:
                continue

            lines.append(CATEGORY_LABELS[category])
            lines.append("-" * 64)

            for (part_id, mat_id), count in items:
                colour = self._resolve_color(mat_id, mat_colors)
                if category == "other":
                    # Unknown parts: part_id is the QDF element name
                    name = part_id
                    code = ""
                else:
                    part = self._catalog.part_by_id(part_id)
                    name = part.name if part else part_id
                    code = part.code if part else ""

                if code:
                    lines.append(f"{code:<6} {name:<40} {colour:<10} x {count:>3}")
                else:
                    lines.append(f"       {name:<40} {colour:<10} x {count:>3}")

            lines.append("")

        lines.append(f"ERKANNTE BAUTEIL-OBJEKTE GESAMT: {counter.grand_total()}")
        lines.append("")
        return "\n".join(lines)

    def _resolve_color(self, mat_id: int | None, mat_colors: dict[int, str] | None) -> str:
        if mat_id is None:
            return ""
        raw = (mat_colors or {}).get(mat_id, "")
        return self._catalog.color_name(raw) if raw else f"Mat.{mat_id}"
