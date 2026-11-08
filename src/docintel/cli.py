"""Command line: docintel download | inspect-labels | run | evaluate | report | serve"""
from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="docintel", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("download", help="download CUAD and keep a small seeded sample")
    d.add_argument("--n", type=int, default=40)
    d.add_argument("--seed", type=int, default=42)
    d.add_argument("--keep-zip", action="store_true")

    sub.add_parser("inspect-labels", help="verify label columns and show label statistics")

    r = sub.add_parser("run", help="parse + extract all sampled contracts")
    r.add_argument("--parser", choices=["pymupdf", "docling", "gemini_direct"], required=True)
    r.add_argument("--run-id", required=True)
    r.add_argument("--limit", type=int)
    r.add_argument("--force", action="store_true")

    e = sub.add_parser("evaluate", help="score a run against CUAD labels")
    e.add_argument("--run-id", required=True)

    sub.add_parser("report", help="write reports/comparison.md")

    c = sub.add_parser("compare", help="fair comparison on the documents every listed run finished")
    c.add_argument("--runs", nargs="+", required=True)

    s = sub.add_parser("serve", help="start the FastAPI server")
    s.add_argument("--port", type=int, default=8000)

    a = ap.parse_args(argv)
    if a.cmd == "download":
        from .download import download
        download(a.n, a.seed, a.keep_zip)
    elif a.cmd == "inspect-labels":
        from .inspect_labels import main as inspect
        inspect()
    elif a.cmd == "run":
        from .pipeline import run
        run(a.parser, a.run_id, a.limit, a.force)
    elif a.cmd == "evaluate":
        from .evaluate import evaluate
        evaluate(a.run_id)
    elif a.cmd == "report":
        from .report import build
        build()
    elif a.cmd == "compare":
        from .compare import compare
        compare(a.runs)
    elif a.cmd == "serve":
        import uvicorn
        uvicorn.run("docintel.api:app", host="127.0.0.1", port=a.port, reload=False)


if __name__ == "__main__":
    main()
