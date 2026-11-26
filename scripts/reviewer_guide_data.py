#!/usr/bin/env python3
"""Tables of the paper as plain text, for the reviewer reading guide (R-105; 0 USD).

AI review tools read the PDF through text extraction, which merges superscripts into numbers,
drops glyphs and misaligns two-column tables; several reviews reported errors that the rendered
PDF does not contain. This script resolves every table of paper/main.tex with the generated macros
of paper/numbers.tex (the same values the PDF prints) and writes them as JSON:

  python scripts/reviewer_guide_data.py --out <file.json>

Nothing is typed by hand: each cell is the LaTeX cell with macros substituted.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
TEX = Path("paper/main.tex")
NUMS = Path("paper/numbers.tex")


def macros() -> dict[str, str]:
    out = {}
    for m in re.finditer(r"\\newcommand\{\\(n\w+)\}\{(.*)\}", NUMS.read_text()):
        out[m.group(1)] = m.group(2)
    # model names are macros of the paper's preamble (e.g. \\nanomodel)
    for m in re.finditer(r"\\newcommand\{\\(\w+model)\}\{(.*)\}", TEX.read_text()):
        out[m.group(1)] = m.group(2).replace("~", " ")
    return out


def plain(t: str, mac: dict[str, str]) -> str:
    """LaTeX cell -> readable text."""
    t = re.sub(r"\\([a-z][A-Za-z]+)(\{\})?", lambda m: mac.get(m.group(1), m.group(0)), t)
    # section references print as numbers in the PDF (R-107)
    secs = {
        "sec:certified": "3",
        "sec:gain": "4.1",
        "sec:mechanism": "4.2",
        "sec:measurement": "4.7",
    }
    t = re.sub(r"\\ref\{([^}]*)\}", lambda m: secs.get(m.group(1), "(see the paper)"), t)
    t = re.sub(r"\\ensuremath\{([^}]*)\}", r"\1", t)
    t = re.sub(r"\\times10\^\{(-?\d+)\}", r" × 10^\1", t)
    t = re.sub(r"\\multicolumn\{\d+\}\{\w\}\{(.*)\}", r"\1", t)
    t = re.sub(r"\$\^\{(\w)\}\$", r" [note \1]", t)
    reps = {
        r"\to": "→",
        r"\geq": "≥",
        r"\ge": "≥",
        r"\pm": "±",
        r"\theta": "θ",
        r"\lambda": "λ",
        r"\alpha": "α",
        "--": "–",
        r"\%": "%",
        r"\,": " ",
        "~": " ",
        r"\ ": " ",
        r"\_": "_",
    }
    t = t.replace("``", "\u201c").replace("''", "\u201d").replace("\\\\[2pt]", " ")
    for a, b in reps.items():
        t = t.replace(a, b)
    t = re.sub(r"\\(texttt|emph|textbf|mathrm|text)\{([^}]*)\}", r"\2", t)
    t = re.sub(r"\$([^$]*)\$", r"\1", t)
    t = t.replace("{", "").replace("}", "")
    t = re.sub(r"_(\w)", r"_\1", t)
    return " ".join(t.split())


def tables(src: str, mac: dict[str, str]) -> list[dict]:
    out = []
    for m in re.finditer(r"\\begin\{table\*?\}(.*?)\\end\{table\*?\}", src, re.S):
        body = m.group(1)
        label = re.search(r"\\label\{([^}]*)\}", body)
        cap = re.search(r"\\caption\{(.*?)\}\s*\\label", body, re.S) or re.search(
            r"\\caption\{(.*?)\}\n", body, re.S
        )
        tab = re.search(
            r"\\begin\{tabular\}\{(?:[^{}]|\{[^{}]*\})*\}(.*?)\\end\{tabular\}", body, re.S
        )
        if not (label and tab):
            continue
        rows = []
        for line in re.split(r"\\\\", tab.group(1)):
            line = re.sub(r"\\(toprule|midrule|bottomrule)", "", line).strip()
            if not line or "&" not in line:
                continue
            rows.append([plain(c, mac) for c in line.split("&")])
        notes = body[tab.end() :]
        out.append(
            {
                "label": label.group(1),
                "caption": plain(cap.group(1), mac) if cap else "",
                "header": rows[0],
                "rows": rows[1:],
                "notes": plain(re.sub(r"\\(raggedright|footnotesize)", "", notes), mac),
            }
        )
    return out


def layout(pdf: Path) -> dict:
    """Page facts read from the built PDF (R-110: never typed into the guide by hand)."""
    import ease_pdf_check as ep

    pages = ep.page_texts(pdf)
    ref = ep.ref_start(pages)
    return {"pages": len(pages), "main_to": ref, "ref_only_after": len(pages) - ref}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    mac = macros()
    src = TEX.read_text()
    data = {"tables": tables(src, mac), "macros": mac, "layout": layout(Path("paper/main.pdf"))}
    left = sorted(
        {
            r
            for t in data["tables"]
            for row in t["rows"]
            for r in re.findall(r"\\n\w+", " ".join(row))
        }
    )
    if left:
        raise SystemExit(f"unresolved macros: {left}")
    a.out.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps([[t["label"], len(t["rows"])] for t in data["tables"]]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
