"""Section 38: size and power of the registered primary test (L11), 0 USD.

Simulates the exact decision rule of a38_analyse.py (one-sided exact permutation p over the 6 leak
and 7 no-leak calls, 3 seeds per call) under per-seed Bernoulli outcomes, and reports the share of
rejections at the registered family level 0.025 and at the strictest Holm step 0.025 / 4.

  python kaggle/scripts/a38_power.py --reps 2000 --seed 38 --out kaggle/results/a38_power.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import a38_analyse as an  # noqa: E402

SCENARIOS = [(0.9, 0.1), (0.8, 0.2), (0.7, 0.3), (0.6, 0.4), (0.9, 0.5), (0.5, 0.5), (0.2, 0.2)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", required=True, type=int)
    ap.add_argument("--seed", required=True, type=int)
    ap.add_argument("--alpha", required=True, type=float)
    ap.add_argument("--k", required=True, type=int, help="cross-vendor models in the Holm family")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    out = {"reps": a.reps, "alpha": a.alpha, "k": a.k, "calls": [6, 7], "seeds": 3, "rows": []}
    for pl, pn in SCENARIOS:
        ps = [
            an.perm_p(list(rng.binomial(3, pl, 6) / 3), list(rng.binomial(3, pn, 7) / 3))
            for _ in range(a.reps)
        ]
        out["rows"].append(
            {
                "p_leak": pl,
                "p_noleak": pn,
                "reject_at_alpha": float(np.mean([p <= a.alpha for p in ps])),
                "reject_at_alpha_over_k": float(np.mean([p <= a.alpha / a.k for p in ps])),
            }
        )
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
