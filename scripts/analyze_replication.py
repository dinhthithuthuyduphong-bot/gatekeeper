"""Pre-registered G1 verdict from 3 seeds (docs/preregistration_g1_v2.md, addendum 2).

Usage: python scripts/analyze_replication.py --skill null-guard --runs g1-c g1-c-s11 g1-c-s21
Per task: Z = mean over seeds of loss(skill) - loss(none) (pairs within the same seed). Pass iff
the pooled mean Z <= -effect AND the upper bound of the Bonferroni-adjusted CI (1 - 0.15/k
two-sided, k = number of screened skills) is < 0. Writes results/g1_replication_<skill>.json.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from gatekeeper.analysis import mean_ci


def pooled_z(runs: list[dict], skill: str) -> dict[str, list[float]]:
    per_task: dict[str, list[float]] = defaultdict(list)
    for run in runs:
        for p in run.get("skills", {}).get(skill, {}).get("pairs", []):
            per_task[p["instance_id"]].append(p["loss_with"] - p["loss_without"])
    return dict(per_task)


def verdict(per_task: dict[str, list[float]], effect: float = 0.10, k: int = 4, n_seeds: int = 3):
    complete = {t: z for t, z in per_task.items() if len(z) >= n_seeds}
    z = [sum(v) / len(v) for v in complete.values()]
    level = 1 - 0.15 / k
    m, lo, hi = mean_ci(z, level=level)
    ok = m is not None and m <= -effect and hi < 0
    return {
        "n_tasks": len(z),
        "n_incomplete": len(per_task) - len(complete),
        "mean_z": m,
        "ci": [lo, hi],
        "ci_level": level,
        "pass": bool(ok),
        "verdict": "G1 PASS" if ok else "not passed",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", required=True)
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--effect", type=float, default=0.10)
    ap.add_argument("--k", type=int, default=4, help="skills screened in stage C (Bonferroni)")
    a = ap.parse_args()
    runs = [json.loads(Path(f"results/pilot/{r}.json").read_text()) for r in a.runs]
    out = verdict(pooled_z(runs, a.skill), a.effect, a.k, len(a.runs))
    out.update(skill=a.skill, runs=a.runs)
    Path(f"results/g1_replication_{a.skill}.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
