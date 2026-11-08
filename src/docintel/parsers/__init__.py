from __future__ import annotations

from pathlib import Path

from .base import ParsedDoc


def parse_pdf(parser: str, pdf: Path) -> ParsedDoc:
    if parser == "pymupdf":
        from .pymupdf_parser import parse
    elif parser == "docling":
        from .docling_parser import parse
    else:
        raise ValueError(f"Unknown text parser {parser!r}. Use pymupdf | docling (or gemini_direct for the multimodal arm).")
    return parse(pdf)
