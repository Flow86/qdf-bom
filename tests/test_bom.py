"""Tests for BomCounter and BomReport."""

import pytest
from qdf_bom.bom import BomCounter, BomReport
from qdf_bom.catalog import PartsCatalog


def test_counter_add_and_grand_total() -> None:
    c = BomCounter()
    c.add("tubes", "T35", 2, count=3)
    c.add("tubes", "T35", 3, count=1)
    c.add("connectors", "3way", 1)
    assert c.grand_total() == 5


def test_counter_items_sorted() -> None:
    c = BomCounter()
    c.add("tubes", "T35", 3)
    c.add("tubes", "T15", 2)
    c.add("tubes", "T35", 2)
    items = c.items("tubes")
    keys = [k for k, _ in items]
    assert keys == sorted(keys)


def test_counter_unknown() -> None:
    c = BomCounter()
    c.add_unknown("wood2", 1)
    c.add_unknown("wood2", 1)
    items = c.items("other")
    assert len(items) == 1
    assert items[0][1] == 2


def test_report_contains_filename(catalog: PartsCatalog) -> None:
    c = BomCounter()
    c.add("tubes", "T35", 2)
    report = BomReport(catalog).render(c, "test.qdf", {2: "red"})
    assert "test.qdf" in report


def test_report_contains_link(catalog: PartsCatalog) -> None:
    c = BomCounter()
    c.add("tubes", "T35", 2)
    report = BomReport(catalog).render(c, "C0048.qdf", {2: "red"})
    assert "https://quadroworld.com/de/designs/C0048" in report


def test_report_total(catalog: PartsCatalog) -> None:
    c = BomCounter()
    c.add("tubes", "T35", 2, count=5)
    c.add("connectors", "3way", 1, count=3)
    report = BomReport(catalog).render(c, "x.qdf", {1: "black", 2: "red"})
    assert "GESAMT: 8" in report


def test_report_empty_category_omitted(catalog: PartsCatalog) -> None:
    c = BomCounter()
    c.add("tubes", "T35", 2)
    report = BomReport(catalog).render(c, "x.qdf", {2: "red"})
    assert "PLATTEN" not in report
    assert "ROHRE" in report


def test_report_sonstige_for_unknown(catalog: PartsCatalog) -> None:
    c = BomCounter()
    c.add_unknown("wood2", 1)
    report = BomReport(catalog).render(c, "x.qdf", {1: "black"})
    assert "SONSTIGE" in report
    assert "wood2" in report


def test_report_color_resolved(catalog: PartsCatalog) -> None:
    c = BomCounter()
    c.add("connectors", "3way", 1)
    report = BomReport(catalog).render(c, "x.qdf", {1: "black"})
    assert "Schwarz" in report


def test_report_hole_material_color(catalog: PartsCatalog) -> None:
    # Color name for hole material should strip the " (hole)" suffix
    c = BomCounter()
    c.add("panels", "hole_panel_40x40", 15)
    report = BomReport(catalog).render(c, "x.qdf", {15: "red (hole)"})
    assert "Rot" in report
    assert "(hole)" not in report
