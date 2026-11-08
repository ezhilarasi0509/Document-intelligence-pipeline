"""Scoring: precision / recall / F1 per field, broken down by field type (stdlib only).

Per (document, field) we produce one outcome:
  TP: model said something AND it matches the label
  FP: model said something that is wrong (or there was no label)
  FN: the label exists but the model said nothing or something wrong
  TN: both say 'nothing'
A wrong non-null answer counts as FP *and* FN - it is both a bad claim and a miss.
"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import date, datetime

from .fields import FIELD_BY_KEY, FieldSpec, FieldType

STOP = {
    "the", "of", "a", "an", "and", "state", "commonwealth", "laws", "law", "province",
    "inc", "llc", "corp", "corporation", "co", "ltd", "company", "limited", "incorporated",
}
_DATE_FORMATS = (
    "%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%B %d, %Y", "%b %d, %Y",
    "%B %d %Y", "%d %B %Y", "%Y/%m/%d", "%b. %d, %Y",
)


def tokens(s: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", s.lower()) if t not in STOP}


def text_match(pred: str, gold: str, threshold: float, allow_containment: bool = True) -> bool:
    p, g = tokens(pred), tokens(gold)
    if not p or not g:
        return False
    if allow_containment and (p <= g or g <= p):
        return True
    inter = len(p & g)
    if inter == 0:
        return False
    prec, rec = inter / len(p), inter / len(g)
    return 2 * prec * rec / (prec + rec) >= threshold


def parse_date(s: str) -> date | None:
    s = re.sub(r"\s+", " ", s.strip())
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def date_match(pred: str, gold: str) -> bool:
    pd_, gd = parse_date(pred), parse_date(gold)
    if pd_ and gd:
        return pd_ == gd
    return text_match(pred, gold, threshold=0.8)  # gold like "perpetual" is not a date


def _present(v) -> bool:
    if isinstance(v, (list, tuple)):
        v = ", ".join(str(x) for x in v)
    return v is not None and str(v).strip() != ""


def outcome(spec: FieldSpec, pred, gold) -> str:
    """Return one of TP/FP/FN/TN."""
    if spec.ftype is FieldType.CLAUSE:
        p, g = bool(pred), bool(gold)
        return "TP" if p and g else "FP" if p else "FN" if g else "TN"
    p_has, g_has = _present(pred), _present(gold)
    if not p_has and not g_has:
        return "TN"
    if p_has and not g_has:
        return "FP"
    if g_has and not p_has:
        return "FN"
    if isinstance(pred, (list, tuple)):
        pred = ", ".join(str(x) for x in pred)
    ok = (date_match(str(pred), str(gold)) if spec.ftype is FieldType.DATE
          else text_match(str(pred), str(gold), spec.match_threshold, spec.allow_containment))
    return "TP" if ok else "FPFN"


def prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def aggregate(outcomes: list[tuple[str, str]]) -> list[dict]:
    """outcomes: [(field_key, 'TP'|'FP'|'FN'|'TN'|'FPFN')] -> per-field rows + per-type rows (micro-averaged)."""
    counts: dict[str, dict[str, int]] = defaultdict(lambda: dict(tp=0, fp=0, fn=0, tn=0))
    for key, o in outcomes:
        c = counts[key]
        if o == "TP": c["tp"] += 1
        elif o == "FP": c["fp"] += 1
        elif o == "FN": c["fn"] += 1
        elif o == "TN": c["tn"] += 1
        elif o == "FPFN": c["fp"] += 1; c["fn"] += 1
    rows, by_type = [], defaultdict(lambda: dict(tp=0, fp=0, fn=0, tn=0))
    for key, c in counts.items():
        spec = FIELD_BY_KEY[key]
        p, r, f = prf(c["tp"], c["fp"], c["fn"])
        rows.append(dict(level="field", name=key, ftype=spec.ftype.value, **c,
                         precision=p, recall=r, f1=f, support=c["tp"] + c["fn"]))
        for k in c:
            by_type[spec.ftype.value][k] += c[k]
    for t, c in by_type.items():
        p, r, f = prf(c["tp"], c["fp"], c["fn"])
        rows.append(dict(level="type", name=t, ftype=t, **c,
                         precision=p, recall=r, f1=f, support=c["tp"] + c["fn"]))
    return sorted(rows, key=lambda x: (x["level"] != "type", x["ftype"], x["name"]))
