"""Sanity-check the labels BEFORE spending any API quota. Fails loudly if a column name is off."""
from __future__ import annotations

import json

from . import config
from .fields import FIELDS, FieldType
from .labels import check_headers, load_gold


def main() -> None:
    if not config.LABELS_CSV.exists():
        raise SystemExit("labels CSV missing. Run: uv run docintel download")
    print("Column mapping (our field -> CSV column):")
    for key, col in check_headers():
        print(f"  {key:<30} -> {col}")
    gold = load_gold()
    stems = json.loads(config.MANIFEST.read_text()) if config.MANIFEST.exists() else list(gold)
    sample = [gold[s] for s in stems if s in gold]
    print(f"\nLabel statistics over {len(sample)} sampled contracts:")
    for spec in FIELDS:
        vals = [g[spec.key] for g in sample]
        if spec.ftype is FieldType.CLAUSE:
            print(f"  {spec.key:<30} clause present in {sum(vals):>3}/{len(vals)} contracts")
        else:
            filled = [v for v in vals if v]
            example = filled[0][:50] if filled else "-"
            print(f"  {spec.key:<30} labelled in {len(filled):>3}/{len(vals)}   e.g. {example!r}")
