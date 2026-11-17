import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import c10r_caps as cc  # noqa: E402


def test_constant_costs_give_total_plus_cost_limit_rounded_up():
    later = [0.02] * 10
    costs = {"x": [0.01] * 3 + later, "y": [0.01] * 3}  # y: later costs scaled by x's ratio (2)
    caps, detail, ratio = cc.caps(
        costs, n_tasks=13, split=3, quantile=0.999, reps=50, seed=1, cost_limit=0.30
    )
    assert abs(ratio - 2.0) < 1e-9
    assert caps["x"] == round(0.03 + 0.20 + 0.30, 3)
    assert caps["y"] == round(0.03 + 0.20 + 0.30, 3)
    assert detail["y"]["later_costs"].startswith("earlier x")


def test_cap_is_rounded_up():
    costs = {"x": [0.0011] * 3 + [0.0011] * 10}
    caps, _, _ = cc.caps(costs, n_tasks=13, split=3, quantile=0.5, reps=5, seed=1, cost_limit=0.3)
    assert caps["x"] == 0.315  # 0.0143 + 0.3 = 0.3143 -> 0.315
