from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from ..config import PARSED_DIR


@dataclass
class ParsedDoc:
    text: str
    seconds: float
    pages: int = 0


def parse_cached(parser_name: str, parse_fn, pdf: Path) -> ParsedDoc:
    """Parse once, reuse forever. Parsing time is stored so cost tables stay honest on cached runs."""
    out_dir = PARSED_DIR / parser_name
    out_dir.mkdir(parents=True, exist_ok=True)
    txt, meta = out_dir / f"{pdf.stem}.txt", out_dir / f"{pdf.stem}.json"
    if txt.exists() and meta.exists():
        m = json.loads(meta.read_text())
        return ParsedDoc(txt.read_text(encoding="utf-8"), m["seconds"], m.get("pages", 0))
    t0 = time.perf_counter()
    text, pages = parse_fn(pdf)
    secs = time.perf_counter() - t0
    txt.write_text(text, encoding="utf-8")
    meta.write_text(json.dumps({"seconds": secs, "pages": pages}))
    return ParsedDoc(text, secs, pages)
