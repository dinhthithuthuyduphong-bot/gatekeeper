import json

import numpy as np
import pytest

from gatekeeper.analysis import (
    benjamini_hochberg,
    cluster_bootstrap_ci,
    endpoint_power,
    harm_at_coverage,
    harm_coverage_curve,
    kendall_tau,
    penalty_sweep,
    trials_needed,
    variance_components,
)
from gatekeeper.baselines import AlwaysRetest, BudgetMatchedRetries, NoSkills, UnrestrictedReuse
from gatekeeper.runlog import CostSummary, ResumableLog, TrialRecord, run_batch


def test_variance_components_recover_model():
    rng = np.random.default_rng(0)
    recs = []
    st, ss = 0.3, 0.2
    for i in range(20000):
        t = rng.normal(0, st)
        recs.append(
            (f"t{i}", 0.4 + t + rng.normal(0, ss / 2**0.5), 0.5 + t + rng.normal(0, ss / 2**0.5))
        )
    vc = variance_components(recs)
    assert vc["sigma_T2"] == pytest.approx(st**2, rel=0.05)
    assert vc["sigma_S2"] == pytest.approx(ss**2, rel=0.05)
    assert vc["unpaired_over_paired"] == pytest.approx(1 + 2 * st**2 / ss**2, rel=0.08)
    assert vc["mean_Z"] == pytest.approx(-0.1, abs=0.01)
    with pytest.raises(ValueError):
        variance_components(recs[:2])


def test_trials_needed_monotone_in_effect():
    strong = trials_needed(-0.25, 0.05, reps=200, max_budget=1000)
    weak = trials_needed(-0.15, 0.05, reps=200, max_budget=1000)
    assert strong is not None and weak is not None and strong < weak
    assert trials_needed(-0.05, 0.05, reps=100, max_budget=300) is None


def test_endpoint_power_grows_with_pairs():
    small = endpoint_power(20, 0.30, 0.10, reps=300, n_boot=200)
    large = endpoint_power(200, 0.30, 0.10, reps=300, n_boot=200)
    assert large > small
    assert large > 0.9


def test_paper_endpoint_is_underpowered():
    # The draft's own projection (11.5% -> 5.1%, 63 harmful pairs) against a 5-point margin.
    kw = dict(reps=400, n_boot=200, seed=2)
    margin5 = endpoint_power(63, 0.115, 0.051, margin=0.05, coupling="nested", **kw)
    superiority = endpoint_power(200, 0.115, 0.051, margin=0.0, coupling="nested", **kw)
    assert margin5 < 0.1  # even in the most favourable coupling
    assert superiority > 0.9
    with pytest.raises(ValueError):
        endpoint_power(10, 0.1, 0.2, coupling="nested")
    with pytest.raises(ValueError):
        endpoint_power(10, 0.2, 0.1, coupling="copula")


def test_cluster_bootstrap_is_wider_than_naive_when_clustered():
    rng = np.random.default_rng(3)
    vals, cl = [], []
    for r in range(10):
        shift = rng.normal(0, 1)
        for _ in range(30):
            vals.append(shift + rng.normal(0, 0.1))
            cl.append(f"repo{r}")
    est, lo, hi = cluster_bootstrap_ci(vals, cl, n_boot=1000)
    naive = 1.96 * np.std(vals) / np.sqrt(len(vals))
    assert lo < est < hi
    assert (hi - lo) / 2 > 2 * naive
    with pytest.raises(ValueError):
        cluster_bootstrap_ci([1.0], ["a", "b"])


def test_benjamini_hochberg():
    # m=4, q=0.05: thresholds 0.0125, 0.025, 0.0375, 0.05
    assert benjamini_hochberg([0.01, 0.04, 0.03, 0.2], q=0.05) == [True, False, False, False]
    assert benjamini_hochberg([0.01, 0.02, 0.03, 0.2], q=0.05) == [True, True, True, False]
    assert benjamini_hochberg([0.5, 0.6]) == [False, False]
    assert benjamini_hochberg([]) == []


