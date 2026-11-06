"""Section 27b: how much of a skill's effect carries over between SWE-Skills-Bench configurations.
Exploratory (the point values were seen before, results/sskb_transfer_power.json). Free.

  python scripts/sskb_transfer.py

rho = mean pairwise covariance of skill effects across the 4 published configurations / mean
within-configuration variance (98 common skills; effect = mean over batches of delta_pp). Sign
agreement: among (configuration, skill) with |effect| >= 6 pp, the share of the other
configurations with the same sign and |effect| >= 6 pp, and with the opposite sign. Skill-level
bootstrap, 10,000 resamples. Writes results/sskb_transfer.json.
"""

from __future__ import annotations

import csv
import itertools
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

SRC = Path("data/external/swe-skills-bench/ALL_combined_cells.csv")
N_BOOT = 10_000
SEED = 2727
THR = 6.0  # pp; the section 23b selection mark, fixed before section 27


def effects() -> tuple[list[str], np.ndarray]:
    d: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    with SRC.open() as f:
        for r in csv.DictReader(f):
            d[r["harness_model"]][r["skill"]].append(float(r["delta_pp"]))
    cfgs = sorted(d)
    skills = sorted(set.intersection(*(set(d[c]) for c in cfgs)))
    return cfgs, np.array([[np.mean(d[c][s]) for c in cfgs] for s in skills])  # skills x cfgs


def stats(e: np.ndarray) -> dict[str, float]:
    k = e.shape[1]
    cov = np.cov(e, rowvar=False)
    off = cov[~np.eye(k, dtype=bool)].mean()
    within = np.diag(cov).mean()
    same = opp = n = 0
    for a, b in itertools.permutations(range(k), 2):
        big = np.abs(e[:, a]) >= THR
        n += big.sum()
        same += (big & (np.sign(e[:, b]) == np.sign(e[:, a])) & (np.abs(e[:, b]) >= THR)).sum()
        opp += (big & (np.sign(e[:, b]) == -np.sign(e[:, a])) & (np.abs(e[:, b]) >= THR)).sum()
    return {
        "rho": float(off / within),
        "mean_cross_cov": float(off),
        "mean_within_var": float(within),
        "same_sign_big": float(same / n) if n else float("nan"),
        "opposite_sign_big": float(opp / n) if n else float("nan"),
        "n_big": int(n),
    }


def main() -> int:
    cfgs, e = effects()
    pt = stats(e)
    rng = np.random.default_rng(SEED)
    boots = [stats(e[rng.integers(0, e.shape[0], e.shape[0])]) for _ in range(N_BOOT)]
    ci = {
        k: [float(np.nanquantile([b[k] for b in boots], q)) for q in (0.025, 0.975)]
        for k in ("rho", "same_sign_big", "opposite_sign_big")
    }
    out = {"configs": cfgs, "n_skills": int(e.shape[0]), "point": pt, "ci95": ci, "thr_pp": THR}
    Path("results/sskb_transfer.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
