"""Optional local tracing with Arize Phoenix (open source, free). Enable with ENABLE_PHOENIX=1.

Start the UI in another terminal:  uv run phoenix serve   (then open http://localhost:6006)
Every LLM call (prompt, response, tokens, latency) shows up as a trace you can click through.
"""
from __future__ import annotations

import os


def init_tracing(project: str = "docintel") -> bool:
    if os.getenv("ENABLE_PHOENIX", "0") != "1":
        return False
    try:
        from phoenix.otel import register

        register(project_name=project, auto_instrument=True)
        print(f"[tracing] Phoenix tracing on (project={project})")
        return True
    except ImportError:
        print("[tracing] Phoenix not installed. Run: uv sync --extra phoenix")
        return False
