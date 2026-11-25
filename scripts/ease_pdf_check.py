#!/usr/bin/env python3
"""EASE 2027 rules checkable only on the built PDF (docs/ease_writing_rules.md, R-98; 0 USD).

  python scripts/ease_pdf_check.py paper/main.pdf

E-F2: "Submissions must not exceed 10 pages for the main text, including all figures, tables,
appendices, etc. Up to two additional pages containing ONLY references are permitted."
Counted conservatively: the page on which the REFERENCES heading starts counts as main text, and
every later page as a reference page.
E-A1: the PDF's Author metadata must be empty (double-anonymous review).
Needs pdftotext and pdfinfo (poppler).
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

MAIN_MAX = 10
REF_MAX = 2


def page_texts(pdf: Path) -> list[str]:
    out = subprocess.run(
        ["pdftotext", str(pdf), "-"], capture_output=True, text=True, check=True
    ).stdout
    pages = out.split("\f")
    return pages[:-1] if pages and not pages[-1].strip() else pages


def ref_start(pages: list[str]) -> int | None:
    """1-based page holding the references heading (acmart prints it in capitals)."""
    for i, t in enumerate(pages, 1):
        if re.search(r"^\s*REFERENCES\s*$", t, re.M):
            return i
    return None


def evaluate(pages: list[str], author: str) -> list[str]:
    bad = []
    r = ref_start(pages)
    if r is None:
        bad.append("E-F2: no REFERENCES heading found")
        main, refs = len(pages), 0
    else:
        main, refs = r, len(pages) - r
    if main > MAIN_MAX:
        bad.append(f"E-F2: main text runs to page {main} (limit {MAIN_MAX})")
    if refs > REF_MAX:
        bad.append(f"E-F2: {refs} pages after the main text (limit {REF_MAX}, references only)")
    if author.strip():
        bad.append(f"E-A1: PDF Author metadata is not empty: {author!r}")
    print(f"pages {len(pages)}; main text to page {main}; reference-only pages {refs}")
    return bad


def pdf_author(pdf: Path) -> str:
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True).stdout
    m = re.search(r"^Author:\s*(.*)$", info, re.M)
    return m.group(1) if m else ""


def main() -> int:
    pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("paper/main.pdf")
    bad = evaluate(page_texts(pdf), pdf_author(pdf))
    for b in bad:
        print("FAIL:", b)
    print("ease pdf:", "PASS" if not bad else "FAIL")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
