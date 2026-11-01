"""Regenerate results/simulation.json (TODO.md section 4 table).

Usage:  python scripts/run_simulations.py [--quick] [--out results/simulation.json]
"""

from __future__ import annotations

import argparse
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from gatekeeper import __version__
from gatekeeper.simulate import simulate

THETA = 0.05
ALPHA_CELL_SMALL = 0.05 / 1600  # 94 skills x 17 scopes (Table 1), Bonferroni
GRID = [
    (-0.25, 0.05),
    (-0.25, ALPHA_CELL_SMALL),
    (-0.15, ALPHA_CELL_SMALL),
    (-0.10, ALPHA_CELL_SMALL),
    (-0.08, ALPHA_CELL_SMALL),
    (-0.05, ALPHA_CELL_SMALL),
]
# Values reported in review v1 (TODO.md section 4), for side-by-side comparison.
REVIEW_V1 = {
    (-0.25, 0.05): (1.00, 52),
    (-0.25, ALPHA_CELL_SMALL): (1.00, 167),
    (-0.15, ALPHA_CELL_SMALL): (1.00, 491),
    (-0.10, ALPHA_CELL_SMALL): (0.64, 1405),
    (-0.08, ALPHA_CELL_SMALL): (0.24, 1361),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="fewer replicates (CI smoke run)")
    ap.add_argument("--out", default="results/simulation.json")
    args = ap.parse_args()

    reps = 100 if args.quick else 1000
    null_reps = 500 if args.quick else 5000
    t0 = time.time()
    rows = []
    for i, (s, a) in enumerate(GRID):
        r = simulate(str_true=s, alpha=a, theta=THETA, reps=reps, budget=2000, seed=1000 + i)
        d = r.to_dict()
        v1 = REVIEW_V1.get((s, a))
        d["review_v1_admit_rate"] = v1[0] if v1 else None
        d["review_v1_median_trials"] = v1[1] if v1 else None
        rows.append(d)
    null = simulate(str_true=-THETA, alpha=0.05, theta=THETA, reps=null_reps, budget=2000, seed=7)

    # Prop. 9 (corrected): unpaired / paired sample-size ratio for the paper's sigma_T^2/sigma_S^2
    ratio_paper = 2.1
    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": "quick" if args.quick else "full",
        "gatekeeper_version": __version__,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "runtime_seconds": round(time.time() - t0, 2),
        "theta": THETA,
        "grid": rows,
        "type_one_check": null.to_dict(),
        "prop9": {
            "sigma_T2_over_sigma_S2": ratio_paper,
            "paper_claim": 1 + ratio_paper,
            "corrected": 1 + 2 * ratio_paper,
        },
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))

    if null.admit_rate > 0.05 + 3 * (0.05 * 0.95 / null_reps) ** 0.5:
        raise SystemExit(f"type-I error too high: {null.admit_rate}")


if __name__ == "__main__":
    main()
