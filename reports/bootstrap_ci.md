# Clause F1 with 95% bootstrap confidence intervals (40 documents, 5000 resamples)

| run | clause F1 | 95% CI |
|---|---|---|
| pymupdf_groq_v2 | 0.65 | 0.56 to 0.72 |
| gemini_snippets | 0.65 | 0.55 to 0.74 |
| gemini_full | 0.87 | 0.81 to 0.92 |

## Paired difference vs `pymupdf_groq_v2`

| run | F1 difference | 95% CI | share of resamples where it is better |
|---|---|---|---|
| gemini_snippets | +0.00 | -0.05 to +0.05 | 56.3% |
| gemini_full | +0.22 | +0.15 to +0.29 | 100.0% |

A difference is reliable when its whole interval is on one side of zero.
