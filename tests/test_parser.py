"""Tests for QdfParser."""

import pytest
from qdf_bom.parser import (
    Connector45Record,
    ConnectorRecord,
    MaterialRecord,
    PanelRecord,
    QdfParser,
    SpecialPartRecord,
    TubeRecord,
    UnknownRecord,
)
from tests.conftest import (
    CONNECTOR_LINES,
    DEAD_TUBE_LINES,
    MATERIAL_LINES,
    PANEL_LINES,
    TUBE_LINES,
)


@pytest.fixture
def parser() -> QdfParser:
    return QdfParser()


# ---------------------------------------------------------------------------
# material3
# ---------------------------------------------------------------------------

def test_material_parse(parser: QdfParser) -> None:
    records = parser.parse(MATERIAL_LINES)
    mats = [r for r in records if isinstance(r, MaterialRecord)]
    assert len(mats) == 4
    black = next(m for m in mats if m.mat_id == 1)
    assert black.color_name == "black"
    assert not black.is_hole_material


def test_hole_material(parser: QdfParser) -> None:
    records = parser.parse(MATERIAL_LINES)
    mats = [r for r in records if isinstance(r, MaterialRecord)]
    hole = next(m for m in mats if m.mat_id == 15)
    assert hole.color_name == "red (hole)"
    assert hole.is_hole_material


# ---------------------------------------------------------------------------
# tube2
# ---------------------------------------------------------------------------

def test_tube_t35(parser: QdfParser) -> None:
    records = parser.parse(TUBE_LINES)
    tubes = [r for r in records if isinstance(r, TubeRecord)]
    assert any(t.length_mm == 350 and t.element == "tube2" and t.mat_id == 2 for t in tubes)


def test_tube_t15(parser: QdfParser) -> None:
    records = parser.parse(TUBE_LINES)
    tubes = [r for r in records if isinstance(r, TubeRecord)]
    assert any(t.length_mm == 150 and t.element == "tube2" for t in tubes)


def test_round_tube(parser: QdfParser) -> None:
    records = parser.parse(TUBE_LINES)
    tubes = [r for r in records if isinstance(r, TubeRecord)]
    assert any(t.element == "round-tube2" for t in tubes)


# ---------------------------------------------------------------------------
# Dead-line filter
# ---------------------------------------------------------------------------

def test_dead_tube_filtered(parser: QdfParser) -> None:
    records = parser.parse(DEAD_TUBE_LINES)
    tubes = [r for r in records if isinstance(r, TubeRecord)]
    # Only the 150mm tube is live; the 350mm tube has two trailing step numbers → dead
    assert len(tubes) == 1
    assert tubes[0].length_mm == 150


# ---------------------------------------------------------------------------
# panel2
# ---------------------------------------------------------------------------

def test_panel_solid(parser: QdfParser) -> None:
    records = parser.parse(PANEL_LINES)
    panels = [r for r in records if isinstance(r, PanelRecord)]
    solid = next(p for p in panels if p.mat_id == 7)
    assert solid.w_mm == 350
    assert solid.h_mm == 350


def test_panel_hole_mat(parser: QdfParser) -> None:
    records = parser.parse(PANEL_LINES)
    panels = [r for r in records if isinstance(r, PanelRecord)]
    hole = next(p for p in panels if p.mat_id == 15)
    assert hole.w_mm == 350
    assert hole.h_mm == 350


# ---------------------------------------------------------------------------
# connector3
# ---------------------------------------------------------------------------

def test_connector3_arm_mask(parser: QdfParser) -> None:
    records = parser.parse(CONNECTOR_LINES)
    conns = [r for r in records if isinstance(r, ConnectorRecord)]
    assert len(conns) == 2
    assert conns[0].arm_mask == 13   # bits 0,2,3 → +X, +Y, -Y
    assert conns[1].arm_mask == 21   # bits 0,2,4 → +X, +Y, +Z


# ---------------------------------------------------------------------------
# connector45_2
# ---------------------------------------------------------------------------

def test_connector45(parser: QdfParser) -> None:
    records = parser.parse(CONNECTOR_LINES)
    c45 = [r for r in records if isinstance(r, Connector45Record)]
    assert len(c45) == 1
    assert c45[0].mat_id == 1


# ---------------------------------------------------------------------------
# clamp2 / clip2
# ---------------------------------------------------------------------------

def test_clamp2(parser: QdfParser) -> None:
    records = parser.parse(CONNECTOR_LINES)
    specials = [r for r in records if isinstance(r, SpecialPartRecord)]
    clamps = [s for s in specials if s.element_name == "clamp2"]
    assert len(clamps) == 1


# ---------------------------------------------------------------------------
# Unknown elements
# ---------------------------------------------------------------------------

def test_unknown_element(parser: QdfParser) -> None:
    qdf = "0, 0;\nwood2{1, {4., 0., 0., 0., 0., 0., 0.}, 1, 0}\n"
    records = parser.parse(qdf)
    unknown = [r for r in records if isinstance(r, UnknownRecord)]
    assert len(unknown) == 1
    assert unknown[0].element_name == "wood2"


def test_camera_skipped(parser: QdfParser) -> None:
    qdf = "0, 0;\ncamera2{1040, 150, -1, 0, 0, 0, 0, 0, 25}\n"
    records = parser.parse(qdf)
    assert not any(isinstance(r, UnknownRecord) for r in records)
