import pytest
from pydantic import ValidationError

from docintel.schema import ContractExtraction, example_json

OFF = {"present": False, "quote": None}


def _base(**over):
    d = dict(document_name="X Agreement", parties=["A", "B"], agreement_date="2020-01-31",
             effective_date=None, expiration_date=None, renewal_term=None, governing_law="Texas",
             non_compete=OFF, exclusivity=OFF, anti_assignment=OFF, cap_on_liability=OFF,
             termination_for_convenience=OFF)
    d.update(over)
    return d


def test_valid_record():
    assert ContractExtraction(**_base()).governing_law == "Texas"


def test_example_roundtrip():
    assert ContractExtraction.model_validate_json(example_json()).parties == ["Acme Corp", "Beta LLC"]


def test_bad_date_format_rejected():
    with pytest.raises(ValidationError):
        ContractExtraction(**_base(agreement_date="January 31, 2020"))


def test_impossible_date_rejected():
    with pytest.raises(ValidationError):
        ContractExtraction(**_base(effective_date="2020-02-30"))


def test_nullish_strings_become_none():
    rec = ContractExtraction(**_base(governing_law="N/A", agreement_date="null"))
    assert rec.governing_law is None and rec.agreement_date is None


def test_clause_needs_quote_when_present():
    with pytest.raises(ValidationError):
        ContractExtraction(**_base(non_compete={"present": True, "quote": None}))


def test_quote_dropped_when_absent():
    rec = ContractExtraction(**_base(exclusivity={"present": False, "quote": "stray"}))
    assert rec.exclusivity.quote is None
