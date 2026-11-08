# Free deploy on Render (Docker)
1. render.com, sign up with GitHub (no card needed).
2. New, Web Service, pick this repo. Language: Docker. Instance type: Free. Health check path: /health.
3. Environment variables: GROQ_API_KEY, MAX_CONTEXT_CHARS=9000, MAX_OUTPUT_TOKENS=1500.
4. Create. When it says Live, open the service URL (it redirects to /docs).
Free services sleep after 15 minutes idle and take about a minute to wake up.
