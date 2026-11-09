# Same-documents comparison (40 documents finished by every run)

Small samples are noisy: treat differences under ~0.10 F1 as inconclusive.

## By field type (precision / recall / F1)

| type | pymupdf_groq_v2 | gemini_snippets | gemini_full |
|---|---|---|---|
| entity | 0.85 / 0.81 / **0.83** | 0.87 / 0.81 / **0.84** | 0.84 / 0.89 / **0.87** |
| date | 0.94 / 0.68 / **0.79** | 0.98 / 0.67 / **0.79** | 0.98 / 0.68 / **0.80** |
| clause | 0.88 / 0.51 / **0.65** | 0.93 / 0.50 / **0.65** | 0.93 / 0.81 / **0.87** |

## F1 per field

| field | support | pymupdf_groq_v2 | gemini_snippets | gemini_full |
|---|---|---|---|---|
| document_name | 40 | 0.97 | 1.00 | 1.00 |
| parties | 39 | 0.92 | 0.97 | 0.95 |
| agreement_date | 35 | 0.90 | 0.88 | 0.89 |
| effective_date | 29 | 0.87 | 0.95 | 0.96 |
| expiration_date | 29 | 0.47 | 0.43 | 0.39 |
| renewal_term | 16 | 0.27 | 0.12 | 0.21 |
| governing_law | 33 | 0.81 | 0.83 | 0.99 |
| non_compete | 12 | 0.14 | 0.14 | 0.70 |
| exclusivity | 11 | 0.59 | 0.53 | 0.91 |
| anti_assignment | 28 | 0.94 | 0.92 | 0.96 |
| cap_on_liability | 20 | 0.40 | 0.40 | 0.82 |
| termination_for_convenience | 13 | 0.58 | 0.70 | 0.81 |
