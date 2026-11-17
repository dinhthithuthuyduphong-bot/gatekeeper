import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import c10_stop_audit as sa  # noqa: E402


def _arm(costs, solved, cap, n_tasks=4, cost_limit=0.3):
    runs = [
        {"instance_id": f"t{i}", "cost_usd": c, "S": {"resolved": s}}
        for i, (c, s) in enumerate(zip(costs, solved, strict=True))
    ]
    return {
        "runs": runs,
        "n_tasks": n_tasks,
        "cap": cap,
        "cost_limit": cost_limit,
        "spent_usd": sum(costs),
    }


def test_guard_replay_flags_a_run_started_past_the_cap():
    ok = sa.guard_replay(_arm([0.1, 0.1], [0, 0], cap=0.45))
    assert ok["stop_explained_by_guard"] and ok["runs_started_after_guard"] == 0
    bad = sa.guard_replay(_arm([0.1, 0.1, 0.1], [0, 0, 0], cap=0.45))
    assert bad["runs_started_after_guard"] == 1


def test_contrast_uses_shortest_prefix_and_fixed_pool():
    full = [0.01] * 4
    arms = {}
    for v in "ABCD":
        arms[f"{v}_none"] = _arm(full, [0] * 4, cap=9)
        arms[f"{v}_skill"] = _arm(full, [1 if v == "A" else 0] * 4, cap=9)
    arms["C_none"] = _arm(full[:3], [0] * 3, cap=0.32)
    res = sa.audit(arms, lam=0.5, theta=0.0, threshold=40, n_fixed=2)
    m = res["contrasts"]["main A-C"]
    assert m["n"] == 3 and m["set_by_arm"] == "C_none"
    assert m["E_at_n"] == pytest.approx(1.25**3)
    assert m["E_on_first_2"] == pytest.approx(1.25**2)
    assert all(a["prefix_of_task_order"] for a in res["arms"].values())
