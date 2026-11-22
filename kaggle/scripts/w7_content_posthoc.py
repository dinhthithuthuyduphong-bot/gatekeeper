"""Section 45 (W7-b), note 45-10: POST HOC content count of the G candidate rules (0 USD).

Not registered. Written after the primary test (pool B: 11/12 issues with G, not rejected) and
after reading the rule texts, so it is descriptive and hypothesis-generating only; its p-value is
reported as post hoc and is not a test of section 45.

For each pool, among candidate rules (Stage 1, candidates/<analyst>.jsonl) that carry G
(`git log` or `git show`, as in w7_analyse.G), count the issues having at least one such rule whose
text also matches each feature below. Feature patterns are fixed in this file.

  python kaggle/scripts/w7_content_posthoc.py --run-a <w7_A dir> --run-b <w7_B dir> \
      --out kaggle/results/w7/w7_content_posthoc.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from w7_analyse import G, fisher_greater, jsonl  # noqa: E402

FEATURES = {
    "git_show": re.compile(r"git show", re.IGNORECASE),
    "diff": re.compile(r"diff", re.IGNORECASE),
    "introduced_bug": re.compile(r"bug patch|inject|introduc|regression", re.IGNORECASE),
    "git_status": re.compile(r"git status", re.IGNORECASE),
}


def count(run: Path) -> dict:
    issues = sorted({p["instance_id"] for p in jsonl(run / "pairs" / "pairs.jsonl")})
    hit = {i: set() for i in issues}
    for f in sorted((run / "candidates").glob("*.jsonl")):
        if f.name == "failed.jsonl":
            continue
        for c in jsonl(f):
            text = c.get("rule", "")
            issue = c["pair_id"].split("::")[0]
            if issue not in hit or not G.search(text):
                continue
            hit[issue].add("G")
            hit[issue].update(k for k, p in FEATURES.items() if p.search(text))
    keys = ["G", *FEATURES]
    return {
        "issues": len(issues),
        "issues_with": {k: sum(k in v for v in hit.values()) for k in keys},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-a", required=True, type=Path)
    ap.add_argument("--run-b", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    ra, rb = count(a.run_a), count(a.run_b)
    out = {
        "status": "post hoc, not registered (note 45-10)",
        "features": {k: p.pattern for k, p in FEATURES.items()},
        "A": ra,
        "B": rb,
        "p_one_sided_post_hoc": {
            k: fisher_greater(
                ra["issues_with"][k], ra["issues"], rb["issues_with"][k], rb["issues"]
            )
            for k in ra["issues_with"]
        },
    }
    a.out.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
