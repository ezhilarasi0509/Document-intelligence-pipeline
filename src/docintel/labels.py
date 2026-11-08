"""Load CUAD ground truth from master_clauses.csv (stdlib only)."""
from __future__ import annotations

import csv
import difflib
import re
from pathlib import Path

from .config import LABELS_CSV
from .fields import FIELDS, FieldType

_NONE = {"", "none", "n/a", "na", "nan", "[]", "null"}


def norm_col(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def resolve_column(headers: list[str], wanted: str) -> str:
    """Find a CSV column tolerant of case/punctuation differences, or explain what exists."""
    index = {norm_col(h): h for h in headers}
    hit = index.get(norm_col(wanted))
    if hit:
        return hit
    close = difflib.get_close_matches(wanted, headers, n=5)
    raise KeyError(f"Column {wanted!r} not found in labels CSV. Closest: {close}")


def stem(filename: str) -> str:
    return re.sub(r"\.pdf$|\.txt$", "", filename.strip(), flags=re.I).lower()


def clean_value(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip()
    return None if v.lower() in _NONE else v


def load_gold(csv_path: Path = LABELS_CSV) -> dict[str, dict[str, object]]:
    """Return {doc_stem: {field_key: value}}.

    ENTITY/DATE -> str | None (CUAD's normalized '-Answer' column)
    CLAUSE      -> bool (Answer == 'Yes')
    """
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        file_col = resolve_column(headers, "Filename")
        cols = {}
        for spec in FIELDS:
            cols[spec.key] = resolve_column(headers, f"{spec.cuad_column}-Answer")
        gold: dict[str, dict[str, object]] = {}
        for row in reader:
            name = row.get(file_col) or ""
            if not name.strip():
                continue
            rec: dict[str, object] = {}
            for spec in FIELDS:
                raw = row.get(cols[spec.key])
                if spec.ftype is FieldType.CLAUSE:
                    rec[spec.key] = (raw or "").strip().lower() == "yes"
                else:
                    rec[spec.key] = clean_value(raw)
            gold[stem(name)] = rec
    return gold


def check_headers(csv_path: Path = LABELS_CSV) -> list[tuple[str, str]]:
    """Return [(our_field, resolved_column)] - used by `docintel inspect-labels` to fail loudly and early."""
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        headers = list(csv.DictReader(f).fieldnames or [])
    return [(s.key, resolve_column(headers, f"{s.cuad_column}-Answer")) for s in FIELDS]
