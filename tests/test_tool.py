"""Tests for BomTool and main() CLI."""

from pathlib import Path

import pytest

from qdf_bom.tool import main

# Minimal valid QDF — one material + one tube
_MINIMAL_QDF = """\
0, 0;
material3{1,"black", 1, 1.,1.,1., 0.,0.,1.,7.5, 0.,0.,0.,7.5, "", 0}
tube2{1, {2., 0., 0., 2., 800., 0., 0.}, 1, 350., 0., 0}
"""


# ---------------------------------------------------------------------------
# main() argument handling
# ---------------------------------------------------------------------------

def test_main_no_args() -> None:
    assert main([]) == 2


def test_main_file_not_found(capsys: pytest.CaptureFixture) -> None:
    rc = main(["nonexistent_file_xyz.qdf"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "nicht gefunden" in captured.err


def test_main_valid_file(tmp_path: Path) -> None:
    qdf = tmp_path / "test.qdf"
    qdf.write_text(_MINIMAL_QDF, encoding="utf-8")

    rc = main([str(qdf)])

    assert rc == 0
    txt = tmp_path / "test_partslist.txt"
    assert txt.exists(), "Expected .txt output file to be created"
    content = txt.read_text(encoding="utf-8")
    assert "QUADRO-Stückliste" in content


def test_main_multiple_files(tmp_path: Path) -> None:
    for name in ("a.qdf", "b.qdf"):
        (tmp_path / name).write_text(_MINIMAL_QDF, encoding="utf-8")

    rc = main([str(tmp_path / "a.qdf"), str(tmp_path / "b.qdf")])

    assert rc == 0
    assert (tmp_path / "a_partslist.txt").exists()
    assert (tmp_path / "b_partslist.txt").exists()
