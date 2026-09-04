"""Integration tests: inline QDF snippets through the full BOM pipeline."""

from qdf_bom.catalog import PartsCatalog
from qdf_bom.tool import BomTool

# ---------------------------------------------------------------------------
# Inline QDF fixtures — no proprietary files required
# ---------------------------------------------------------------------------

_MAT_HEADER = """\
0, 0;
material3{1,"rot", 1, 1.,0.,0., 0.5,1.,1.,7.5, 0.3,0.,0.,7.5, "", 0}
material3{2,"blau", 1, 0.,0.,1., 0.,0.,1.,7.5, 0.,0.,0.,7.5, "", 0}
"""

_MAT_HOLE = """\
0, 0;
material3{1,"rot", 1, 1.,0.,0., 0.5,1.,1.,7.5, 0.3,0.,0.,7.5, "", 0}
material3{2,"rot (hole)", 1, 1.,0.,0., 0.5,1.,1.,7.5, 0.3,0.,0.,7.5, "", 0}
"""

# 3 × T35 (mat 1) + 2 × T35 (mat 2) + 1 × T15 (mat 1)
_TUBES_QDF = _MAT_HEADER + """\
tube2{1, {2., 0., 0., 2., 800., 0., 0.}, 1, 350., 0., 0}
tube2{1, {2., 0., 0., 2., 800., 0., 0.}, 1, 350., 0., 0}
tube2{1, {2., 0., 0., 2., 800., 0., 0.}, 1, 350., 0., 0}
tube2{2, {2., 0., 0., 2., 800., 0., 0.}, 1, 350., 0., 0}
tube2{2, {2., 0., 0., 2., 800., 0., 0.}, 1, 350., 0., 0}
tube2{1, {2., 0., 0., 2., 400., 0., 0.}, 1, 150., 0., 0}
"""

# solid panel (mat 1) and hole panel (mat 2 = hole material)
_PANELS_QDF = _MAT_HOLE + """\
panel2{1, {0., 0., 2., 2., 600., 600., -200.}, 1, 350., 0., 350., 0., 0}
panel2{2, {0., 0., 2., 2., 600., 600., -200.}, 1, 350., 0., 350., 0., 0}
"""

# dead tube (two trailing step numbers) must not be counted
_DEAD_LINE_QDF = _MAT_HEADER + """\
tube2{1, {2., 0., 0., 2., 800., 0., 0.}, 1, 350., 0., 1, 3}
tube2{1, {2., 0., 0., 2., 400., 0., 0.}, 1, 150., 0., 0}
"""

# connector3 (6-way, mask=63), connector45, clamp2, clip2
_CONNECTORS_QDF = _MAT_HEADER + """\
connector3{1, {4., 0., 0., 0., 0., 1200., 0.}, 1, 0, 63, 0, 4095, 0}
connector3{1, {4., 0., 0., 0., 0., 1200., 0.}, 1, 0, 63, 0, 4095, 0}
connector45_2{1, {2., 0., 2., 0., 0., 1600., -400.}, 1, 0, 0}
clamp2{1, {2., 0., -2., 0., 800., 400., 60.}, 1, 0}
clip2{1, {2., 0., 0., 0., 400., 800., 0.}, 1, 0}
"""

# slide elements
_SLIDES_QDF = _MAT_HEADER + """\
slide2{1, {4., 0., 0., 0., 0., 0., 0.}, 1, 0}
slide-end2{1, {4., 0., 0., 0., 0., 0., 0.}, 1, 0}
"""


def _tool(catalog: PartsCatalog) -> BomTool:
    return BomTool(catalog)


# ---------------------------------------------------------------------------
# Tubes
# ---------------------------------------------------------------------------

def test_tube_total(catalog: PartsCatalog) -> None:
    counter, _ = _tool(catalog).process(_TUBES_QDF)
    assert sum(cnt for _, cnt in counter.items("tubes")) == 6


def test_tube_t35_count(catalog: PartsCatalog) -> None:
    counter, _ = _tool(catalog).process(_TUBES_QDF)
    t35 = sum(cnt for (pid, _), cnt in counter.items("tubes") if pid == "T35")
    assert t35 == 5


def test_tube_t15_count(catalog: PartsCatalog) -> None:
    counter, _ = _tool(catalog).process(_TUBES_QDF)
    t15 = sum(cnt for (pid, _), cnt in counter.items("tubes") if pid == "T15")
    assert t15 == 1


# ---------------------------------------------------------------------------
# Panels + hole detection
# ---------------------------------------------------------------------------

def test_solid_panel_counted(catalog: PartsCatalog) -> None:
    counter, _ = _tool(catalog).process(_PANELS_QDF)
    panel_ids = {pid for (pid, _), _ in counter.items("panels")}
    assert "panel_40x40" in panel_ids


def test_hole_panel_detected(catalog: PartsCatalog) -> None:
    counter, _ = _tool(catalog).process(_PANELS_QDF)
    panel_ids = {pid for (pid, _), _ in counter.items("panels")}
    assert "hole_panel_40x40" in panel_ids


# ---------------------------------------------------------------------------
# Dead-line filter
# ---------------------------------------------------------------------------

def test_dead_tube_not_counted(catalog: PartsCatalog) -> None:
    counter, _ = _tool(catalog).process(_DEAD_LINE_QDF)
    total = sum(cnt for _, cnt in counter.items("tubes"))
    assert total == 1  # only the live T15; dead T35 excluded


# ---------------------------------------------------------------------------
# Connectors
# ---------------------------------------------------------------------------

def test_6way_connector(catalog: PartsCatalog) -> None:
    counter, _ = _tool(catalog).process(_CONNECTORS_QDF)
    c6 = sum(cnt for (pid, _), cnt in counter.items("connectors") if pid == "6way")
    assert c6 == 2


def test_diagonal_connector45(catalog: PartsCatalog) -> None:
    counter, _ = _tool(catalog).process(_CONNECTORS_QDF)
    c45 = sum(cnt for (pid, _), cnt in counter.items("connectors") if pid == "diagonal")
    assert c45 == 1


def test_clamp2_maps_to_double_tube(catalog: PartsCatalog) -> None:
    counter, _ = _tool(catalog).process(_CONNECTORS_QDF)
    cdt = sum(cnt for (pid, _), cnt in counter.items("connectors") if pid == "double_tube")
    assert cdt == 1


def test_clip2_maps_to_tube_clamp(catalog: PartsCatalog) -> None:
    counter, _ = _tool(catalog).process(_CONNECTORS_QDF)
    ccl = sum(cnt for (pid, _), cnt in counter.items("connectors") if pid == "tube_clamp")
    assert ccl == 1


def test_no_unknowns_in_connector_qdf(catalog: PartsCatalog) -> None:
    counter, _ = _tool(catalog).process(_CONNECTORS_QDF)
    assert not counter.items("other")


# ---------------------------------------------------------------------------
# Slides
# ---------------------------------------------------------------------------

def test_slide_elements_categorised(catalog: PartsCatalog) -> None:
    counter, _ = _tool(catalog).process(_SLIDES_QDF)
    assert sum(cnt for _, cnt in counter.items("slides")) == 2


# ---------------------------------------------------------------------------
# Report format
# ---------------------------------------------------------------------------

def test_report_contains_sections(catalog: PartsCatalog) -> None:
    report = _tool(catalog)._reporter.render(
        _tool(catalog).process(_TUBES_QDF)[0], "test.qdf"
    )
    assert "QUADRO-Stückliste" in report
    assert "ROHRE" in report
    assert "= " in report  # category total line
