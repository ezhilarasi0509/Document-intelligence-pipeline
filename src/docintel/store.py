"""DuckDB analytics store: runs, per-document extractions, flattened clause flags, metrics."""
from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime, timezone

import duckdb

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  run_id VARCHAR PRIMARY KEY, parser VARCHAR, model VARCHAR, created_at TIMESTAMP,
  n_docs INTEGER, ok_docs INTEGER, retry_docs INTEGER,
  parse_seconds DOUBLE, llm_seconds DOUBLE,
  prompt_tokens BIGINT, completion_tokens BIGINT, est_cost_usd DOUBLE);
CREATE TABLE IF NOT EXISTS extractions (
  run_id VARCHAR, filename VARCHAR, ok BOOLEAN, attempts INTEGER, error VARCHAR,
  seconds DOUBLE, prompt_tokens BIGINT, completion_tokens BIGINT, ungrounded VARCHAR, record VARCHAR);
CREATE TABLE IF NOT EXISTS clause_flags (
  run_id VARCHAR, filename VARCHAR, field VARCHAR, present BOOLEAN, quote VARCHAR);
CREATE TABLE IF NOT EXISTS metrics (
  run_id VARCHAR, level VARCHAR, name VARCHAR, ftype VARCHAR,
  tp INTEGER, fp INTEGER, fn INTEGER, tn INTEGER,
  precision DOUBLE, recall DOUBLE, f1 DOUBLE, support INTEGER);
CREATE TABLE IF NOT EXISTS api_extractions (
  id VARCHAR, filename VARCHAR, created_at TIMESTAMP, ok BOOLEAN, record VARCHAR, error VARCHAR);
"""


@contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    try:
        con.execute(SCHEMA)
        yield con
    finally:
        con.close()


def save_run(meta: dict, results: list) -> None:
    run_id = meta["run_id"]
    with connect() as con:
        for t in ("runs", "extractions", "clause_flags", "metrics"):
            con.execute(f"DELETE FROM {t} WHERE run_id = ?", [run_id])
        con.execute("INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", [
            run_id, meta["parser"], meta["model"], datetime.now(timezone.utc).replace(tzinfo=None),
            meta["n_docs"], meta["ok_docs"], meta["retry_docs"], meta["parse_seconds"],
            meta["llm_seconds"], meta["prompt_tokens"], meta["completion_tokens"], meta["est_cost_usd"]])
        for r in results:
            con.execute("INSERT INTO extractions VALUES (?,?,?,?,?,?,?,?,?,?)", [
                run_id, r.filename, r.ok, r.attempts, r.error, r.seconds, r.prompt_tokens,
                r.completion_tokens, json.dumps(r.ungrounded), json.dumps(r.record) if r.record else None])
            if r.record:
                for key, val in r.record.items():
                    if isinstance(val, dict) and "present" in val:
                        con.execute("INSERT INTO clause_flags VALUES (?,?,?,?,?)",
                                    [run_id, r.filename, key, val["present"], val.get("quote")])


def save_metrics(run_id: str, rows: list[dict]) -> None:
    with connect() as con:
        con.execute("DELETE FROM metrics WHERE run_id = ?", [run_id])
        for r in rows:
            con.execute("INSERT INTO metrics VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", [
                run_id, r["level"], r["name"], r["ftype"], r["tp"], r["fp"], r["fn"], r["tn"],
                r["precision"], r["recall"], r["f1"], r["support"]])


def query(sql: str, params: list | None = None) -> list[dict]:
    with connect() as con:
        cur = con.execute(sql, params or [])
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def save_api_extraction(id_: str, filename: str, ok: bool, record: dict | None, error: str | None) -> None:
    with connect() as con:
        con.execute("INSERT INTO api_extractions VALUES (?,?,?,?,?,?)", [
            id_, filename, datetime.now(timezone.utc).replace(tzinfo=None), ok,
            json.dumps(record) if record else None, error])
