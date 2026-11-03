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


def test_sign_flip_is_exact():
    assert gf.sign_flip_p([-1.0] * 10) == pytest.approx(1 / 1024)
    assert gf.sign_flip_p([0.0] * 10) == 1.0
    # brute force over all 2^n sign patterns agrees with the convolution
    import itertools

    x = [-1.0, -2 / 3, 1 / 3, 0.0, -1 / 3, 1.0, -1.0, 2 / 3]
    obs = sum(x)
    pats = list(itertools.product((1, -1), repeat=len(x)))
    brute = sum(sum(s * abs(v) for s, v in zip(p, x, strict=True)) <= obs + 1e-12 for p in pats)
    assert gf.sign_flip_p(x) == pytest.approx(brute / len(pats))
    two = sum(
        abs(sum(s * abs(v) for s, v in zip(p, x, strict=True))) >= abs(obs) - 1e-12 for p in pats
    )
    assert gf.sign_flip_p(x, two_sided=True) == pytest.approx(two / len(pats))


def test_exact_test_is_valid_under_h0():
    rng = np.random.default_rng(1)
    ps = [gf.sign_flip_p(list(rng.choice([-1.0, 0.0, 1.0], 30))) for _ in range(400)]
    assert np.mean(np.array(ps) <= 0.05) <= 0.075  # exact test: size <= nominal (+ MC noise)


def test_holm_step_down():
    h = gf.holm({"a": 0.001, "b": 0.02, "c": 0.5}, 0.025)
    assert h["a"]["reject"] and not h["b"]["reject"] and not h["c"]["reject"]
    h2 = gf.holm({"a": 0.004, "b": 0.012}, 0.025)
    assert h2["a"]["reject"] and h2["b"]["reject"]


