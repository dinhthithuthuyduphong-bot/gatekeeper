import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import replicate_attribution as ra  # noqa: E402


def test_consistency_counts_only_same_nonzero_sign_rows():
    M = np.array([[1, 1, 1], [-1, -1, -1], [1, 0, 1], [1, -1, 1], [0, 0, 0]], float)
    assert ra.consistency(M) == pytest.approx(2 / 5)


def test_tau2_zero_when_tasks_identical_and_positive_when_they_differ():
    same = np.array([[1, 0, -1]] * 50, float)
    assert ra.tau2_mom(same) == pytest.approx(-same.var(axis=1, ddof=1).mean() / 3 + 0.0)
    rng = np.random.default_rng(0)
    eff = rng.normal(0, 0.5, 400)
    M = eff[:, None] + rng.normal(0, 0.1, (400, 3))
    assert ra.tau2_mom(M) == pytest.approx(eff.var(ddof=1), rel=0.15)


def test_signflip_null_has_expected_mean_for_pure_noise():
    rng = np.random.default_rng(1)
    M = rng.choice([-1.0, 1.0], size=(2000, 3))
    null = ra.signflip_null(M, 50, rng)
    assert null.shape == (50,)
    assert null.mean() == pytest.approx(0.25, abs=0.02)  # P(all three of one sign) = 2/8


def test_functional_candidate_rule():
    assert ra.functional(False, True)
    assert not ra.functional(True, True)
    assert not ra.functional(False, False)
    assert not ra.functional(True, False)


def test_efficiency_rule_matches_dong_et_al():
    r = {"tokens": 100, "seconds": 10.0}
    assert ra.efficiency({"tokens": 250, "seconds": 11.0}, r, True, False)  # max > 2, min > 1
    assert not ra.efficiency({"tokens": 250, "seconds": 9.0}, r, True, False)  # time decreased
    assert not ra.efficiency({"tokens": 150, "seconds": 15.0}, r, True, False)  # neither doubles
    assert not ra.efficiency({"tokens": 999, "seconds": 99.0}, r, False, False)  # not PASS/PASS
    assert ra.efficiency({"tokens": 250, "seconds": None}, r, True, False) is None
    assert ra.efficiency({"tokens": 250, "seconds": None}, r, True, True)  # token-only sensitivity


def test_boot_ci_contains_statistic_and_has_shape():
    rng = np.random.default_rng(2)
    M = rng.normal(0, 1, (100, 3))
    lo, hi = ra.boot_ci(lambda X: float(X.mean()), M, None, 500, rng)
    assert lo < M.mean() < hi
    lo2, hi2 = ra.boot_ci(lambda X: float(X.mean()), M, [str(i % 10) for i in range(100)], 500, rng)
    assert lo2 < hi2


def test_seed_of_parses_part_names():
    assert ra.seed_of("g1-e1-s51-p03") == "s51"
    assert ra.seed_of("g2-e2-s61-k12-p04") == "s61"
    with pytest.raises(ValueError):
        ra.seed_of("t4-x-p00")


def test_metrics_reads_usage_and_timestamps():
    import run_metrics as rm

    traj = {
        "messages": [
            {"role": "system"},
            {
                "role": "assistant",
                "extra": {
                    "timestamp": "10.0",
                    "response": {"usage": {"prompt_tokens": 5, "completion_tokens": 2}},
                },
            },
            {"role": "tool", "extra": {"timestamp": "13.5"}},
        ]
    }
    m = rm.metrics(traj)
    assert m["tokens"] == 7 and m["seconds"] == pytest.approx(3.5) and m["n_timestamps"] == 2


def test_recurrence_matches_registered_definition():
    assert ra.recurrence(np.array([3, 1, 0, 2])) == pytest.approx(3 / 6)
    assert ra.recurrence(np.array([0, 0])) is None


def test_end_to_end_on_synthetic_records():
    """Dry run of the analysis functions on fake data (L37), small repetition counts."""
    rng = np.random.default_rng(3)
    tasks = {}
    for t in range(30):
        tasks[f"repo{t % 5}__x-{t}"] = {
            s: (
                bool(rng.random() < 0.3),
                bool(rng.random() < 0.3),
                {"tokens": int(rng.integers(100, 400)), "seconds": float(rng.uniform(5, 50))},
                {"tokens": int(rng.integers(100, 400)), "seconds": float(rng.uniform(5, 50))},
            )
            for s in ra.SEEDS
        }
    M, ids = ra.zmatrix(tasks)
    assert M.shape == (30, 3)
    h = ra.heterogeneity(M, ids, 200, 200, rng)
    assert 0 <= h["p_one_sided"] <= 1 and h["tau2_ci95_task"][0] <= h["tau2_ci95_task"][1]
    a = ra.summarise(ra.attribution(tasks, ids), 200, rng)
    assert a["tasks"] == 30 and a["functional"]["skill_candidates"] >= 0
    pc = ra.power_check(tasks, ids, 5, 50, 50, rng)
    assert set(pc) == {str(t) for t in ra.POWER_TAUS}
