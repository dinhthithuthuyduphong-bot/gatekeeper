"""Cross-check our e-process against confseq's betting confidence sequence (TODO.md R1).

confseq works with observations in [0, 1], so we map Y = (Z + 1) / 2. The null
E[Z] >= -theta becomes E[Y] >= m0 = (1 - theta) / 2; confseq "admits" when the upper end of its
time-uniform CS drops below m0. The two bettors differ, so decisions need not coincide trial by
trial; we check that both control type-I error and both admit a clearly beneficial skill.

Writes results/confseq_crosscheck.json. Prints confseq's API on failure so CI logs are
actionable.
"""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import numpy as np

from gatekeeper.eprocess import run_admission

THETA, ALPHA, N = 0.05, 0.05, 600


def _draws(str_true: float, reps: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    p_plus = 0.10
    p_minus = p_plus - str_true
    return rng.choice([-1.0, 0.0, 1.0], size=(reps, N), p=[p_minus, 1 - p_plus - p_minus, p_plus])


def main() -> int:
    try:
        from confseq import betting
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"confseq import failed: {exc!r}")
        return 1

    print("confseq.betting members:", [m for m in dir(betting) if not m.startswith("_")])
    fn = getattr(betting, "betting_cs", None)
    if fn is None:
        print("betting_cs not found")
        return 1
    print("betting_cs signature:", inspect.signature(fn))

    m0 = (1 - THETA) / 2
    out = {}
    for label, s, reps in [("boundary_null", -THETA, 100), ("strong_skill", -0.25, 30)]:
        z = _draws(s, reps, seed=11)
        ours = [run_admission(row, THETA, ALPHA, N).admitted for row in z]
        theirs = []
        for row in z:
            y = (row + 1.0) / 2.0
            _lower, upper = fn(y, alpha=ALPHA)
            theirs.append(bool(np.min(upper) < m0))
        out[label] = {
            "str_true": s,
            "reps": reps,
            "ours_admit_rate": float(np.mean(ours)),
            "confseq_admit_rate": float(np.mean(theirs)),
            "agreement": float(np.mean(np.array(ours) == np.array(theirs))),
        }
        print(label, out[label])

    Path("results").mkdir(exist_ok=True)
    Path("results/confseq_crosscheck.json").write_text(json.dumps(out, indent=2) + "\n")

    ok = (
        out["boundary_null"]["ours_admit_rate"] <= 0.15
        and out["boundary_null"]["confseq_admit_rate"] <= 0.15
        and out["strong_skill"]["ours_admit_rate"] == 1.0
        and out["strong_skill"]["confseq_admit_rate"] >= 0.9
    )
    print("CROSSCHECK", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
