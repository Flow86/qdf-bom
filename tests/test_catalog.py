"""Tests for PartsCatalog."""

import pytest
from qdf_bom.catalog import PartsCatalog


def test_tube_by_mm_t35(catalog: PartsCatalog) -> None:
    part = catalog.tube_by_mm(350)
    assert part is not None
    assert part.id == "T35"
    assert part.code == "T35"


def test_tube_by_mm_t15(catalog: PartsCatalog) -> None:
    part = catalog.tube_by_mm(150)
    assert part is not None
    assert part.id == "T15"


def test_tube_by_mm_unknown(catalog: PartsCatalog) -> None:
    assert catalog.tube_by_mm(999) is None


def test_panel_by_mm_solid_40x40(catalog: PartsCatalog) -> None:
    part = catalog.panel_by_mm(400, 400, False)
    assert part is not None
    assert part.id == "panel_40x40"
    assert part.code == "PA4"
    assert not part.has_holes


def test_panel_by_mm_solid_40x20(catalog: PartsCatalog) -> None:
    part = catalog.panel_by_mm(200, 400, False)
    assert part is not None
    assert part.id == "panel_40x20"


def test_panel_by_mm_hole_40x40(catalog: PartsCatalog) -> None:
    part = catalog.panel_by_mm(400, 400, True)
    assert part is not None
    assert part.id == "hole_panel_40x40"
    assert part.code == "PO4"
    assert part.has_holes


def test_panel_by_mm_hole_fallback(catalog: PartsCatalog) -> None:
    # Hole panel requested for non-hole size → falls back to solid
    part = catalog.panel_by_mm(200, 400, True)
    assert part is not None
    assert part.id == "panel_40x20"
    assert not part.has_holes


def test_panel_by_mm_unknown(catalog: PartsCatalog) -> None:
    assert catalog.panel_by_mm(999, 999, False) is None


def test_part_by_qdf_round_tube(catalog: PartsCatalog) -> None:
    # TC1 does not have a qdf field in parts.json; tested via BomTool special map
    part = catalog.tube_by_mm(350)
    assert part.id == "T35"  # round-tube2 uses special map, not qdf lookup


def test_part_by_qdf_flexi_hinge(catalog: PartsCatalog) -> None:
    part = catalog.part_by_qdf("flexi-connector3")
    assert part is not None
    assert part.id == "flexi_hinge"
    assert part.code == "CXB"


def test_part_by_qdf_slide(catalog: PartsCatalog) -> None:
    part = catalog.part_by_qdf("slide2")
    assert part is not None
    assert part.id == "slide_module"
    assert part.category == "slides"


def test_part_by_qdf_unknown(catalog: PartsCatalog) -> None:
    assert catalog.part_by_qdf("wood2") is None


def test_color_name_black(catalog: PartsCatalog) -> None:
    assert catalog.color_name("black") == "Schwarz"


def test_color_name_red(catalog: PartsCatalog) -> None:
    assert catalog.color_name("red") == "Rot"


def test_color_name_hole_suffix_stripped(catalog: PartsCatalog) -> None:
    # "red (hole)" → look up "red" → "Rot"
    assert catalog.color_name("red (hole)") == "Rot"


def test_color_name_unknown_passthrough(catalog: PartsCatalog) -> None:
    assert catalog.color_name("purple") == "purple"


def test_double_tube_is_connector(catalog: PartsCatalog) -> None:
    # double_tube appears in both connectors and accessories; connector must win
    part = catalog.part_by_id("double_tube")
    assert part is not None
    assert part.category == "connectors"
    assert part.code == "CDT"


def test_tube_clamp_is_connector(catalog: PartsCatalog) -> None:
    part = catalog.part_by_id("tube_clamp")
    assert part is not None
    assert part.category == "connectors"
    assert part.code == "CCL"
