"""Build reports/comparison.md: accuracy by field type, per-field F1, and the performance-vs-cost table."""
from __future__ import annotations

from . import config, store


def _table(headers: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def build() -> str:
    runs = store.query("SELECT * FROM runs ORDER BY created_at")
    if not runs:
        raise SystemExit("No runs in DuckDB yet. Run `docintel run ...` then `docintel evaluate ...`.")
    metrics = store.query("SELECT * FROM metrics")
    by = {(m["run_id"], m["level"], m["name"]): m for m in metrics}
    ids = [r["run_id"] for r in runs]

    def f1(run, level, name):
        m = by.get((run, level, name))
        return f"{m['f1']:.2f}" if m else "-"

    md = ["# Comparison of runs\n"]
    md.append("## 1. Accuracy by field type (micro-averaged F1)\n")
    md.append(_table(["run", "entity", "date", "clause"],
                     [[i, f1(i, "type", "entity"), f1(i, "type", "date"), f1(i, "type", "clause")] for i in ids]))
    md.append("\n## 2. F1 per field\n")
    fields = sorted({m["name"] for m in metrics if m["level"] == "field"})
    md.append(_table(["field"] + ids, [[fn] + [f1(i, "field", fn) for i in ids] for fn in fields]))
    md.append("\n## 3. Performance vs cost\n")
    md.append("Cost is *hypothetical paid pricing* (edit `PRICES_PER_M` in config.py); free tiers cost $0.\n")
    rows = []
    for r in runs:
        n = max(r["n_docs"], 1)
        total = (r["parse_seconds"] or 0) + (r["llm_seconds"] or 0)
        rows.append([r["run_id"], r["parser"], r["model"], f"{r['ok_docs']}/{r['n_docs']}", r["retry_docs"],
                     f"{(r['parse_seconds'] or 0) / n:.2f}", f"{(r['llm_seconds'] or 0) / n:.2f}",
                     f"{((r['prompt_tokens'] or 0) + (r['completion_tokens'] or 0)) / n:,.0f}",
                     f"${r['est_cost_usd'] / n * 1000:.2f}", f"{total / n:.2f}"])
    md.append(_table(["run", "parser", "model", "valid", "retried", "parse s/doc", "LLM s/doc",
                      "tokens/doc", "est $ per 1k docs", "total s/doc"], rows))
    text = "\n".join(md) + "\n"
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (config.REPORTS_DIR / "comparison.md").write_text(text)
    print(text)
    return text
