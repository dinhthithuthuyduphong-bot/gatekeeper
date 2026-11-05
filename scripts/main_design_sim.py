"""Design simulation for the main experiment (docs/preregistration_main_draft.md section 4).

For each RQ1 cell: the Gatekeeper e-process (gatekeeper.eprocess.run_admission, theta = 0,
alpha_cell = 0.025 / K) is run on a trial sequence that CONTINUES the cell's E1/E2 trials:
  - first n0 trials: per-task mean Z over 3 seeds (as E1/E2 produce them),
  - then new trials: Z of ONE run per new task (the main experiment's new part).
Per-task solve probability q of the NO-SKILL arm is resampled from the measured values (E2: Live,
results/e2; E1 cells: the E1 extension, 37 tasks x 3 seeds); the skill arm never enters (L28).
Effect model as scripts/verify_methods.py: q' = min(1, q + delta). delta <= 0: harmful / null cell
(validity: admission rate must be <= alpha_cell). Reports P(admit within n0 + b new trials) for a
grid of b, capped by the tasks a cell can still draw. Writes results/main_design_sim.json.
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import e2_power_live_q as live  # noqa: E402

from gatekeeper.eprocess import run_admission  # noqa: E402

ALPHA_FAMILY = 0.025  # one-sided (ICH E9; preregistration D2)
K = 9  # cells registered: 3 E1 skills, 3 harmful controls, xreposkill, positive control, memgovern
COST_PER_NEW_TRIAL = 0.13  # USD: 2 arms x 1 run x 0.064 measured (E1 0.0645, E2 0.063)
CELLS = {
    # name: (q source, n0 continuation trials, max tasks available in total for the cell)
    "xreposkill": ("e2", 109, 1100),
    # E1 cells: activated tasks in the E1 frame (configs/pools/e1.json random_order: 221 / 118 / 89)
    # x usable rate measured on the E1 pool (204/216); was taken from data/activation.json (A70)
    "type-guard": ("e1x", 53, 209),
    "exception-handling": ("e1x", 53, 111),
    "null-guard": ("e1x", 53, 84),
}
DELTAS = [-0.05, 0.0, 0.05, 0.109, 0.15]
BUDGETS = [0, 31, 50, 58, 100, 156, 200, 300, 500, 800]
REPS = 400  # operational: MCSE <= sqrt(0.25/400) = 0.025 for an admission probability


def admit_index(z: np.ndarray, alpha: float) -> int | None:
    r = run_admission(list(z), 0.0, alpha, budget=len(z))
    return r.n_trials if r.admitted else None


def main() -> int:
    q_src = {
        "e2": np.array(
            list(live.none_q(sorted(glob.glob("results/e2/g2-e2-s*-k*-p*.json"))).values())
        ),
        "e1x": np.array(
            list(live.none_q(sorted(glob.glob("results/pilot/g1-e1x-s*-p*.json"))).values())
        ),
    }
    rng = np.random.default_rng(20271104)
    a_cell = ALPHA_FAMILY / K
    out: dict = {
        "alpha_cell": a_cell,
        "K": K,
        "cost_per_new_trial_usd": COST_PER_NEW_TRIAL,
        "q": {k: {"n": int(v.size), "mean": float(v.mean())} for k, v in q_src.items()},
        "cells": {},
    }
    for name, (src, n0, n_max) in CELLS.items():
        q = q_src[src]
        new_max = max(0, n_max - n0)
        res = {}
        for d in DELTAS:
            hits = []
            for _ in range(REPS):
                qi = rng.choice(q, size=n0 + new_max, replace=True)
                qs = np.clip(qi + d, 0.0, 1.0)
                z0 = (
                    (rng.random((n0, 3)) >= qs[:n0, None]).astype(float)
                    - (rng.random((n0, 3)) >= qi[:n0, None]).astype(float)
                ).mean(axis=1)
                z1 = (rng.random(new_max) >= qs[n0:]).astype(float) - (
                    rng.random(new_max) >= qi[n0:]
                ).astype(float)
                assert z0.shape == (n0,) and z1.shape == (new_max,)  # review R-6
                hits.append(admit_index(np.concatenate([z0, z1]), a_cell))
            res[str(d)] = {
                str(b): float(np.mean([h is not None and h <= n0 + b for h in hits]))
                for b in BUDGETS
                if b <= new_max
            }
            print(name, d, res[str(d)], flush=True)
        out["cells"][name] = {"n0": n0, "new_max": new_max, "admit_prob": res}
    Path("results/main_design_sim.json").write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
