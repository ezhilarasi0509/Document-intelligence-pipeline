"""Arm C: multimodal end-to-end. Send the PDF itself to Gemini (free tier) - no separate parser.

Optional install: `uv sync --extra gemini`. Compare against the text-parser arms in `docintel report`.
"""
from __future__ import annotations

import time
from pathlib import Path

from pydantic import ValidationError

from . import config
from .extract import ExtractionResult, format_errors, get_system_prompt
from .schema import ContractExtraction


def extract_pdf(pdf: Path, max_attempts: int = 2) -> ExtractionResult:
    try:
        from google import genai
        from google.genai import types
    except ImportError as e:  # pragma: no cover
        raise SystemExit("google-genai is not installed. Run: uv sync --extra gemini") from e
    if not config.GEMINI_API_KEY:
        raise SystemExit("GEMINI_API_KEY is missing in .env (free at aistudio.google.com/apikey).")
    if pdf.stat().st_size > config.MAX_PDF_MB * 1_000_000:
        return ExtractionResult(filename=pdf.stem, error=f"PDF larger than {config.MAX_PDF_MB} MB; skipped")

    client = genai.Client(api_key=config.GEMINI_API_KEY)
    part = types.Part.from_bytes(data=pdf.read_bytes(), mime_type="application/pdf")
    res = ExtractionResult(filename=pdf.stem)
    prompt = "Read the attached contract PDF and return the JSON object."
    t0 = time.perf_counter()
    for attempt in range(1, max_attempts + 1):
        res.attempts = attempt
        resp = None
        last_err = ""
        for i in range(7):  # backoff on rate limits and temporary server overload
            try:
                resp = client.models.generate_content(
                    model=config.GEMINI_MODEL, contents=[part, prompt],
                    config=types.GenerateContentConfig(
                        system_instruction=get_system_prompt(), response_mime_type="application/json",
                        response_schema=ContractExtraction, temperature=0))
                break
            except Exception as e:  # noqa: BLE001 - SDK raises several error types
                if any(t in str(e) for t in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE", "500", "INTERNAL", "DEADLINE")):
                    last_err = str(e)[:200]
                    time.sleep(min(60, 8 * 2**i))
                    continue
                res.error = f"Gemini error: {str(e)[:200]}"
                break
        if resp is None:
            res.error = res.error or f"Gemini unavailable after retries: {last_err}"
            break
        u = getattr(resp, "usage_metadata", None)
        if u:
            res.prompt_tokens += getattr(u, "prompt_token_count", 0) or 0
            res.completion_tokens += getattr(u, "candidates_token_count", 0) or 0
        try:
            rec = ContractExtraction.model_validate_json(resp.text or "{}")
            res.ok, res.record, res.error = True, rec.model_dump(), None
            break
        except ValidationError as e:
            res.error = format_errors(e)
            prompt = f"Your previous JSON failed validation: {res.error}. Return the corrected JSON object."
    res.seconds = time.perf_counter() - t0
    return res
