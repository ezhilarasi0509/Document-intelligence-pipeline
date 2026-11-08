# Dataset: CUAD sample (40 contracts)

A seeded random sample (seed 42) of 40 commercial contracts from the
**Contract Understanding Atticus Dataset (CUAD) v1**, used to evaluate the pipeline.

- `pdf/` - the 40 contract PDFs
- `master_clauses.csv` - CUAD's expert labels for all 510 contracts (the pipeline scores against the `-Answer` columns)
- `manifest.json` - the 40 sampled contract names

## Source and license
CUAD is created by The Atticus Project (https://www.atticusprojectai.org/cuad) and released under
**CC BY 4.0**. Please cite: Hendrycks, Burns, Chen, Ball. *CUAD: An Expert-Annotated NLP Dataset
for Legal Contract Review.* NeurIPS 2021 Datasets and Benchmarks Track.
This folder is an unmodified subset. All credit for the contracts and annotations belongs to the
Atticus Project and its attorney annotators.
