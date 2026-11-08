"""Parser B: Docling, layout-aware (reading order, tables, headings) -> Markdown.

Optional install: `uv sync --extra docling` (downloads sizeable models; do this last, check disk first).
OCR is OFF by default (CUAD PDFs are mostly digital). Set DOCLING_OCR=1 to turn it on and compare.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from .base import ParsedDoc, parse_cached


@lru_cache(maxsize=1)
def _converter():
    try:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption
    except ImportError as e:  # pragma: no cover
        raise SystemExit("Docling is not installed. Run: uv sync --extra docling") from e
    opts = PdfPipelineOptions()
    opts.do_ocr = os.getenv("DOCLING_OCR", "0") == "1"
    if opts.do_ocr:  # OCR-style arm: rasterize and OCR every page, ignoring the PDF text layer
        try:
            from docling.datamodel.pipeline_options import OcrAutoOptions as _Ocr
        except ImportError:
            from docling.datamodel.pipeline_options import EasyOcrOptions as _Ocr
        opts.ocr_options = _Ocr(force_full_page_ocr=True)
    return DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})


def _parse(pdf: Path) -> tuple[str, int]:
    res = _converter().convert(str(pdf))
    pages = len(getattr(res.document, "pages", {}) or {})
    return res.document.export_to_markdown(), pages


def parse(pdf: Path) -> ParsedDoc:
    name = "docling_ocr" if os.getenv("DOCLING_OCR", "0") == "1" else "docling"
    return parse_cached(name, _parse, pdf)
