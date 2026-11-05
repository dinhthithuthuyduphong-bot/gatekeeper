import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import placebo_suite as ps  # noqa: E402


def test_signflip_exact_extremes_and_zeros():
    assert ps.signflip_p_exact([1.0] * 10) == pytest.approx(2 / 1024)
    assert ps.signflip_p_exact([0.0] * 10) == 1.0
    assert ps.signflip_p_exact([1.0, -1.0]) == 1.0
    assert ps.signflip_p_exact([2.0, 0.0, 0.0]) == 1.0  # one nonzero entry: p = 1


def test_signflip_mc_close_to_exact():
    rng = np.random.default_rng(0)
    d = np.array([3.0, 1.0, 2.0, 0.0, -1.0, 4.0, 2.0, 1.0])
    assert ps.signflip_p_mc(d, 200_000, rng) == pytest.approx(
        ps.signflip_p_exact(list(d)), abs=0.01
    )


def test_library_drift_and_esr_on_extreme_streams():
    assert ps.library_drift_retires([1.0] * 120)  # always harmful: mean gain -1 <= -0.10 at t = 100
    assert not ps.library_drift_retires([-1.0] * 400)  # always helpful
    assert not ps.library_drift_retires([1.0] * 99)  # below the evidence floor
    assert ps.esr_alarms([1.0] * 50)
    assert not ps.esr_alarms([-1.0] * 400)


def test_binom_count_p():
    assert ps.binom_count_p(10, 0) == pytest.approx(2**-10)
    assert ps.binom_count_p(0, 0) == 1.0
    assert ps.binom_count_p(5, 5) > 0.5


def test_candidates_order_matches_section_18():
    none = np.array([[True, False, True]])  # seeds 41, 51, 61
    skill = np.array([[False, False, False]])
    sk, pl = ps.candidates(none, skill)
    assert sk.tolist() == [[True, False, True]]
    # placebo pairs (target, reference): (41, 61), (51, 41), (61, 51)
    assert pl.tolist() == [[False, True, False]]


def test_simulate_cell_q1_never_resolves_with_skill():
    rng = np.random.default_rng(1)
    none, skill = ps.simulate_cell(rng, 0.5, 1.0, 200, 3, 1.0)
    assert not skill.any() and none.shape == (200, 3)


def test_gk_harm_detects_clear_harm_and_keeps_level_under_noise():
    rng = np.random.default_rng(2)
    assert ps.gk_harm([1.0] * 60, 0.025)
    false = sum(ps.gk_harm(list(rng.choice([-1.0, 0.0, 1.0], 300)), 0.025) for _ in range(400))
    assert false / 400 <= 0.025 + 2 * (0.025 * 0.975 / 400) ** 0.5  # Ville: P(cross) <= alpha


def test_sham_audit_parse_and_prompt_conditions():
    import sham_audit as sa

    assert sa.parse('noise {"attributed": true, "confidence": 0.8, "category": "x"} tail')[
        "attributed"
    ]
    assert sa.parse('{"attributed": "yes"}') is None
    assert sa.parse("no json") is None
    tpl = sa.PROMPT.read_text()
    assert "{setup_sentence}" in tpl and "{skill_block}" in tpl and "{target_tail}" in tpl


@pytest.mark.skipif(
    not Path("runs/g1-e1-s41-p00").exists(), reason="E1 runs only on the work machine"
)
def test_sham_audit_collect_matches_section_18_counts():
    import json

    import sham_audit as sa

    real, placebo = sa.collect()
    att = json.loads(Path("results/replicate_attribution.json").read_text())["stages"]["e1"]
    assert len(real) == sum(
        v["attribution"]["functional"]["skill_candidates"] for v in att.values()
    )
    assert len({(p["iid"], p["target"], p["ref"]) for p in placebo}) == len(placebo)


def test_proposition_P_expectations():
    """docs/theory/proofs.md, Proposition P (a) and (b), by simulation."""
    rng = np.random.default_rng(5)
    n, k, reps = 60, 3, 4000
    p0 = rng.uniform(0.1, 0.9, n)
    h = rng.uniform(0.0, 0.5, n)
    diffs, causal = [], []
    for _ in range(reps):
        none = rng.random((n, k)) < p0[:, None]
        n2 = rng.random((n, k)) < p0[:, None]  # N' (the run without the skill)
        hit = rng.random((n, k)) < h[:, None]
        skill = n2 & ~hit
        sk, pl = ps.candidates(none, skill)
        diffs.append(sk.sum() - pl.sum())
        causal.append((sk & n2).sum())
    target = (k * p0 * (p0 - p0 * (1 - h))).sum()
    se = np.std(diffs) / np.sqrt(reps)
    assert abs(np.mean(diffs) - target) < 3 * se  # (a)
    assert abs(np.mean(diffs) - np.mean(causal)) < 3 * se + 3 * np.std(causal) / np.sqrt(
        reps
    )  # (b)


def test_section20_test_command_pattern():
    import section20 as s20

    assert s20.TEST_CMD.search("cd /testbed && python -m pytest tests/test_x.py")
    assert s20.TEST_CMD.search("./runtests.py admin_views")
    assert s20.TEST_CMD.search("python manage.py test app")
    assert not s20.TEST_CMD.search("grep -rn foo src/")


def test_preflight_run_counts_accept_reused_none_only():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import preflight

    reused = {
        "reused_none": "x.json",
        "usage": {"none": {"runs": 0, "scored": 3}, "s": {"runs": 3, "scored": 3}},
    }
    assert preflight.run_count_problems(reused) == []
    not_reused = {"usage": {"none": {"runs": 0, "scored": 3}}}
    assert preflight.run_count_problems(not_reused)
    lost = {"reused_none": "x.json", "usage": {"s": {"runs": 3, "scored": 2}}}
    assert preflight.run_count_problems(lost)
