# Clause F1 with 95% bootstrap confidence intervals (20 documents, 5000 resamples)

| run | clause F1 | 95% CI |
|---|---|---|
| pymupdf_groq_v2 | 0.65 | 0.54 to 0.74 |
| gemini_snippets | 0.61 | 0.46 to 0.74 |
| gemini_full | 0.87 | 0.81 to 0.93 |

## Paired difference vs `pymupdf_groq_v2`

| run | F1 difference | 95% CI | share of resamples where it is better |
|---|---|---|---|
| gemini_snippets | -0.04 | -0.14 to +0.05 | 19.5% |
| gemini_full | +0.23 | +0.15 to +0.32 | 100.0% |

A difference is reliable when its whole interval is on one side of zero.
