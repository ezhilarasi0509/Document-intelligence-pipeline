# Free deploy: Hugging Face Spaces (Docker)

Cloud Run's free tier needs a billing card on file, so we use Hugging Face Spaces (free CPU, Docker supported).
The code is identical either way; Dockerfile reads `PORT` (7860 here, `$PORT` on Cloud Run).

1. Create a free account at huggingface.co, then **New Space** -> SDK: **Docker** -> blank -> Public.
2. Space **Settings -> Variables and secrets** -> add secret `GROQ_API_KEY` (and optionally `GROQ_MODEL`).
3. Clone the Space repo locally, copy in: `Dockerfile`, `pyproject.toml`, `src/`, and this README as `README.md`:

```
---
title: Contract Document Intelligence
emoji: 📄
sdk: docker
app_port: 7860
---
# Contract Document Intelligence
POST a contract PDF to /extract. Docs at /docs.
```
4. `git add . && git commit -m "deploy" && git push` -> the Space builds and goes live at
   `https://<user>-<space>.hf.space/docs`.

Caveats worth mentioning in interviews: free Spaces sleep when idle (cold start), storage is ephemeral
(DuckDB file resets on restart), so the deployed API is a demo; the real analytics live in your offline runs.

## Optional: Cloud Run (if you add a billing account)
```
gcloud run deploy docintel --source . --region asia-south1 --set-secrets GROQ_API_KEY=groq-key:latest --allow-unauthenticated
```
