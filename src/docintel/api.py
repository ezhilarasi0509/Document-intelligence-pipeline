"""FastAPI service: upload a contract PDF, get validated JSON back. Run: uv run docintel serve"""
from __future__ import annotations

import json
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from . import config, store
from .extract import extract_from_text
from .parsers.pymupdf_parser import _parse as parse_pdf_text
from .schema import ContractExtraction
from .tracing import init_tracing

init_tracing("docintel-api")
app = FastAPI(title="Contract Document Intelligence", version="0.1.0",
              description="Messy contract PDF in, schema-validated JSON out.")


class ExtractResponse(BaseModel):
    id: str
    filename: str
    ok: bool
    attempts: int
    error: str | None = None
    record: ContractExtraction | None = None
    ungrounded_quotes: list[str] = []


@app.get("/health")
def health():
    return {"status": "ok", "model": config.GROQ_MODEL}


@app.post("/extract", response_model=ExtractResponse)
async def extract(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Please upload a .pdf file")
    data = await file.read()
    if len(data) > config.MAX_PDF_MB * 1_000_000:
        raise HTTPException(413, f"PDF larger than {config.MAX_PDF_MB} MB")
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        tmp.write(data); tmp.flush()
        try:
            text, _pages = parse_pdf_text(Path(tmp.name))
        except Exception as e:  # noqa: BLE001
            raise HTTPException(422, f"Could not read PDF: {e}") from e
    if len(text.strip()) < 200:
        raise HTTPException(422, "No text layer found (scanned PDF?). Use the Docling/Gemini arms offline.")
    try:
        res = extract_from_text(text, file.filename or "upload.pdf")
    except RuntimeError as e:
        raise HTTPException(503, str(e)) from e
    id_ = uuid.uuid4().hex[:12]
    store.save_api_extraction(id_, res.filename, res.ok, res.record, res.error)
    return ExtractResponse(id=id_, filename=res.filename, ok=res.ok, attempts=res.attempts,
                           error=res.error, record=res.record, ungrounded_quotes=res.ungrounded)


@app.get("/documents")
def documents(limit: int = 50):
    return store.query("SELECT id, filename, created_at, ok FROM api_extractions ORDER BY created_at DESC LIMIT ?",
                       [min(limit, 200)])


@app.get("/documents/{doc_id}")
def document(doc_id: str):
    rows = store.query("SELECT * FROM api_extractions WHERE id = ?", [doc_id])
    if not rows:
        raise HTTPException(404, "Not found")
    row = rows[0]
    row["record"] = json.loads(row["record"]) if row["record"] else None
    return row


@app.get("/stats/clauses")
def clause_stats():
    """Share of API-uploaded contracts containing each clause (analytics straight from DuckDB)."""
    rows = store.query("SELECT record FROM api_extractions WHERE ok")
    recs = [json.loads(r["record"]) for r in rows]
    out = {}
    for key in ("non_compete", "exclusivity", "anti_assignment", "cap_on_liability", "termination_for_convenience"):
        out[key] = round(sum(r[key]["present"] for r in recs) / len(recs), 3) if recs else None
    return {"n_documents": len(recs), "clause_rates": out}


@app.get("/metrics/{run_id}")
def metrics(run_id: str):
    rows = store.query("SELECT level, name, ftype, precision, recall, f1, support FROM metrics WHERE run_id = ? "
                       "ORDER BY level DESC, ftype, name", [run_id])
    if not rows:
        raise HTTPException(404, "No metrics for that run (run `docintel evaluate` first)")
    return rows
