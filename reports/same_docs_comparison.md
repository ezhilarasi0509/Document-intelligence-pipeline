# Same-documents comparison (20 documents finished by every run)

Small samples are noisy: treat differences under ~0.10 F1 as inconclusive.

## By field type (precision / recall / F1)

| type | pymupdf_groq_v2 | gemini_snippets | gemini_full |
|---|---|---|---|
| entity | 0.88 / 0.80 / **0.84** | 0.91 / 0.82 / **0.86** | 0.88 / 0.92 / **0.90** |
| date | 0.94 / 0.62 / **0.74** | 0.97 / 0.60 / **0.74** | 0.97 / 0.66 / **0.78** |
| clause | 0.83 / 0.53 / **0.65** | 0.94 / 0.45 / **0.61** | 0.94 / 0.82 / **0.87** |

## F1 per field

| field | support | pymupdf_groq_v2 | gemini_snippets | gemini_full |
|---|---|---|---|---|
| document_name | 20 | 0.95 | 1.00 | 1.00 |
| parties | 20 | 0.95 | 1.00 | 1.00 |
| agreement_date | 19 | 0.89 | 0.82 | 0.86 |
| effective_date | 14 | 0.80 | 0.88 | 0.96 |
| expiration_date | 14 | 0.35 | 0.35 | 0.35 |
| renewal_term | 7 | 0.36 | 0.17 | 0.25 |
| governing_law | 14 | 0.69 | 0.75 | 0.97 |
| non_compete | 6 | 0.29 | 0.29 | 0.67 |
| exclusivity | 5 | 0.29 | 0.00 | 0.89 |
| anti_assignment | 13 | 1.00 | 0.92 | 1.00 |
| cap_on_liability | 9 | 0.36 | 0.36 | 0.88 |
| termination_for_convenience | 5 | 0.55 | 0.67 | 0.73 |
