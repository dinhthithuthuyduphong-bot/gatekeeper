"""T2b, two-stage retirement (docs/preregistration_main.md section 15). 0 USD.
Writes results/two_stage_retirement.json.

Stage 1: e-SR alarm (Shin et al. Def. 2.12, lambda 0.5, threshold 1/alpha).
Stage 2: on the k-th alarm the skill is quarantined; a FRESH harm e-process on the trials after the
alarm must reach 1/alpha_k within W trials, alpha_k = alpha * 6 / (pi^2 k^2); else the skill is
reinstated and the e-SR restarts.

  python scripts/two_stage_retirement.py --reps 1000
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import lifecycle_plasmode as lp  # noqa: E402
import plasmode_real as pr  # noqa: E402

from gatekeeper.eprocess import BettingEProcess  # noqa: E402

ALPHA = 0.025
LAMBDA = 0.5  # e-SR bet = Gatekeeper bettor c (results/gro_c.json), as T2-1
W = 200  # confirmation window = max trials per cell in section 14
SEED = 20271109
N, CHANGE = 400, 100


def alpha_k(k: int) -> float:
    return ALPHA * 6 / (math.pi**2 * k**2)


def two_stage(z: list[float]) -> tuple[int | None, int]:
    """Returns (retirement trial or None, trials spent in quarantine)."""
    m, k, t, quarantined = 0.0, 0, 0, 0
    while t < len(z):
        m = (1 + LAMBDA * z[t]) * (m + 1)
        t += 1
        if m < 1 / ALPHA:
            continue
        k += 1  # alarm: quarantine and confirm on fresh trials
        ep = BettingEProcess(theta=0.0, alpha=alpha_k(k))
        start = t
        while t < len(z) and t - start < W:
            ep.update(-z[t])  # certifies E[Z] > 0 (harm)
            t += 1
            if ep.crossed:
                return t, quarantined + (t - start)
        quarantined += t - start
        m = 0.0  # reinstated: restart the alarm
    return None, quarantined


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, required=True)
    a = ap.parse_args()
    tasks = pr.no_skill_runs()
    base = float(np.mean([np.mean(t) for t in tasks]))
    rng = np.random.default_rng(SEED)
    out = {"alpha": ALPHA, "lambda": LAMBDA, "W": W, "reps": a.reps}
    for scen, d_after in (("drift", -0.20), ("no_drift", 0.20), ("to_neutral", 0.0)):
        ret, quar = [], []
        for _ in range(a.reps):
            z = lp.drift_stream(rng, tasks, base, N, 0.20, d_after, CHANGE)
            r, q = two_stage(z)
            ret.append(r)
            quar.append(q)
        hits = [r for r in ret if r is not None]
        out[scen] = {
            "retired_share": len(hits) / a.reps,
            "median_delay_after_change": float(np.median([r - CHANGE for r in hits]))
            if hits and scen != "no_drift"
            else None,
            "retired_before_change_share": sum(1 for r in hits if r < CHANGE) / a.reps,
            "mean_quarantine_share_of_trials": float(np.mean(quar)) / N,
        }
        print(scen, out[scen], flush=True)
    Path("results/two_stage_retirement.json").write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
