"""Positive-control cell (oracle file hint) for the main experiment: admission probability of the
Gatekeeper e-process vs number of trials, started from zero (no continuation), one run per task,
on the measured Live no-skill solve rates (results/e2, no-skill arm only, L28). alpha_cell =
0.025 / 8 (K = 7 cells + this one). Same effect model as scripts/verify_methods.py. The hint's real
effect is unknown, so power is reported over a grid of delta. Writes results/pc_design_sim.json."""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import e2_power_live_q as live  # noqa: E402

from gatekeeper.eprocess import run_admission  # noqa: E402

ALPHA_CELL = 0.025 / 8
DELTAS = [0.0, 0.109, 0.15, 0.2, 0.3]
BUDGETS = [25, 50, 100, 150, 200, 300]
REPS = 400  # operational: MCSE <= 0.025


def main() -> int:
    q = np.array(list(live.none_q(sorted(glob.glob("results/e2/g2-e2-s*-k*-p*.json"))).values()))
    rng = np.random.default_rng(20271105)
    n = max(BUDGETS)
    out = {"alpha_cell": ALPHA_CELL, "q_mean": float(q.mean()), "admit_prob": {}}
    for d in DELTAS:
        hits = []
        for _ in range(REPS):
            qi = rng.choice(q, size=n, replace=True)
            qs = np.clip(qi + d, 0.0, 1.0)
            z = (rng.random(n) >= qs).astype(float) - (rng.random(n) >= qi).astype(float)
            r = run_admission(list(z), 0.0, ALPHA_CELL, budget=n)
            hits.append(r.n_trials if r.admitted else None)
        out["admit_prob"][str(d)] = {
            str(b): float(np.mean([h is not None and h <= b for h in hits])) for b in BUDGETS
        }
        print(d, out["admit_prob"][str(d)], flush=True)
    Path("results/pc_design_sim.json").write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