def test_harm_coverage_matched_comparison():
    labels = ["beneficial"] * 4 + ["harmful"] * 4 + ["neutral"] * 2
    good_sys = [0.9, 0.8, 0.7, 0.6, 0.1, 0.2, 0.3, 0.65, 0.5, 0.4]
    bad_sys = [0.9, 0.5, 0.4, 0.3, 0.85, 0.8, 0.2, 0.1, 0.5, 0.4]
    c1, c2 = harm_coverage_curve(good_sys, labels), harm_coverage_curve(bad_sys, labels)
    assert c1[0][1] == 0.0 and c1[-1][1] == 1.0
    assert harm_at_coverage(c1, 0.75) < harm_at_coverage(c2, 0.75)


def test_penalty_sweep_and_tau():
    assert kendall_tau([1, 2, 3], [1, 2, 3]) == 1.0
    assert kendall_tau([1, 2, 3], [3, 2, 1]) == -1.0
    stable = penalty_sweep({"A": (0.4, 0.05), "B": (0.5, 0.10), "C": (0.6, 0.15)})
    assert stable["stable"]
    # A is better only for w < 0.233, so the ranking flips inside the sweep
    flip = penalty_sweep({"A": (0.40, 0.30), "B": (0.47, 0.00)})
    assert not flip["stable"]


def test_simple_baselines():
    assert not NoSkills().decide("s", "t").use_skill
    assert UnrestrictedReuse().decide("s", "t").use_skill
    b8 = AlwaysRetest(lambda s, t: (0.0, 1.0) if t == "fixable" else (1.0, 0.0))
    assert b8.decide("s", "fixable") == b8.decide("s", "fixable")
    assert b8.decide("s", "fixable").use_skill and b8.decide("s", "fixable").extra_runs == 2
    assert not b8.decide("s", "broken").use_skill
    b9 = BudgetMatchedRetries(2.7, lambda t, k: k == 2)
    assert b9.solve("t") == (True, 3)
    assert BudgetMatchedRetries(0, lambda t, k: False).solve("t") == (False, 1)
    with pytest.raises(ValueError):
        BudgetMatchedRetries(-1, lambda t, k: True)


def rec(key, cost=0.5, **kw):
    base = dict(
        key=key,
        system="gatekeeper",
        cell="good@django4",
        task_id="django__django-1",
        seed=1,
        loss_with=0.0,
        loss_without=1.0,
        model_id="claude-sonnet-5-5",
        model_access_date="2026-11-01",
        image_digest="sha256:abc",
        repo_commit="deadbeef",
        tokens_in=1000,
        tokens_out=200,
        wall_seconds=60,
        cost_usd=cost,
    )
    base.update(kw)
    return TrialRecord(**base)


def test_trial_record_requires_reproducibility_fields():
    with pytest.raises(ValueError):
        rec("k", model_id="")
    with pytest.raises(ValueError):
        rec("k", image_digest="python:3.11")  # tag, not a pinned digest


def test_resumable_log_and_cost(tmp_path):
    log = ResumableLog(tmp_path / "trials.jsonl")
    calls = []

    def run_one(k):
        calls.append(k)
        if k == "k3" and len(calls) == 3:
            raise RuntimeError("container died")
        return rec(k)

    with pytest.raises(RuntimeError):
        run_batch(log, ["k1", "k2", "k3", "k4"], run_one)
    assert len(log) == 2
    # simulate a torn line written by the crash
    with (tmp_path / "trials.jsonl").open("a") as fh:
        fh.write('{"key": "k3", "trunc')
    log2 = ResumableLog(tmp_path / "trials.jsonl")
    new, skipped = run_batch(log2, ["k1", "k2", "k3", "k4"], run_one)
    assert (new, skipped) == (2, 2)
    assert (tmp_path / "trials.jsonl").read_text().endswith("\n")  # torn line repaired
    log2.append(rec("k1"))  # duplicates are ignored
    assert len(log2.records()) == 4
    cs = CostSummary.from_log(log2, budget_usd=1.5)
    assert cs.trials == 4 and cs.cost_usd == 2.0 and cs.over_budget and cs.remaining_usd == -0.5
    assert cs.wall_hours == pytest.approx(4 * 60 / 3600)
    json.loads((tmp_path / "trials.jsonl").read_text().splitlines()[0])
