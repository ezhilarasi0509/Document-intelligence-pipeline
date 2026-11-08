"""'Retrieval-lite': choose which parts of a long contract to send to a size-limited LLM (stdlib only).

Free LLM tiers cap tokens per minute, and contracts can be 50k+ tokens. So we send:
  1) the opening of the contract (title, parties, dates live here), and
  2) the paragraphs whose keywords best match our fields.
This is also a real cost lever: fewer input tokens = cheaper at scale.
"""
from __future__ import annotations

import re

from .config import HEAD_CHARS, MAX_CONTEXT_CHARS
from .fields import FIELDS

ALL_KEYWORDS = sorted({k for f in FIELDS for k in f.keywords}, key=len, reverse=True)


def split_paragraphs(text: str, max_len: int = 1500) -> list[tuple[int, str]]:
    """Return [(start_offset, paragraph)]. Very long paragraphs are cut at sentence boundaries."""
    out: list[tuple[int, str]] = []
    pos = 0
    for block in re.split(r"\n\s*\n", text):
        start = text.find(block, pos) if block else pos
        if start < 0:
            start = pos
        pos = start + len(block)
        block = block.strip()
        if not block:
            continue
        if len(block) <= max_len:
            out.append((start, block))
            continue
        cur, cur_start = "", start
        for sent in re.split(r"(?<=[.;:])\s+", block):
            if len(cur) + len(sent) > max_len and cur:
                out.append((cur_start, cur))
                cur, cur_start = "", cur_start + len(cur)
            cur += (" " if cur else "") + sent
        if cur:
            out.append((cur_start, cur))
    return out


def score(par: str) -> int:
    low = par.lower()
    return sum(low.count(k) for k in ALL_KEYWORDS)


def build_context(text: str, max_chars: int = MAX_CONTEXT_CHARS, head_chars: int = HEAD_CHARS) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    head = text[:head_chars]
    budget = max_chars - len(head)
    paras = [(i, s, p) for i, (s, p) in enumerate(split_paragraphs(text)) if s >= head_chars]
    ranked = sorted(paras, key=lambda t: score(t[2]), reverse=True)
    chosen, used = [], 0
    for i, s, p in ranked:
        if score(p) == 0:
            break
        if used + len(p) + 2 > budget:
            continue
        chosen.append((s, p))
        used += len(p) + 2
    chosen.sort()
    body = "\n\n".join(p for _, p in chosen)
    return f"{head}\n\n[... relevant excerpts ...]\n\n{body}" if body else head
