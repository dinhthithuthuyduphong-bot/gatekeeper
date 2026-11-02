import importlib.util
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location(
    "analyze_g1_final", Path(__file__).parents[1] / "scripts" / "analyze_g1_final.py"
)
gf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gf)

U = 2 / 3  # loss of an unresolved task


def run(skill_losses: dict[str, list[tuple[float, float]]], usd=0.05):
    sk = {
        s: {
            "pairs": [
                {"instance_id": f"t{i}", "loss_with": w, "loss_without": o}
                for i, (w, o) in enumerate(v)
            ]
        }
        for s, v in skill_losses.items()
    }
    n = sum(len(v) for v in skill_losses.values())
    return {"skills": sk, "usage": {"none": {"runs": n, "usd_per_run": usd}}}


def test_sign_flip_exact_and_null():
    assert gf.sign_flip_p([-1.0] * 10) == pytest.approx(1 / 1024)
    assert gf.sign_flip_p([0.0] * 10) == 1.0
    rng = np.random.default_rng(1)
    ps = [
        gf.sign_flip_p(list(rng.choice([-1.0, 0.0, 1.0], 30)), n_mc=5000, seed=i)
        for i in range(200)
    ]
    assert np.mean(np.array(ps) <= 0.05) <= 0.09  # valid under H0 (nominal 0.05)


def test_holm_step_down():
    h = gf.holm({"a": 0.001, "b": 0.02, "c": 0.5}, 0.025)
    assert h["a"]["reject"] and not h["b"]["reject"] and not h["c"]["reject"]
    h2 = gf.holm({"a": 0.004, "b": 0.012}, 0.025)
    assert h2["a"]["reject"] and h2["b"]["reject"]  # 0.004 <= .0125, 0.012 <= .025


def test_tost_and_mde():
    assert gf.tost([0.0] * 30 + [1.0, -1.0] * 5, margin=0.3)["equivalent"]
    assert not gf.tost([1.0] * 20 + [0.0] * 20, margin=0.3)["equivalent"]
    assert gf.mde([1.0, -1.0] * 15, 1) > gf.mde([1.0, -1.0] * 15, 4) * 0.8


def test_select_plan_and_verdict():
    c = run({"good": [(0.0, U)] * 8 + [(U, U)] * 12, "bad": [(U, 0.0)] * 5 + [(0.0, 0.0)] * 15})
    sel = gf.select(c)
    assert [s for s, _, _ in sel] == ["good"]
    skills, m, per_seed = gf.plan_seeds(c, sel, spent=30.0, cap=34.0)
    assert skills == ["good"] and m == int(4.0 // (40 * 0.05))
    confirm = [c, c]
    v = gf.verdict(c, confirm, ["good"])
    assert v["verdict"].startswith("G1 PASS") and v["aa_tost"]["equivalent"]
    none = gf.verdict(c, confirm, [])
    assert none["verdict"].startswith("G1 FAIL")


def test_budget_drops_weakest_skill():
    c = run({"a": [(0.0, U)] * 20, "b": [(0.0, U)] * 20})
    sel = [("a", -0.5, 20), ("b", -0.2, 20)]
    # both: 20 no-skill + 40 skill runs = 60 x 0.05 = 3 USD per seed; a alone: 40 x 0.05 = 2 USD
    assert gf.plan_seeds(c, sel, spent=30.0, cap=34.0)[:2] == (["a", "b"], 1)
    assert gf.plan_seeds(c, sel, spent=31.5, cap=34.0)[:2] == (["a"], 1)
    assert gf.plan_seeds(c, sel, spent=33.0, cap=34.0)[:2] == ([], 0)
