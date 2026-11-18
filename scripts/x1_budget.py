"""Cumulative money guard of sections 46-47 (docs/plan_vs_review.md section 11.3). 0 USD.

Spent so far = for each learning tag, the largest `spent_total` over its ledgers (the second half
carries the first half's spend as spent_before), plus `spent_usd` of every probe result file of
sections 46-47. Exit 0 only when spent + the next step's cap <= the approved cumulative cap.

  python scripts/x1_budget.py --dir <results dir> --next-cap 14.5 --total 38.96
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

LEARN_TAGS = ("x1ship", "x1lf")
PROBE_PREFIXES = ("x2_", "x1eval_")


def spent(folder: Path) -> dict:
    learn = {}
    for tag in LEARN_TAGS:
        totals = [
            float(json.loads(p.read_text())["spent_total"])
            for p in folder.glob(f"{tag}_learn_ledger_h*.json")
        ]
        learn[tag] = max(totals) if totals else 0.0
    probes = {
        p.name: float(json.loads(p.read_text()).get("spent_usd") or 0.0)
        for p in sorted(folder.glob("*.json"))
        if p.name.startswith(PROBE_PREFIXES) and not p.name.endswith((".cost.json",))
    }
    return {"learn": learn, "probes": probes, "total": sum(learn.values()) + sum(probes.values())}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, type=Path)
    ap.add_argument("--next-cap", required=True, type=float)
    ap.add_argument("--total", required=True, type=float)
    a = ap.parse_args()
    s = spent(a.dir)
    ok = s["total"] + a.next_cap <= a.total + 1e-9
    print(json.dumps({**s, "next_cap": a.next_cap, "approved_total": a.total, "ok": ok}, indent=1))
    return 0 if ok else 4


if __name__ == "__main__":
    raise SystemExit(main())
