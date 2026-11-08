from docintel.fields import FIELD_BY_KEY
from docintel.metrics import aggregate, outcome, parse_date, prf, text_match


def test_prf():
    assert prf(8, 2, 2) == (0.8, 0.8, 0.8000000000000002) or abs(prf(8, 2, 2)[2] - 0.8) < 1e-9
    assert prf(0, 0, 0) == (0.0, 0.0, 0.0)


def test_text_match_containment_and_stopwords():
    assert text_match("Delaware", "State of Delaware", 0.6)
    assert not text_match("New York", "Delaware", 0.6)


def test_parties_need_overlap_not_containment():
    spec = FIELD_BY_KEY["parties"]
    assert outcome(spec, ["Acme Inc.", "Beta LLC"], "Acme, Beta") == "TP"
    # only one of two parties found -> F1 below threshold -> wrong
    assert outcome(spec, ["Acme Inc."], "Acme Inc., Beta LLC, Gamma Corp, Delta Co") == "FPFN"


def test_dates():
    assert parse_date("5/6/2005").isoformat() == "2005-05-06"
    spec = FIELD_BY_KEY["agreement_date"]
    assert outcome(spec, "2005-05-06", "5/6/2005") == "TP"
    assert outcome(spec, "2005-05-07", "5/6/2005") == "FPFN"
    assert outcome(spec, None, "5/6/2005") == "FN"
    assert outcome(spec, "2005-05-06", None) == "FP"
    assert outcome(spec, None, None) == "TN"


def test_clause_outcomes():
    spec = FIELD_BY_KEY["non_compete"]
    assert outcome(spec, True, True) == "TP"
    assert outcome(spec, True, False) == "FP"
    assert outcome(spec, False, True) == "FN"
    assert outcome(spec, False, False) == "TN"


def test_aggregate_by_type():
    rows = aggregate([("non_compete", "TP"), ("non_compete", "FN"), ("exclusivity", "TP"),
                      ("governing_law", "FPFN")])
    clause = next(r for r in rows if r["level"] == "type" and r["name"] == "clause")
    assert clause["tp"] == 2 and clause["fn"] == 1
    gl = next(r for r in rows if r["name"] == "governing_law")
    assert gl["fp"] == 1 and gl["fn"] == 1 and gl["f1"] == 0.0
