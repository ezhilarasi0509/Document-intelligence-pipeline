"""Fair comparison: score several runs on exactly the documents ALL of them finished successfully."""
from __future__ import annotations

import json

from . import config
from .fields import FIELDS, FieldType
from .labels import load_gold
from .metrics import aggregate, outcome


def _load(run_id: str) -> dict[str, dict]:
    d = config.PRED_DIR / run_id
    if not d.exists():
        raise SystemExit(f"No predictions for run {run_id!r} in {d}")
    out = {}
    for f in d.glob("*.json"):
        if f.name.startswith("_"):
            continue
        r = json.loads(f.read_text())
        if r.get("ok") and r.get("record"):
            out[f.stem] = r["record"]
    return out


def _pred(spec, rec):
    if spec.ftype is FieldType.CLAUSE:
        return bool(rec[spec.key]["present"])
    return rec.get(spec.key)


def compare(run_ids: list[str]) -> str:
    runs = {r: _load(r) for r in run_ids}
    gold = load_gold()
    common = sorted(set.intersection(*(set(v) for v in runs.values())) & set(gold))
    if not common:
        raise SystemExit("No documents were finished by all of these runs.")
    rows = {}
    for rid, recs in runs.items():
        outs = [(s.key, outcome(s, _pred(s, recs[d]), gold[d][s.key])) for d in common for s in FIELDS]
        rows[rid] = aggregate(outs)

    def get(rid, level, name):
        return next(r for r in rows[rid] if r["level"] == level and r["name"] == name)

    md = [f"# Same-documents comparison ({len(common)} documents finished by every run)\n"]
    md.append("Small samples are noisy: treat differences under ~0.10 F1 as inconclusive.\n")
    md.append("## By field type (precision / recall / F1)\n")
    md.append("| type | " + " | ".join(run_ids) + " |")
    md.append("|---|" + "---|" * len(run_ids))
    for t in ("entity", "date", "clause"):
        cells = []
        for rid in run_ids:
            r = get(rid, "type", t)
            cells.append(f"{r['precision']:.2f} / {r['recall']:.2f} / **{r['f1']:.2f}**")
        md.append(f"| {t} | " + " | ".join(cells) + " |")
    md.append("\n## F1 per field\n")
    md.append("| field | support | " + " | ".join(run_ids) + " |")
    md.append("|---|---|" + "---|" * len(run_ids))
    for s in FIELDS:
        sup = get(run_ids[0], "field", s.key)["support"]
        md.append(f"| {s.key} | {sup} | " + " | ".join(f"{get(r, 'field', s.key)['f1']:.2f}" for r in run_ids) + " |")
    text = "\n".join(md) + "\n"
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (config.REPORTS_DIR / "same_docs_comparison.md").write_text(text)
    print(text)
    return text