def test_interval_and_critical_effect_derive_from_alpha():
    x = [1.0, -1.0, 0.0] * 10
    lo, hi = gf.t_interval(x)
    assert lo < 0 < hi and gf.CI_LEVEL == pytest.approx(0.95)
    assert gf.critical_effect(x, 4) > gf.critical_effect(x, 1) > 0
    # consistency with the exact test: observing exactly the critical effect is significant
    n = 30
    crit = gf.critical_effect([1.0] * n, 1)  # |Z| = 1 for all tasks
    k = round(crit * n)  # net number of helped tasks needed
    obs = [-1.0] * ((n + k) // 2) + [1.0] * ((n - k) // 2)
    weaker = [-1.0] * ((n + k) // 2 - 1) + [1.0] * ((n - k) // 2 + 1)  # one helped -> hurt
    assert gf.sign_flip_p(obs) <= gf.ALPHA_FAMILY < gf.sign_flip_p(weaker)


def test_select_plan_and_verdict():
    c = run({"good": [(0.0, U)] * 8 + [(U, U)] * 12, "bad": [(U, 0.0)] * 5 + [(0.0, 0.0)] * 15})
    sel = gf.select(c)
    assert [s for s, _, _ in sel] == ["good"]
    skills, m, per_seed = gf.plan_seeds(c, sel, spent=30.0, cap=34.0)
    assert skills == ["good"] and m == int(4.0 // (40 * 0.05))
    confirm = [c, c]
    v = gf.verdict(c, confirm, ["good"])
    assert v["verdict"].startswith("G1 PASS") and not v["aa"]["flag"]
    none = gf.verdict(c, confirm, [])
    assert none["verdict"].startswith("G1 FAIL")


def test_budget_drops_weakest_skill():
    c = run({"a": [(0.0, U)] * 20, "b": [(0.0, U)] * 20})
    sel = [("a", -0.5, 20), ("b", -0.2, 20)]
    # both: 20 no-skill + 40 skill runs = 60 x 0.05 = 3 USD per seed; a alone: 40 x 0.05 = 2 USD
    assert gf.plan_seeds(c, sel, spent=30.0, cap=34.0)[:2] == (["a", "b"], 1)
    assert gf.plan_seeds(c, sel, spent=31.5, cap=34.0)[:2] == (["a"], 1)
    assert gf.plan_seeds(c, sel, spent=33.0, cap=34.0)[:2] == ([], 0)


def test_sensitivity_analyses():
    # S1 paired t: strong negative mean -> small p; zero -> 0.5
    assert gf.paired_t_p([-1.0] * 10 + [0.0] * 10) < 0.01
    assert gf.paired_t_p([1.0, -1.0] * 10) == pytest.approx(0.5)
    # S2 cluster sign-flip: one repo carrying every helped task cannot be significant on its own
    one_repo = {f"django__django-{i}": -1.0 for i in range(12)}
    one_repo.update({f"sympy__sympy-{i}": 0.0 for i in range(6)})
    p, g = gf.cluster_sign_flip_p(one_repo)
    assert g == 2 and p >= 0.25  # 2 clusters: smallest attainable p is 1/4
    spread = {f"r{j}__r{j}-{i}": -1.0 for j in range(10) for i in range(2)}
    assert gf.cluster_sign_flip_p(spread)[0] == pytest.approx(1 / 1024)


def test_verdict_requires_robust_agreement():
    U = 2 / 3
    # 12 helped tasks, all in ONE repository: task-level test rejects, cluster test cannot
    pairs = [(0.0, U)] * 12 + [(U, U)] * 20
    run = {
        "skills": {
            "s": {
                "pairs": [
                    {"instance_id": f"django__django-{i}", "loss_with": w, "loss_without": o}
                    for i, (w, o) in enumerate(pairs)
                ]
            }
        }
    }
    v = gf.verdict(run, [run, run, run], ["s"])
    assert v["skills"]["s"]["reject"] and not v["skills"]["s"]["robust"]
    assert v["verdict"].startswith("INCONCLUSIVE")


def test_harm_direction_is_reported_separately():
    U = 2 / 3
    pairs = [(U, 0.0)] * 12 + [(U, U)] * 20  # skill breaks 12 tasks spread over 12 repos
    run = {
        "skills": {
            "s": {
                "pairs": [
                    {"instance_id": f"r{i}__r{i}-1", "loss_with": w, "loss_without": o}
                    for i, (w, o) in enumerate(pairs)
                ]
            }
        }
    }
    v = gf.verdict(run, [run, run, run], ["s"])
    assert not v["skills"]["s"]["reject"] and v["skills"]["s"]["harm"]["reject"]
    assert v["verdict"].startswith("G1 FAIL")  # the primary (benefit) decision is unchanged


def test_verdict_has_harm_verdict_and_label():
    import analyze_g1_final as gf

    pairs = [{"instance_id": f"o__r-{i}", "loss_with": 1.0, "loss_without": 0.0} for i in range(12)]
    run = {"skills": {"s": {"pairs": pairs}}}
    out = gf.verdict(None, [run, run, run], ["s"], label="E2")
    assert out["harm_verdict"].startswith("harm established") is False  # 1 repo cluster: S2 fails
    assert out["skills"]["s"]["harm"]["p"] < 0.025
    assert "E2" in out["verdict"]


def test_hypothetical_drops_pairs_not_tasks():
    import analyze_g1_final as gf

    def run(trunc_task):
        pairs = [
            {"instance_id": f"o__r{i}-1", "loss_with": 0.0, "loss_without": 1.0} for i in range(4)
        ]
        st = {f"o__r{i}-1": "Submitted" for i in range(4)}
        sk = dict(st)
        if trunc_task is not None:
            sk[f"o__r{trunc_task}-1"] = "LimitsExceeded"
        return {"skills": {"s": {"pairs": pairs}}, "exit_status": {"none": st, "s": sk}}

    out = gf.intercurrent([run(0), run(None), run(1)], ["s"])
    h = out["hypothetical"]["s"]
    assert h["n_tasks"] == 4 and h["n_pairs"] == 10  # 12 pairs minus the 2 truncated ones
    assert abs(out["truncation_rate"]["s"]["rate"] - 2 / 12) < 1e-12
    assert gf._lattice([1 / 2, 1 / 3, 1.0])[1] == 6  # means of 1..3 seeds stay exact


def test_ich_verdict_uses_primary_test_and_reports_sensitivity():
    import analyze_g1_final as gf

    # 30 helped tasks in ONE repository: primary rejects, S2 (1 cluster) cannot
    pairs = [{"instance_id": f"o__r-{i}", "loss_with": 0.0, "loss_without": 1.0} for i in range(30)]
    run = {"skills": {"s": {"pairs": pairs}}}
    out = gf.verdict(None, [run, run, run], ["s"], label="E1")
    assert out["verdict_ich_e9_r1"]["benefit"] == ["s"]
    assert out["skills"]["s"]["sensitivity_agrees"]["s2"] is False
    assert out["skills"]["s"]["sensitivity_agrees"]["s2_min_attainable_p"] == 0.5
    assert "INCONCLUSIVE" in out["verdict"]  # the pre-registered conjunction, still reported
