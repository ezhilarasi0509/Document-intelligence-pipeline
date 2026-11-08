# Learning guide: Nov 4 - Nov 17

Rule: after each day, answer the "can you explain" questions out loud without looking. That is your interview prep.

| Day | Do | Concepts | Can you explain... |
|---|---|---|---|
| Nov 4 | Setup (`uv sync`, keys), read `fields.py`, `schema.py`, run `pytest` | virtualenvs, uv, Pydantic models | Why one field registry instead of scattered strings? |
| Nov 5 | `download`, `inspect-labels`, open the CSV in DuckDB | dataset curation, seeded sampling, label semantics | Why 40 docs and 12 fields? What does CUAD's "-Answer" column hold? |
| Nov 6 | Run PyMuPDF parser, open 3 parsed files | text layers vs scans, layout loss | What does PyMuPDF lose that a layout parser keeps? |
| Nov 7 | Add Docling (`--extra docling`), compare same 3 docs | layout-aware parsing, OCR cost | When is OCR worth its cost? |
| Nov 8 | Read `context.py`, run `--limit 5` extraction | token limits, retrieval-lite, prompts | Why not send the whole contract? What breaks? |
| Nov 9 | Force failures: lower retries, break a date, read validation errors | structured outputs, validate-and-retry | Schema-constrained decoding vs Pydantic validation: difference? |
| Nov 10 | Full run + `evaluate` | precision, recall, F1, micro vs macro | Why does a wrong date count as FP *and* FN? |
| Nov 11 | Open `reports/*_errors.csv`, categorize 30 errors by hand | error analysis | Which field types fail most, and why? |
| Nov 12 | Gemini multimodal arm + `report` | multimodal vs OCR+LLM trade-offs | Which arm wins on F1 per dollar-equivalent? |
| Nov 13 | DuckDB SQL on `clause_flags`, `metrics`; FastAPI `/extract` | analytics store, REST design | Why DuckDB not Postgres here? |
| Nov 14 | Phoenix tracing, Docker build | observability, containers | What can a trace tell you that logs cannot? |
| Nov 15 | Deploy to Spaces | secrets, ports, ephemeral storage | What breaks on a free tier in production? |
| Nov 16-17 | Write results into README: tables, 3 failure examples, limits | communicating results | 60-second pitch of the project |

## Starter DuckDB queries
```sql
-- which clauses does the model flag most often?
SELECT field, avg(present::INT) AS rate FROM clause_flags WHERE run_id='pymupdf_groq' GROUP BY 1 ORDER BY 2 DESC;
-- worst fields
SELECT name, f1, support FROM metrics WHERE run_id='pymupdf_groq' AND level='field' ORDER BY f1;
-- how many docs needed retries?
SELECT attempts, count(*) FROM extractions WHERE run_id='pymupdf_groq' GROUP BY 1;
```
Run with: `uv run python -c "from docintel import store; print(store.query(\"SQL HERE\"))"`.

## Stretch goals that make it 10/10
1. Ablation: full-context vs retrieval-lite on 10 docs (does recall drop?).
2. Failure taxonomy: label every error as parser / retrieval / model / label-noise. Report counts.
3. Confidence check: does `ungrounded` correlate with wrong answers?
4. Hold-out set: tune prompts on 20 docs, report final numbers only on the other 20.
5. GitHub Actions: run `pytest` on every push.
6. Scale math: extrapolate "cost per 100k contracts" per arm with real token counts.
