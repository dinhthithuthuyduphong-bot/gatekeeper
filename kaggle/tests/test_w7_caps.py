"""kaggle/scripts/w7_caps.py: merge cost fit and the simulated spend (note 45-5)."""

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import w7_caps  # noqa: E402


def test_fit_recovers_a_line():
    a, b = w7_caps.fit([(1, 0.012), (2, 0.014), (12, 0.034)])
    assert abs(a - 0.010) < 1e-12 and abs(b - 0.002) < 1e-12


def test_simulation_counts_every_stage():
    m = {
        "slots": {"A-": [(0.1, 1)], "A+": [(0.2, 0)], "A_diff": [(0.3, 2)]},
        "categories": ["lookup"],
        "merge": [(1, 0.01), (3, 0.03)],  # a = 0, b = 0.01
        "judge": [0.005],
    }
    tots = w7_caps.simulate(m, pairs=2, cands_so_far=0, reps=3, rng=random.Random(1))
    # discover 2 * 0.6; 6 candidates: one merge call of 6 (0.06) and 6 judge calls (0.03)
    assert all(abs(t - (1.2 + 0.06 + 0.03)) < 1e-12 for t in tots)
