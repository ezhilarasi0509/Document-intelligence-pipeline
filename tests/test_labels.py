import csv

import pytest

from docintel.labels import load_gold, resolve_column, stem
from docintel.fields import FIELDS


def test_resolve_column_is_forgiving():
    headers = ["Filename", "Anti-Assignment-Answer", "Governing Law-Answer"]
    assert resolve_column(headers, "anti assignment-answer") == "Anti-Assignment-Answer"
    with pytest.raises(KeyError):
        resolve_column(headers, "Nonexistent-Answer")


def test_stem():
    assert stem("ABC Corp-EX-1.PDF") == "abc corp-ex-1"


def test_load_gold(tmp_path):
    headers = ["Filename"] + [f"{f.cuad_column}-Answer" for f in FIELDS]
    p = tmp_path / "labels.csv"
    with open(p, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(headers)
        row = ["Doc One.pdf"] + [""] * len(FIELDS)
        row[headers.index("Governing Law-Answer")] = "Delaware"
        row[headers.index("Non-Compete-Answer")] = "Yes"
        w.writerow(row)
    gold = load_gold(p)
    assert gold["doc one"]["governing_law"] == "Delaware"
    assert gold["doc one"]["non_compete"] is True
    assert gold["doc one"]["exclusivity"] is False
    assert gold["doc one"]["agreement_date"] is None
