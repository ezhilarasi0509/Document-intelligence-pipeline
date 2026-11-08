"""Parser A: plain text-layer extraction. Fastest and cheapest; blind to layout, tables, scans."""
from __future__ import annotations

from pathlib import Path

from .base import ParsedDoc, parse_cached


def _parse(pdf: Path) -> tuple[str, int]:
    import pymupdf as fitz  # PyMuPDF

    with fitz.open(pdf) as doc:
        pages = [p.get_text("text") for p in doc]
    return "\n\n".join(pages), len(pages)


def parse(pdf: Path) -> ParsedDoc:
    return parse_cached("pymupdf", _parse, pdf)
