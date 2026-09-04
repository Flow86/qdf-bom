"""Tests for ConnectorClassifier."""

import pytest
from qdf_bom.classifier import ConnectorClassifier
from qdf_bom.catalog import PartsCatalog


@pytest.fixture
def classifier(catalog: PartsCatalog) -> ConnectorClassifier:
    return ConnectorClassifier(catalog)


def test_6way(classifier: ConnectorClassifier) -> None:
    # All 6 cardinal bits set → 6-way space connector
    mask = 0b111111  # bits 0-5
    assert classifier.classify(mask) == "6way"


def test_5way(classifier: ConnectorClassifier) -> None:
    # 5 cardinal bits → 5-way space connector
    mask = 0b011111  # bits 0-4
    assert classifier.classify(mask) == "5way"


def test_4way_space(classifier: ConnectorClassifier) -> None:
    # +X, -X, +Y, +Z → 4-way space connector
    mask = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 4)
    assert classifier.classify(mask) == "4way"


def test_3way_space(classifier: ConnectorClassifier) -> None:
    # +X, +Y, +Z → 3-way space connector
    mask = (1 << 0) | (1 << 2) | (1 << 4)
    assert classifier.classify(mask) == "3way"


def test_cross_planar(classifier: ConnectorClassifier) -> None:
    # +X, -X, +Y, -Y → 4-way cross (planar)
    mask = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 3)
    assert classifier.classify(mask) == "cross"


def test_t_planar(classifier: ConnectorClassifier) -> None:
    # +X, +Y, -Y → 3-way T-piece (planar)
    mask = (1 << 0) | (1 << 2) | (1 << 3)
    assert classifier.classify(mask) == "t"


def test_straight_180(classifier: ConnectorClassifier) -> None:
    # +X, -X → straight (180°)
    mask = (1 << 0) | (1 << 1)
    assert classifier.classify(mask) == "straight"


def test_elbow_90(classifier: ConnectorClassifier) -> None:
    # +X, +Y → elbow (90°)
    mask = (1 << 0) | (1 << 2)
    assert classifier.classify(mask) == "elbow"


def test_zero_mask_unknown(classifier: ConnectorClassifier) -> None:
    assert classifier.classify(0) == "connector_unknown"
