"""Download CUAD once, keep only a small seeded sample of PDFs + the labels CSV (saves disk)."""
from __future__ import annotations

import json
import random
import shutil
import urllib.request
import zipfile
from pathlib import Path

from .config import CUAD_ZIP_PATH, CUAD_ZIP_URL, LABELS_CSV, MANIFEST, PDF_DIR, RAW_DIR
from .labels import stem


def _fetch(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url}\n  -> {dest}")
    req = urllib.request.Request(url, headers={"User-Agent": "docintel/0.1"})
    with urllib.request.urlopen(req) as r, open(dest, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while chunk := r.read(1 << 20):
            f.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r  {done / 1e6:.0f}/{total / 1e6:.0f} MB", end="", flush=True)
    print()


def download(n: int = 40, seed: int = 42, keep_zip: bool = False) -> list[str]:
    import csv

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    if not CUAD_ZIP_PATH.exists():
        _fetch(CUAD_ZIP_URL, CUAD_ZIP_PATH)

    with zipfile.ZipFile(CUAD_ZIP_PATH) as z:
        names = z.namelist()
        csv_members = [m for m in names if m.endswith("master_clauses.csv")]
        if not csv_members:
            raise SystemExit("master_clauses.csv not found in the zip; check the CUAD download.")
        with z.open(csv_members[0]) as src, open(LABELS_CSV, "wb") as dst:
            shutil.copyfileobj(src, dst)

        pdf_index = {stem(Path(m).name): m for m in names
                     if m.lower().endswith(".pdf") and "__MACOSX" not in m}
        with open(LABELS_CSV, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            file_col = next(h for h in reader.fieldnames if h.strip().lower() == "filename")
            labelled = sorted({stem(r[file_col]) for r in reader if r[file_col].strip()})
        candidates = [s for s in labelled if s in pdf_index]
        print(f"{len(labelled)} labelled contracts, {len(candidates)} have a PDF in the zip.")
        if not candidates:
            raise SystemExit("No overlap between labels and PDFs; filenames may differ. Run `docintel inspect-labels`.")

        random.Random(seed).shuffle(candidates)
        chosen = sorted(candidates[:n])
        for s in chosen:
            target = PDF_DIR / f"{s}.pdf"
            if not target.exists():
                with z.open(pdf_index[s]) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)

    MANIFEST.write_text(json.dumps(chosen, indent=2))
    if not keep_zip:
        CUAD_ZIP_PATH.unlink(missing_ok=True)
        print("Deleted the zip to save disk space (use --keep-zip to keep it).")
    print(f"Saved {len(chosen)} PDFs to {PDF_DIR} and the manifest to {MANIFEST}")
    return chosen
