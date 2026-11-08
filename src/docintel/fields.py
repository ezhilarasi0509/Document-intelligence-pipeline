"""The field registry: ONE place that defines what we extract, how we find it, and how we score it.

Adding a field = add one FieldSpec here + one attribute in schema.py.
Pure stdlib on purpose (no pydantic) so labels/metrics/context stay easy to test.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FieldType(str, Enum):
    ENTITY = "entity"   # free text: names, jurisdictions, short phrases
    DATE = "date"       # calendar dates
    CLAUSE = "clause"   # does the contract contain this clause? (yes/no)


@dataclass(frozen=True)
class FieldSpec:
    key: str                      # attribute name in ContractExtraction
    cuad_column: str              # column name in CUAD's master_clauses.csv (without "-Answer")
    ftype: FieldType
    keywords: tuple[str, ...]     # used to pick relevant paragraphs for the LLM
    match_threshold: float = 0.6  # token-F1 needed to call a text answer correct
    allow_containment: bool = True  # "Delaware" == "State of Delaware"?


FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec("document_name", "Document Name", FieldType.ENTITY,
              ("agreement", "contract", "this ")),
    FieldSpec("parties", "Parties", FieldType.ENTITY,
              ("by and between", "between", "party", "parties", "inc.", "llc", "corporation"),
              match_threshold=0.5, allow_containment=False),
    FieldSpec("agreement_date", "Agreement Date", FieldType.DATE,
              ("dated", "dated as of", "made and entered", "entered into", "as of")),
    FieldSpec("effective_date", "Effective Date", FieldType.DATE,
              ("effective date", "effective as of", "commence")),
    FieldSpec("expiration_date", "Expiration Date", FieldType.DATE,
              ("expire", "expiration", "term of this agreement", "terminate on", "initial term")),
    FieldSpec("renewal_term", "Renewal Term", FieldType.ENTITY,
              ("renew", "successive", "automatically extend", "extended for"),
              match_threshold=0.4, allow_containment=False),
    FieldSpec("governing_law", "Governing Law", FieldType.ENTITY,
              ("governing law", "governed by", "laws of the state", "jurisdiction",
               "construed in accordance")),
    FieldSpec("non_compete", "Non-Compete", FieldType.CLAUSE,
              ("non-compet", "not compete", "shall not engage", "competing business", "competitive")),
    FieldSpec("exclusivity", "Exclusivity", FieldType.CLAUSE,
              ("exclusive", "exclusively", "sole and exclusive")),
    FieldSpec("anti_assignment", "Anti-Assignment", FieldType.CLAUSE,
              ("assign", "transfer", "change of control", "consent of")),
    FieldSpec("cap_on_liability", "Cap On Liability", FieldType.CLAUSE,
              ("limitation of liability", "in no event", "aggregate liability",
               "shall not exceed", "consequential")),
    FieldSpec("termination_for_convenience", "Termination For Convenience", FieldType.CLAUSE,
              ("terminate this agreement", "terminate for convenience", "without cause",
               "upon written notice", "days' notice", "days prior written notice")),
)

FIELD_BY_KEY = {f.key: f for f in FIELDS}
CLAUSE_KEYS = tuple(f.key for f in FIELDS if f.ftype is FieldType.CLAUSE)
