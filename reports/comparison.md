# Comparison of runs

## 1. Accuracy by field type (micro-averaged F1)

| run | entity | date | clause |
|---|---|---|---|
| smoke | 0.89 | 0.96 | 0.86 |
| pymupdf_groq | 0.84 | 0.80 | 0.64 |
| pymupdf_groq_v2 | 0.83 | 0.79 | 0.65 |
| docling_groq | 0.84 | 0.78 | 0.68 |
| gemini_full | 0.87 | 0.80 | 0.87 |
| docling_ocr_groq | 0.80 | 0.77 | 0.69 |

## 2. F1 per field

| field | smoke | pymupdf_groq | pymupdf_groq_v2 | docling_groq | gemini_full | docling_ocr_groq |
|---|---|---|---|---|---|---|
| agreement_date | 1.00 | 0.88 | 0.90 | 0.87 | 0.89 | 0.88 |
| anti_assignment | 1.00 | 0.94 | 0.94 | 0.82 | 0.96 | 0.86 |
| cap_on_liability | 1.00 | 0.40 | 0.40 | 0.62 | 0.82 | 0.62 |
| document_name | 0.80 | 0.97 | 0.97 | 1.00 | 1.00 | 0.90 |
| effective_date | 1.00 | 0.91 | 0.87 | 0.91 | 0.96 | 0.87 |
| exclusivity | 1.00 | 0.56 | 0.59 | 0.62 | 0.91 | 0.62 |
| expiration_date | 0.80 | 0.51 | 0.47 | 0.43 | 0.39 | 0.46 |
| governing_law | 0.86 | 0.82 | 0.81 | 0.79 | 0.99 | 0.74 |
| non_compete | 0.00 | 0.14 | 0.14 | 0.38 | 0.70 | 0.47 |
| parties | 1.00 | 0.95 | 0.92 | 0.95 | 0.95 | 0.97 |
| renewal_term | 0.00 | 0.26 | 0.27 | 0.20 | 0.21 | 0.19 |
| termination_for_convenience | 0.00 | 0.58 | 0.58 | 0.69 | 0.81 | 0.62 |

## 3. Performance vs cost

Cost is *hypothetical paid pricing* (edit `PRICES_PER_M` in config.py); free tiers cost $0.

| run | parser | model | valid | retried | parse s/doc | LLM s/doc | tokens/doc | est $ per 1k docs | total s/doc |
|---|---|---|---|---|---|---|---|---|---|
| smoke | pymupdf | openai/gpt-oss-20b | 5/5 | 0 | 0.33 | 30.71 | 5,754 | $0.64 | 31.03 |
| pymupdf_groq | pymupdf | openai/gpt-oss-20b | 40/40 | 5 | 0.09 | 247.71 | 4,806 | $0.59 | 247.79 |
| pymupdf_groq_v2 | pymupdf | openai/gpt-oss-20b | 40/40 | 2 | 0.09 | 1349.44 | 4,654 | $0.57 | 1349.53 |
| docling_groq | docling | openai/gpt-oss-20b | 40/40 | 8 | 7.26 | 30.49 | 4,149 | $0.54 | 37.76 |
| gemini_full | gemini_direct | gemini-3.6-flash | 40/40 | 0 | 0.00 | 29.41 | 8,230 | $14.05 | 29.41 |
| docling_ocr_groq | docling | openai/gpt-oss-20b | 40/40 | 3 | 58.50 | 2.97 | 4,051 | $0.53 | 61.48 |
