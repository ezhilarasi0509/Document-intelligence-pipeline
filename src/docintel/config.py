"""Central configuration. Everything tunable lives here or in .env."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DATA_DIR = Path(os.getenv("DATA_DIR", ROOT / "data"))
RAW_DIR = DATA_DIR / "raw"
PDF_DIR = RAW_DIR / "pdf"
PARSED_DIR = DATA_DIR / "parsed"
PRED_DIR = DATA_DIR / "predictions"
REPORTS_DIR = Path(os.getenv("REPORTS_DIR", ROOT / "reports"))
DB_PATH = Path(os.getenv("DB_PATH", DATA_DIR / "docintel.duckdb"))
LABELS_CSV = RAW_DIR / "master_clauses.csv"
MANIFEST = RAW_DIR / "manifest.json"

# CUAD v1 on Zenodo. If this URL ever changes, download the zip manually from
# atticusprojectai.org/cuad and place it at data/raw/CUAD_v1.zip.
CUAD_ZIP_URL = "https://zenodo.org/records/4595826/files/CUAD_v1.zip?download=1"
CUAD_ZIP_PATH = RAW_DIR / "CUAD_v1.zip"

# --- LLM (Groq, OpenAI-compatible) ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

# --- Gemini (optional multimodal arm) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# --- Tuning ---
MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS", "16000"))
HEAD_CHARS = 3500  # the start of a contract (title, parties, date) is always included
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "3000"))
MAX_VALIDATION_ATTEMPTS = int(os.getenv("MAX_VALIDATION_ATTEMPTS", "3"))
REQUEST_DELAY_S = float(os.getenv("REQUEST_DELAY_S", "2"))
MAX_PDF_MB = 15

# Hypothetical PAID prices in USD per 1M tokens (input, output). You pay $0 on free tiers;
# these exist so the report can answer "what would this cost at scale?".
# Looked up Nov 2026 - VERIFY before quoting: console.groq.com pricing, ai.google.dev/gemini-api/docs/pricing.
# Gemini 3.6 Flash: most sources list $1.50 / $7.50, one tracker lists $0.75 / $3.75 (check Google's page).
# Gemini bills "thinking" tokens as output; our script only counts visible output, so Gemini cost is a floor.
PRICES_PER_M = {
    "default": (0.075, 0.30),
    "openai/gpt-oss-20b": (0.075, 0.30),
    "gemini-3.6-flash": (1.50, 7.50),
}
