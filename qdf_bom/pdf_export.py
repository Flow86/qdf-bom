"""PDF export for BOM reports."""

from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

_LINE_HEIGHT_MM = 4   # ≈ 10 pt + minimal Durchschuss
_MARGIN_MM = 15


def save_pdf(report_text: str, path: Path) -> None:
    """Write *report_text* as a monospaced PDF to *path*."""
    pdf = FPDF()
    pdf.set_margins(_MARGIN_MM, _MARGIN_MM, _MARGIN_MM)
    pdf.set_auto_page_break(auto=True, margin=_MARGIN_MM)
    pdf.add_page()
    pdf.set_font("Courier", size=10)
    for line in report_text.splitlines():
        pdf.cell(0, _LINE_HEIGHT_MM, text=line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.output(str(path))
