"""LLM extraction with a validate -> explain -> retry loop (Parser-agnostic: takes plain text).

Flow per document:
  text -> build_context (pick relevant paragraphs) -> LLM (JSON) -> Pydantic validation
       -> if invalid: send the exact validation errors back to the model and retry
       -> grounding check: is each 'quote' really in the source text?
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field

from openai import APIConnectionError, APIStatusError, BadRequestError, OpenAI, RateLimitError
from pydantic import ValidationError

from . import config
from .context import build_context
from .fields import CLAUSE_KEYS
from .schema import ContractExtraction, example_json

SYSTEM_PROMPT = f"""You are a careful contract-review assistant. You receive excerpts from ONE commercial contract
(its opening section plus the paragraphs most relevant to the fields below). Return ONE JSON object and nothing else.

Rules:
- Use ONLY the excerpts. Never guess. Unknown -> null (parties -> [], clause flags -> present=false, quote=null).
- Dates must be ISO YYYY-MM-DD. If only a month/year or a relative period is given, use null.
- document_name: the title as written (e.g. "Software License Agreement").
- parties: legal names of the contracting parties (not individual signatories).
- agreement_date: when the contract is dated/signed. effective_date: when it takes effect.
- expiration_date: only if a calendar date is stated (not "two years after...").
- renewal_term: short phrase about renewal/extension, else null.
- governing_law: the jurisdiction only (e.g. "Delaware", "State of New York"), else null.
- Clause flags: present=true ONLY if the contract has a clause matching the definition, and quote = ONE verbatim
  sentence from the excerpts (max 300 chars) that proves it. Otherwise present=false, quote=null.
    non_compete: restricts a party from competing or engaging in a competing business.
    exclusivity: grants exclusive rights, or restricts a party to dealing only with the other party.
    anti_assignment: requires consent to assign/transfer the contract, or restricts assignment / change of control.
    cap_on_liability: caps a party's liability at a dollar amount or formula.
    termination_for_convenience: lets a party terminate without cause (usually on notice).

The JSON must have exactly this shape (example values shown):
{example_json()}"""


@dataclass
class ExtractionResult:
    filename: str
    ok: bool = False
    record: dict | None = None
    attempts: int = 0
    error: str | None = None
    seconds: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    context_chars: int = 0
    ungrounded: list[str] = field(default_factory=list)
    parse_seconds: float = 0.0


class _TooLarge(Exception):
    """HTTP 413: prompt + reserved output exceeds the free-tier tokens-per-minute cap."""


class _BadOutput(Exception):
    """The API itself rejected the model's output as invalid JSON; treat like a validation failure."""


_client: OpenAI | None = None
_json_mode = "json_schema"  # auto-downgrades to "json_object" if the model/endpoint rejects schemas


def get_client() -> OpenAI:
    global _client
    if _client is None:
        if not config.GROQ_API_KEY:
            raise SystemExit("GROQ_API_KEY is missing. Copy .env.example to .env and paste your free key.")
        _client = OpenAI(api_key=config.GROQ_API_KEY, base_url=config.GROQ_BASE_URL, max_retries=0)
    return _client


def _chat(messages: list[dict], mode: str):
    kwargs = dict(model=config.GROQ_MODEL, messages=messages, temperature=0,
                  max_completion_tokens=config.MAX_OUTPUT_TOKENS)
    if mode == "json_schema":
        kwargs["response_format"] = {"type": "json_schema", "json_schema": {
            "name": "contract_extraction", "strict": False,
            "schema": ContractExtraction.model_json_schema()}}
    else:
        kwargs["response_format"] = {"type": "json_object"}
    return get_client().chat.completions.create(**kwargs)


def _retry_after(e: RateLimitError) -> float | None:
    try:
        return float(e.response.headers.get("retry-after"))
    except Exception:
        return None


def _call(messages: list[dict]):
    global _json_mode
    for attempt in range(6):
        try:
            return _chat(messages, _json_mode)
        except BadRequestError as e:
            msg = str(e).lower()
            if _json_mode == "json_schema" and ("json_schema" in msg or "response_format" in msg or "not support" in msg):
                print(f"[extract] json_schema not accepted here; falling back to json_object. ({str(e)[:100]})")
                _json_mode = "json_object"
                continue
            raise _BadOutput(str(e)[:300]) from e
        except RateLimitError as e:
            if "too large" in str(e).lower():
                raise RuntimeError("Request too large for your free-tier token limit. Lower MAX_CONTEXT_CHARS in .env.") from e
            wait = _retry_after(e) or min(60, 5 * 2**attempt)
            print(f"[extract] rate limited; sleeping {wait:.0f}s")
            time.sleep(wait)
        except APIConnectionError:
            wait = min(60, 5 * 2**attempt)
            print(f"[extract] network error; retrying in {wait}s")
            time.sleep(wait)
        except APIStatusError as e:
            if e.status_code == 413:
                raise _TooLarge(str(e)[:200]) from e
            raise
    raise RuntimeError("Rate-limit retries exhausted (daily quota?). Wait, or switch GROQ_MODEL in .env.")


