# Light image: API only (PyMuPDF + Groq). Docling/Gemini/Phoenix stay offline-experiment extras.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATA_DIR=/app/data REPORTS_DIR=/app/reports PORT=7860
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir -e .
RUN useradd -m app && mkdir -p /app/data /app/reports && chown -R app /app
USER app
EXPOSE 7860
CMD ["sh", "-c", "uvicorn docintel.api:app --host 0.0.0.0 --port ${PORT}"]
