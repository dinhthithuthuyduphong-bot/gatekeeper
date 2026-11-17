"""Section 38, note 38-7 (post hoc, descriptive, 0 USD): the same saved prompt answered by the
original learning run (Vertex AI, called from the GitHub workflow) and by the reference model on
Kaggle. Only prompts sent to Kaggle byte-for-byte as saved count (no parent line removed).

  python kaggle/scripts/a38_platform_check.py --prompts kaggle/data/a38_prompts.jsonl.gz \
      --results kaggle/results/a38_results_2026111*.jsonl \
      --model google/gemini-3.1-pro-preview --out kaggle/results/a38_platform_check.json
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import a38_analyse as an


def check(prompts: list[dict], results: list[dict], model: str) -> dict:
    by_sha: dict[str, list[bool]] = {}
    for r in an.dedupe(results):
        if r["model"] == model and r.get("ok"):
            by_sha.setdefault(r["sha256"], []).append(an.has(an.RULE, r["new_skills"]))
    rows, seen = [], set()
    for p in prompts:
        if p["parent_lines_removed"] or p["sha256"] in seen or p["sha256"] not in by_sha:
            continue
        seen.add(p["sha256"])
        k = by_sha[p["sha256"]]
        rows.append(
            {
                "pid": p["pid"],
                "condition": p["condition"],
                "original_H": p["original_child_has_history_line"],
                "kaggle_H": sum(k),
                "kaggle_n": len(k),
            }
        )
    cells: dict[str, dict] = {}
    for r in rows:
        c = cells.setdefault(
            r["condition"], {"calls": 0, "original_share": 0.0, "kaggle_share": 0.0}
        )
        c["calls"] += 1
        c["original_share"] += r["original_H"]
        c["kaggle_share"] += r["kaggle_H"] / r["kaggle_n"]
    for c in cells.values():
        c["original_share"] /= c["calls"]
        c["kaggle_share"] /= c["calls"]
    return {
        "model": model,
        "prompts": len(rows),
        "seed_level_agreement": [
            sum(r["kaggle_H"] if r["original_H"] else r["kaggle_n"] - r["kaggle_H"] for r in rows),
            sum(r["kaggle_n"] for r in rows),
        ],
        "majority_agreement": [
            sum((2 * r["kaggle_H"] > r["kaggle_n"]) == r["original_H"] for r in rows),
            len(rows),
        ],
        "cells": cells,
        "rows": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", required=True, type=Path)
    ap.add_argument("--results", required=True, type=Path, nargs="+")
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    prompts = [json.loads(x) for x in gzip.open(a.prompts, "rt")]
    results = [json.loads(x) for f in a.results for x in f.read_text().splitlines() if x.strip()]
    res = check(prompts, results, a.model)
    a.out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
