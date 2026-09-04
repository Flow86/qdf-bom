"""Integration tests: real QDF files through the full BOM pipeline."""

from pathlib import Path

import pytest

from qdf_bom.catalog import PartsCatalog
from qdf_bom.tool import BomTool

REPO_ROOT = Path(__file__).parent.parent
QDF_DIR = REPO_ROOT / "qdf"


def _tool(catalog: PartsCatalog) -> BomTool:
    return BomTool(catalog)


# ---------------------------------------------------------------------------
# C0048 – known reference model (no hole panels, no dead lines)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not (QDF_DIR / "C0048.qdf").exists(), reason="C0048.qdf not found")
def test_c0048_no_hole_panels(catalog: PartsCatalog) -> None:
    tool = _tool(catalog)
    text = (QDF_DIR / "C0048.qdf").read_text(encoding="utf-8")
    counter, mat_colors = tool.process(text)
    items = counter.items("panels")
    panel_ids = {pid for (pid, _), _ in items}
    assert "hole_panel_40x40" not in panel_ids, (
        "C0048 has no hole materials → no hole panels expected"
    )


@pytest.mark.skipif(not (QDF_DIR / "C0048.qdf").exists(), reason="C0048.qdf not found")
def test_c0048_tubes(catalog: PartsCatalog) -> None:
    tool = _tool(catalog)
    text = (QDF_DIR / "C0048.qdf").read_text(encoding="utf-8")
    counter, _ = tool.process(text)
    total_tubes = sum(cnt for _, cnt in counter.items("tubes"))
    assert total_tubes == 104


@pytest.mark.skipif(not (QDF_DIR / "C0048.qdf").exists(), reason="C0048.qdf not found")
def test_c0048_t35_count(catalog: PartsCatalog) -> None:
    tool = _tool(catalog)
    text = (QDF_DIR / "C0048.qdf").read_text(encoding="utf-8")
    counter, _ = tool.process(text)
    t35_total = sum(cnt for (pid, _), cnt in counter.items("tubes") if pid == "T35")
    assert t35_total == 84   # 20+19+19+26


@pytest.mark.skipif(not (QDF_DIR / "C0048.qdf").exists(), reason="C0048.qdf not found")
def test_c0048_t15_count(catalog: PartsCatalog) -> None:
    tool = _tool(catalog)
    text = (QDF_DIR / "C0048.qdf").read_text(encoding="utf-8")
    counter, _ = tool.process(text)
    t15_total = sum(cnt for (pid, _), cnt in counter.items("tubes") if pid == "T15")
    assert t15_total == 20   # 4+4+4+8


@pytest.mark.skipif(not (QDF_DIR / "C0048.qdf").exists(), reason="C0048.qdf not found")
def test_c0048_diagonal_connectors(catalog: PartsCatalog) -> None:
    tool = _tool(catalog)
    text = (QDF_DIR / "C0048.qdf").read_text(encoding="utf-8")
    counter, _ = tool.process(text)
    c45 = sum(cnt for (pid, _), cnt in counter.items("connectors") if pid == "diagonal")
    assert c45 == 4


@pytest.mark.skipif(not (QDF_DIR / "C0048.qdf").exists(), reason="C0048.qdf not found")
def test_c0048_double_tube(catalog: PartsCatalog) -> None:
    # clamp2 → double_tube (CDT); POC missed these
    tool = _tool(catalog)
    text = (QDF_DIR / "C0048.qdf").read_text(encoding="utf-8")
    counter, _ = tool.process(text)
    cdt = sum(cnt for (pid, _), cnt in counter.items("connectors") if pid == "double_tube")
    assert cdt == 2


@pytest.mark.skipif(not (QDF_DIR / "C0048.qdf").exists(), reason="C0048.qdf not found")
def test_c0048_slides(catalog: PartsCatalog) -> None:
    tool = _tool(catalog)
    text = (QDF_DIR / "C0048.qdf").read_text(encoding="utf-8")
    counter, _ = tool.process(text)
    slide_ids = {pid for (pid, _), _ in counter.items("slides")}
    assert "slide_module" in slide_ids
    assert "slide_end" in slide_ids


@pytest.mark.skipif(not (QDF_DIR / "C0048.qdf").exists(), reason="C0048.qdf not found")
def test_c0048_no_unknowns(catalog: PartsCatalog) -> None:
    tool = _tool(catalog)
    text = (QDF_DIR / "C0048.qdf").read_text(encoding="utf-8")
    counter, _ = tool.process(text)
    unknowns = counter.items("other")
    assert not unknowns, f"Unexpected unknowns in C0048: {unknowns}"


@pytest.mark.skipif(not (QDF_DIR / "C0048.qdf").exists(), reason="C0048.qdf not found")
def test_c0048_report_runs(catalog: PartsCatalog) -> None:
    tool = _tool(catalog)
    report = tool.run_file(QDF_DIR / "C0048.qdf")
    assert "QUADRO-Stückliste" in report
    assert "ROHRE" in report
    assert "KUPPLUNGEN" in report


# ---------------------------------------------------------------------------
# C0145-mod – contains hole panels (material " (hole)" suffix)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not (QDF_DIR / "C0145-mod.qdf").exists(), reason="C0145-mod.qdf not found")
def test_c0145mod_has_hole_panels(catalog: PartsCatalog) -> None:
    tool = _tool(catalog)
    text = (QDF_DIR / "C0145-mod.qdf").read_text(encoding="utf-8")
    counter, _ = tool.process(text)
    panel_ids = {pid for (pid, _), _ in counter.items("panels")}
    assert "hole_panel_40x40" in panel_ids, (
        "C0145-mod should contain at least one hole panel (PO4)"
    )


# ---------------------------------------------------------------------------
# Smoke tests for other QDF files
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fname", ["C0091.qdf", "C0145.qdf"])
def test_smoke(catalog: PartsCatalog, fname: str) -> None:
    path = QDF_DIR / fname
    if not path.exists():
        pytest.skip(f"{fname} not found")
    tool = _tool(catalog)
    counter, _ = tool.process(path.read_text(encoding="utf-8"))
    assert counter.grand_total() > 0