def _json_text(content: str) -> str:
    content = re.sub(r"^```(?:json)?|```$", "", content.strip(), flags=re.M).strip()
    i, j = content.find("{"), content.rfind("}")
    return content[i:j + 1] if i != -1 and j > i else content


def format_errors(err: ValidationError) -> str:
    parts = [f"{'.'.join(str(x) for x in e['loc']) or 'root'}: {e['msg']}" for e in err.errors()]
    return "; ".join(parts)[:700]


def _norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def ungrounded_quotes(rec: ContractExtraction, context: str) -> list[str]:
    """Clause keys whose supporting quote can't be found in the source (hallucination signal)."""
    ctx = _norm_ws(context)
    bad = []
    for key in CLAUSE_KEYS:
        flag = getattr(rec, key)
        if flag.present and flag.quote and _norm_ws(flag.quote)[:80] not in ctx:
            bad.append(key)
    return bad


def extract_from_text(text: str, filename: str = "") -> ExtractionResult:
    context = build_context(text)
    messages = [
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": f"CONTRACT EXCERPTS:\n<<<\n{context}\n>>>\nReturn the JSON object."},
    ]
    res = ExtractionResult(filename=filename, context_chars=len(context))
    t0 = time.perf_counter()
    for attempt in range(1, config.MAX_VALIDATION_ATTEMPTS + 1):
        res.attempts = attempt
        content = ""
        try:
            resp = _call(messages)
            if resp.usage:
                res.prompt_tokens += resp.usage.prompt_tokens or 0
                res.completion_tokens += resp.usage.completion_tokens or 0
            content = resp.choices[0].message.content or ""
            rec = ContractExtraction.model_validate_json(_json_text(content))
            res.ok, res.record, res.error = True, rec.model_dump(), None
            res.ungrounded = ungrounded_quotes(rec, context)
            break
        except ValidationError as e:
            res.error = format_errors(e)
        except _TooLarge:
            context = build_context(text, max_chars=max(int(len(context) * 0.65), 4500))
            res.context_chars = len(context)
            messages[1]["content"] = f"CONTRACT EXCERPTS:\n<<<\n{context}\n>>>\nReturn the JSON object."
            res.error = "request too large; shrank context and retried"
            continue
        except _BadOutput as e:
            res.error = f"API rejected output: {e}"
        messages += [
            {"role": "assistant", "content": content or "{}"},
            {"role": "user", "content": f"Your JSON failed validation: {res.error}\n"
                                        "Return the corrected, complete JSON object only."},
        ]
    res.seconds = time.perf_counter() - t0
    return res


def result_to_json(res: ExtractionResult) -> str:
    return json.dumps(res.__dict__, indent=2, default=str)


# ---- Prompt v3: definitions widened to match how CUAD's lawyers actually label ----
_V3_SWAPS = [
    ("non_compete: restricts a party from competing or engaging in a competing business.",
     "non_compete: restricts a party from competing, soliciting, or dealing with competitors (competitor lists, bans on engaging or investing in a competing business, during or after the term)."),
    ("exclusivity: grants exclusive rights, or restricts a party to dealing only with the other party.",
     "exclusivity: any exclusive grant or restriction: exclusive license/territory/supply/purchase/distribution rights, a party barred from dealing with others, or a promise not to grant the same rights to third parties."),
    ("anti_assignment: requires consent to assign/transfer the contract, or restricts assignment / change of control.",
     "anti_assignment: any provision restricting or conditioning assignment/transfer of the contract or its rights (consent requirements, change of control, limits even if some assignments are allowed)."),
    ("cap_on_liability: caps a party's liability at a dollar amount or formula.",
     "cap_on_liability: any limit on liability: a cap (dollar amount or formula such as fees paid), OR an exclusion/waiver of consequential, indirect, incidental or punitive damages, OR a time limit on claims."),
    ("termination_for_convenience: lets a party terminate without cause (usually on notice).",
     "termination_for_convenience: a party may end the contract or stop providing services without cause: on notice, at its discretion, or for convenience (not termination for breach or insolvency)."),
    ('- expiration_date: only if a calendar date is stated (not "two years after...").',
     '- expiration_date: end of the initial term as a calendar date. If the term is a fixed period from a stated date (e.g. "5 years from June 16, 2004"), compute the end date; otherwise null.'),
    ("- renewal_term: short phrase about renewal/extension, else null.",
     "- renewal_term: short normalized phrase, e.g. 'successive 1 year' when it renews automatically for repeated periods; null if there is no renewal."),
]


def get_system_prompt() -> str:
    """PROMPT_VERSION=v3 in the environment switches to the widened definitions."""
    if os.getenv("PROMPT_VERSION", "v2") != "v3":
        return SYSTEM_PROMPT
    out = SYSTEM_PROMPT
    for old, new in _V3_SWAPS:
        assert old in out, f"v3 swap target missing: {old[:50]!r}"
        out = out.replace(old, new, 1)
    return out
