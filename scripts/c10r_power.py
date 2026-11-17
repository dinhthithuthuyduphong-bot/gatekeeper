"""Power and size of the C10 replication main test (docs/preregistration_main.md section 44;
0 USD), with the rule of section 43 (end-of-pool test, lam 0.5, theta 0, reject when E >= 40) on
the fixed pool of 70 tasks.

  python scripts/c10r_power.py --out results/c10r_power.json

Scenarios (tasks resampled with replacement from the first C10 run, section 43):
  as_first_run : D_i drawn from the A - C differences of the 45 tasks complete in the first run
  half         : as above, each D_i < 0 set to 0 with probability 1/2
  null         : A and C drawn independently from the same per-arm solve rates (A's, pooled)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

R = Path(__file__).resolve().parents[1] / "results"
LAM, THRESHOLD, REPS, SEED, N = 0.5, 40.0, 20000, 4403, 70


def fails(f: str) -> list[int]:
    return [
        int(not (r.get("S") or {}).get("resolved")) for r in json.loads((R / f).read_text())["runs"]
    ]


def reject(d: np.ndarray) -> float:
    return float((np.log1p(LAM * (-d)).sum(axis=1) >= np.log(THRESHOLD)).mean())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    f = {k: fails(f"c10_{k}_all70.json") for k in ("A_skill", "A_none", "C_skill", "C_none")}
    n = min(len(v) for v in f.values())
    d = np.array(
        [
            ((f["A_skill"][i] - f["A_none"][i]) - (f["C_skill"][i] - f["C_none"][i])) / 2
            for i in range(n)
        ]
    )
    p_skill = 1 - float(np.mean(f["A_skill"][:n]))
    p_none = 1 - float(np.mean(f["A_none"][:n]))
    rng = np.random.default_rng(SEED)
    x = rng.choice(d, size=(REPS, N), replace=True)
    h = np.where((x < 0) & (rng.random(x.shape) < 0.5), 0.0, x)

    def z(shape):
        return (rng.random(shape) >= p_skill).astype(float) - (rng.random(shape) >= p_none)

    out = {
        "lam": LAM,
        "threshold": THRESHOLD,
        "reps": REPS,
        "seed": SEED,
        "n_pool": N,
        "first_run": {"n": n, "n_negative": int((d < 0).sum()), "n_positive": int((d > 0).sum())},
        "solve_rate_A_first_run": {"skill": p_skill, "none": p_none},
        "rejection_rate": {
            "as_first_run": reject(x),
            "half": reject(h),
            "null": reject((z((REPS, N)) - z((REPS, N))) / 2),
        },
    }
    a.out.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
