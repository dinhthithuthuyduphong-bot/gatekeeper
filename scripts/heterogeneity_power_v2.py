"""Corrected power check for section 18 (deviation D-M8, audit A80). 0 USD.
Writes results/heterogeneity_power_v2.json.

The registered check (execution note 18-2) planted effects around the *sample* mean of three
no-skill runs, so its "true" tau^2 was not the quantity the estimator targets (A80). Here both
arms are simulated from per-task solve probabilities p_i ~ Beta(a, b), with (a, b) fitted by the
method of moments to the beta-binomial counts of E2's no-skill runs, and
p_with_i = clip(p_i + delta_i, 0, 1), delta_i ~ N(0, tau^2). Truth = Var_i(p_with_i - p_i).
Same estimator, CI and consistency test as H18.

  python scripts/heterogeneity_power_v2.py --reps 1000 --null-reps 1000 --boot 1000
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import replicate_attribution as ra  # noqa: E402

SEED = 20271112


def beta_mom(k: np.ndarray, n: int) -> tuple[float, float]:
    """Method-of-moments fit of a beta-binomial (counts k out of n per task)."""
    mu = k.mean() / n
    rho = (k.var() / (n * mu * (1 - mu)) - 1) / (n - 1)
    if not 0 < rho < 1:
        raise SystemExit(f"beta-binomial moment fit failed: rho = {rho}")
    s = 1 / rho - 1
    return mu * s, (1 - mu) * s


def simulate(rng, a: float, b: float, n_tasks: int, tau: float):
    p = rng.beta(a, b, n_tasks)
    pw = np.clip(p + rng.normal(0, tau, n_tasks), 0, 1)
    k = len(ra.SEEDS)
    none = (rng.random((n_tasks, k)) < p[:, None]).astype(float)  # 1 = resolved
    withs = (rng.random((n_tasks, k)) < pw[:, None]).astype(float)
    M = (1 - withs) - (1 - none)
    return M, float(np.var(pw - p, ddof=1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, required=True)
    ap.add_argument("--null-reps", type=int, required=True)
    ap.add_argument("--boot", type=int, required=True)
    args = ap.parse_args()
    e2 = ra.load("e2")["xreposkill"]
    _, ids = ra.zmatrix(e2)
    k = np.array([sum(e2[i][s][1] for s in ra.SEEDS) for i in ids], float)
    a, b = beta_mom(k, len(ra.SEEDS))
    rng = np.random.default_rng(SEED)
    out = {"beta": [a, b], "n_tasks": len(ids), "args": vars(args), "taus": {}}
    for tau in ra.POWER_TAUS:
        rej = cover = 0
        upper_below = []
        for _ in range(args.reps):
            M, truth = simulate(rng, a, b, len(ids), tau)
            c = ra.consistency(M)
            rej += (ra.signflip_null(M, args.null_reps, rng) >= c).mean() <= 0.05
            lo, hi = ra.boot_ci(ra.tau2_mom, M, None, args.boot, rng)
            cover += lo <= truth <= hi
            upper_below.append(hi < 0.15**2)
        out["taus"][str(tau)] = {
            "H18_1_rejection_rate": rej / args.reps,
            "tau2_ci_coverage": cover / args.reps,
            "share_upper_bound_below_0.15sq": float(np.mean(upper_below)),
        }
        print(tau, out["taus"][str(tau)], flush=True)
    Path("results/heterogeneity_power_v2.json").write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
