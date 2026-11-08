# Same-documents comparison (40 documents finished by every run)

Small samples are noisy: treat differences under ~0.10 F1 as inconclusive.

## By field type (precision / recall / F1)

| type | pymupdf_groq | docling_groq | docling_ocr_groq | gemini_full |
|---|---|---|---|---|
| entity | 0.86 / 0.82 / **0.84** | 0.88 / 0.80 / **0.84** | 0.84 / 0.76 / **0.80** | 0.84 / 0.89 / **0.87** |
| date | 0.96 / 0.69 / **0.80** | 0.95 / 0.66 / **0.78** | 0.94 / 0.66 / **0.77** | 0.98 / 0.68 / **0.80** |
| clause | 0.86 / 0.51 / **0.64** | 0.88 / 0.55 / **0.68** | 0.87 / 0.57 / **0.69** | 0.93 / 0.81 / **0.87** |

## F1 per field

| field | support | pymupdf_groq | docling_groq | docling_ocr_groq | gemini_full |
|---|---|---|---|---|---|
| document_name | 40 | 0.97 | 1.00 | 0.90 | 1.00 |
| parties | 39 | 0.95 | 0.95 | 0.97 | 0.95 |
| agreement_date | 35 | 0.88 | 0.87 | 0.88 | 0.89 |
| effective_date | 29 | 0.91 | 0.91 | 0.87 | 0.96 |
| expiration_date | 29 | 0.51 | 0.43 | 0.46 | 0.39 |
| renewal_term | 16 | 0.26 | 0.20 | 0.19 | 0.21 |
| governing_law | 33 | 0.82 | 0.79 | 0.74 | 0.99 |
| non_compete | 12 | 0.14 | 0.38 | 0.47 | 0.70 |
| exclusivity | 11 | 0.56 | 0.62 | 0.62 | 0.91 |
| anti_assignment | 28 | 0.94 | 0.82 | 0.86 | 0.96 |
| cap_on_liability | 20 | 0.40 | 0.62 | 0.62 | 0.82 |
| termination_for_convenience | 13 | 0.58 | 0.69 | 0.62 | 0.81 |
