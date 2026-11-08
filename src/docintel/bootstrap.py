"""Bootstrap 95% confidence intervals for clause F1 by resampling DOCUMENTS (stdlib only).

Usage: uv run python -m docintel.bootstrap --runs pymupdf_groq_v2 gemini_full
The first run is the baseline: every other run is compared to it with a paired bootstrap
(the same resampled documents are used for every run, so the difference is meaningful).
"""
from __future__ import annotations

import argparse
import random

from . import config
from .compare import _load, _pred
from .fields import FIELDS, FieldType
from .labels import load_gold
from .metrics import outcome, prf


def _doc_counts(rec: dict, gold: dict) -> tuple[int, int, int]:
    tp = fp = fn = 0
    for s in FIELDS:
        if s.ftype is not FieldType.CLAUSE:
            continue
        o = outcome(s, _pred(s, rec), gold[s.key])
        tp += o == "TP"
        fp += o == "FP"
        fn += o == "FN"
    return tp, fp, fn


def _f1(rows: list[tuple[int, int, int]], idx: list[int]) -> float:
    tp = sum(rows[i][0] for i in idx)
    fp = sum(rows[i][1] for i in idx)
    fn = sum(rows[i][2] for i in idx)
    return prf(tp, fp, fn)[2]


def _ci(values: list[float]) -> tuple[float, float]:
    v = sorted(values)
    return v[int(0.025 * len(v))], v[min(int(0.975 * len(v)), len(v) - 1)]


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--n", type=int, default=5000, help="bootstrap resamples")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args(argv)

    runs = {r: _load(r) for r in a.runs}
    gold = load_gold()
    common = sorted(set.intersection(*(set(v) for v in runs.values())) & set(gold))
    if len(common) < 5:
        raise SystemExit(f"Only {len(common)} documents finished by every run; need at least 5.")
    per = {r: [_doc_counts(runs[r][d], gold[d]) for d in common] for r in a.runs}
    n = len(common)
    rng = random.Random(a.seed)
    boots: dict[str, list[float]] = {r: [] for r in a.runs}
    for _ in range(a.n):
        idx = [rng.randrange(n) for _ in range(n)]
        for r in a.runs:
            boots[r].append(_f1(per[r], idx))

    base = a.runs[0]
    lines = [f"# Clause F1 with 95% bootstrap confidence intervals ({n} documents, {a.n} resamples)\n",
             "| run | clause F1 | 95% CI |", "|---|---|---|"]
    for r in a.runs:
        point = _f1(per[r], list(range(n)))
        lo, hi = _ci(boots[r])
        lines.append(f"| {r} | {point:.2f} | {lo:.2f} to {hi:.2f} |")
    lines += ["", f"## Paired difference vs `{base}`\n", "| run | F1 difference | 95% CI | share of resamples where it is better |",
              "|---|---|---|---|"]
    for r in a.runs[1:]:
        diffs = [x - y for x, y in zip(boots[r], boots[base])]
        lo, hi = _ci(diffs)
        point = _f1(per[r], list(range(n))) - _f1(per[base], list(range(n)))
        better = sum(d > 0 for d in diffs) / len(diffs)
        lines.append(f"| {r} | {point:+.2f} | {lo:+.2f} to {hi:+.2f} | {better:.1%} |")
    lines += ["", "A difference is reliable when its whole interval is on one side of zero."]
    text = "\n".join(lines) + "\n"
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (config.REPORTS_DIR / "bootstrap_ci.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
