"""Pydantic models = the contract between the LLM and the rest of the system.

Validation here is what turns "text that looks like JSON" into trustworthy records.
Every ValueError raised below is fed back to the model on retry (see extract.py).
"""
from __future__ import annotations

import re
from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator

_NULLISH = {"", "null", "none", "n/a", "na", "not specified", "not stated", "unknown", "unspecified"}
_ISO = re.compile(r"\d{4}-\d{2}-\d{2}")


def _clean_optional(v):
    if v is None:
        return None
    if isinstance(v, str):
        v = v.strip()
        if v.lower() in _NULLISH:
            return None
    return v


class ClauseFlag(BaseModel):
    present: bool = Field(description="True only if the contract contains this kind of clause.")
    quote: str | None = Field(
        description="One verbatim sentence (max 300 chars) that proves the clause exists; null if absent."
    )

    @model_validator(mode="after")
    def _quote_rules(self):
        if self.present and not (self.quote and self.quote.strip()):
            raise ValueError("present=true requires a verbatim supporting quote")
        if not self.present:
            self.quote = None
        elif self.quote and len(self.quote) > 600:
            self.quote = self.quote[:600]
        return self


class ContractExtraction(BaseModel):
    document_name: str | None = Field(description="Contract title as written, e.g. 'Software License Agreement'.")
    parties: list[str] = Field(description="Legal names of the contracting parties.")
    agreement_date: str | None = Field(description="Date the contract is signed/dated, ISO YYYY-MM-DD, else null.")
    effective_date: str | None = Field(description="Date the contract takes effect, ISO YYYY-MM-DD, else null.")
    expiration_date: str | None = Field(description="Date the initial term ends ONLY if a calendar date is stated, ISO YYYY-MM-DD, else null.")
    renewal_term: str | None = Field(description="Short phrase describing renewal, e.g. 'auto-renews for successive 1 year terms'; null if none.")
    governing_law: str | None = Field(description="Jurisdiction whose law governs, e.g. 'Delaware'; null if not stated.")
    non_compete: ClauseFlag
    exclusivity: ClauseFlag
    anti_assignment: ClauseFlag
    cap_on_liability: ClauseFlag
    termination_for_convenience: ClauseFlag

    @field_validator("document_name", "renewal_term", "governing_law", mode="before")
    @classmethod
    def _clean_text(cls, v):
        return _clean_optional(v)

    @field_validator("agreement_date", "effective_date", "expiration_date", mode="before")
    @classmethod
    def _check_date(cls, v):
        v = _clean_optional(v)
        if v is None:
            return None
        if not isinstance(v, str) or not _ISO.fullmatch(v):
            raise ValueError(f"must be ISO YYYY-MM-DD or null, got {v!r}")
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError(f"{v!r} is not a real calendar date") from None
        return v

    @field_validator("parties", mode="before")
    @classmethod
    def _clean_parties(cls, v):
        if isinstance(v, str):
            v = [v]
        if not isinstance(v, list):
            raise ValueError("parties must be a list of strings")
        seen, out = set(), []
        for p in v:
            p = str(p).strip()
            if p and p.lower() not in seen:
                seen.add(p.lower())
                out.append(p)
        return out


def example_json() -> str:
    """A tiny example shown to the model so it knows the exact shape (also works without strict schema mode)."""
    off = {"present": False, "quote": None}
    ex = ContractExtraction(
        document_name="Distribution Agreement",
        parties=["Acme Corp", "Beta LLC"],
        agreement_date="2019-03-01",
        effective_date=None,
        expiration_date=None,
        renewal_term="auto-renews for successive 1 year terms",
        governing_law="Delaware",
        non_compete=off, exclusivity=off, anti_assignment=off,
        cap_on_liability=off, termination_for_convenience=off,
    )
    return ex.model_dump_json()
