"""Run one experiment: (parser x model) over the sampled contracts. Results are cached per document,
so a crash or rate-limit never costs you the work already done. Use --force to redo."""
from __future__ import annotations

import json
import time

from tqdm import tqdm

from . import config, store
from .costs import estimate_cost
from .extract import ExtractionResult, extract_from_text, result_to_json
from .parsers import parse_pdf
from .tracing import init_tracing


def run(parser: str, run_id: str, limit: int | None = None, force: bool = False) -> dict:
    init_tracing()
    if not config.MANIFEST.exists():
        raise SystemExit("No data yet. Run: uv run docintel download")
    stems = json.loads(config.MANIFEST.read_text())
    if limit:
        stems = stems[:limit]
    out_dir = config.PRED_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    model = config.GEMINI_MODEL if parser in ("gemini_direct", "gemini_snippets") else config.GROQ_MODEL

    results: list[ExtractionResult] = []
    fail_streak = 0
    for s in tqdm(stems, desc=run_id):
        cache = out_dir / f"{s}.json"
        if cache.exists() and not force:
            results.append(ExtractionResult(**json.loads(cache.read_text())))
            continue
        pdf = config.PDF_DIR / f"{s}.pdf"
        crashed = False
        try:
            if parser == "gemini_direct":
                from .gemini_direct import extract_pdf
                res = extract_pdf(pdf)
            elif parser == "gemini_snippets":
                from .gemini_direct import extract_text
                parsed = parse_pdf("pymupdf", pdf)
                res = extract_text(parsed.text, s)
                res.parse_seconds = parsed.seconds
            else:
                parsed = parse_pdf(parser, pdf)
                res = extract_from_text(parsed.text, s)
                res.parse_seconds = parsed.seconds
        except Exception as e:  # one bad document must not kill the whole run
            print(f"\n[run] {s}: {str(e)[:200]}")
            res, crashed = ExtractionResult(filename=s, error=str(e)[:300]), True
        res.filename = s
        if not crashed and res.ok:  # failed docs are not cached, so the next run retries them
            cache.write_text(result_to_json(res))
        results.append(res)
        fail_streak = 0 if res.ok else fail_streak + 1
        if fail_streak >= 3:
            print(f"\n[run] 3 failures in a row (last error: {res.error}). Quota or outage - stopping.\n"
                  "      Finished documents are saved; re-run the same command later to resume.")
            break
        time.sleep(config.REQUEST_DELAY_S)

    pt = sum(r.prompt_tokens for r in results)
    ct = sum(r.completion_tokens for r in results)
    meta = dict(
        run_id=run_id, parser=parser, model=model, n_docs=len(results),
        ok_docs=sum(r.ok for r in results), retry_docs=sum(r.attempts > 1 for r in results),
        parse_seconds=sum(r.parse_seconds for r in results), llm_seconds=sum(r.seconds for r in results),
        prompt_tokens=pt, completion_tokens=ct, est_cost_usd=estimate_cost(model, pt, ct))
    (out_dir / "_run.json").write_text(json.dumps(meta, indent=2))
    store.save_run(meta, results)
    print(f"\n{run_id}: {meta['ok_docs']}/{meta['n_docs']} valid, {meta['retry_docs']} needed retries, "
          f"{pt:,} prompt tokens, hypothetical cost ${meta['est_cost_usd']:.4f}")
    return meta
