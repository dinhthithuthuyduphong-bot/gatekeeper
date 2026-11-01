import math

import numpy as np
import pytest

from gatekeeper.eprocess import BettingEProcess, run_admission


def test_rejects_out_of_range_inputs():
    with pytest.raises(ValueError):
        BettingEProcess(theta=0.0, alpha=0.05)
    with pytest.raises(ValueError):
        BettingEProcess(theta=0.05, alpha=1.5)
    ep = BettingEProcess(theta=0.05, alpha=0.05)
    with pytest.raises(ValueError):
        ep.update(1.5)


def test_bet_is_bounded_so_factors_stay_positive():
    ep = BettingEProcess(theta=0.05, alpha=0.05, c=0.5)
    for _ in range(50):
        ep.update(-1.0)  # strong evidence of benefit -> maximal bet
        assert 0.0 <= ep.next_lambda() <= 0.5 / 1.05 + 1e-12
    ep.update(1.0)  # worst case factor 1 - lambda * (1 + theta) >= 0.5
    assert math.isfinite(ep.log_e)


def test_no_bet_when_data_look_harmful():
    ep = BettingEProcess(theta=0.05, alpha=0.05)
    for _ in range(20):
        ep.update(1.0)
    assert ep.next_lambda() == 0.0
    assert not ep.crossed


def test_predictable_bet_uses_only_past_data():
    a = BettingEProcess(theta=0.05, alpha=0.05)
    b = BettingEProcess(theta=0.05, alpha=0.05)
    for z in (-1, 0, -1):
        a.update(z)
        b.update(z)
    # the bet for observation 4 is fixed before observation 4 is seen
    assert a.next_lambda() == b.next_lambda()
    lam4 = a.next_lambda()
    log_a, log_b = a.log_e, b.log_e
    a.update(1.0)
    b.update(-1.0)
    assert a.log_e == pytest.approx(log_a + math.log1p(lam4 * (-0.05 - 1.0)))
    assert b.log_e == pytest.approx(log_b + math.log1p(lam4 * (-0.05 + 1.0)))


def test_strong_skill_is_admitted_quickly():
    rng = np.random.default_rng(1)
    z = rng.choice([-1.0, 0.0, 1.0], size=2000, p=[0.35, 0.55, 0.10])  # STR = -0.25
    res = run_admission(z, theta=0.05, alpha=0.05, budget=2000)
    assert res.admitted
    assert res.decision == "Admit"
    assert res.n_trials < 300


def test_neutral_skill_stays_in_quarantine():
    z = [0.0] * 500  # STR = 0: harmless is not enough
    res = run_admission(z, theta=0.05, alpha=0.05, budget=500)
    assert not res.admitted
    assert res.decision == "Quarantine"
    assert res.n_trials == 500


def test_budget_is_respected():
    res = run_admission([-1.0] * 10_000, theta=0.05, alpha=1e-300, budget=7)
    assert res.n_trials == 7
