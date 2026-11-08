"""Score a run against CUAD labels: precision/recall/F1 per field and per field type + an error log."""
from __future__ import annotations

import csv
import json

from . import config, store
from .fields import FIELDS, FieldType
from .labels import load_gold
from .metrics import aggregate, outcome


def _pred_value(spec, rec: dict | None):
    if spec.ftype is FieldType.CLAUSE:
        return bool(rec and rec[spec.key]["present"])
    if rec is None:
        return [] if spec.key == "parties" else None
    return rec.get(spec.key)


def evaluate(run_id: str) -> list[dict]:
    run_dir = config.PRED_DIR / run_id
    files = sorted(p for p in run_dir.glob("*.json") if not p.name.startswith("_"))
    if not files:
        raise SystemExit(f"No predictions in {run_dir}. Run `docintel run` first.")
    gold = load_gold()
    outcomes, errors = [], []
    scored = 0
    for f in files:
        res = json.loads(f.read_text())
        g = gold.get(f.stem)
        if g is None:
            continue
        scored += 1
        rec = res["record"] if res.get("ok") else None  # failed docs count against recall (honest)
        for spec in FIELDS:
            pred, truth = _pred_value(spec, rec), g[spec.key]
            o = outcome(spec, pred, truth)
            outcomes.append((spec.key, o))
            if o in ("FP", "FN", "FPFN"):
                errors.append(dict(doc=f.stem, field=spec.key, ftype=spec.ftype.value, kind=o,
                                   predicted=pred, gold=truth, doc_failed_validation=rec is None))
    rows = aggregate(outcomes)
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.REPORTS_DIR / f"{run_id}_metrics.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    with open(config.REPORTS_DIR / f"{run_id}_errors.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["doc", "field", "ftype", "kind", "predicted", "gold", "doc_failed_validation"])
        w.writeheader(); w.writerows(errors)
    store.save_metrics(run_id, rows)

    print(f"\nRun {run_id}: scored {scored} documents\n")
    print(f"{'level':<6}{'field/type':<30}{'type':<8}{'P':>6}{'R':>6}{'F1':>6}{'support':>8}")
    for r in rows:
        print(f"{r['level']:<6}{r['name']:<30}{r['ftype']:<8}{r['precision']:>6.2f}{r['recall']:>6.2f}{r['f1']:>6.2f}{r['support']:>8}")
    print(f"\nError log: reports/{run_id}_errors.csv  ({len(errors)} rows)")
    return rows
