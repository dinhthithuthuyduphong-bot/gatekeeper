import itertools
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gatekeeper.eprocess import BettingEProcess  # noqa: E402


def _mean_wealth(pool, theta):
    """Exact E[E_n] for n = 1..N over all orders of a fixed pool (Proposition prop:wor)."""
    tot = np.zeros(len(pool))
    perms = list(itertools.permutations(pool))
    for order in perms:
        ep = BettingEProcess(theta=theta, alpha=0.025, c=0.5)
        for k, z in enumerate(order):
            ep.update(z)
            tot[k] += np.exp(ep.log_e)
    return tot / len(perms)


def test_finite_pool_random_order_is_supermartingale_in_mean():
    for pool, theta in (
        ([-1, -1, -1, 1, 1, 1], 0.0),
        ([-1, -1, -1, -1, 1, 1, 1, 1], 0.0),
        ([-1, -1, 0, 0, 1, 1, 0], 0.0),
        ([-1, -1, -1, 0, 1, 1], 1 / 6),  # pool mean -1/6 = -theta: the boundary of H0
    ):
        assert np.mean(pool) >= -theta - 1e-12
        assert (_mean_wealth(pool, theta) <= 1 + 1e-12).all()


def test_bet_is_positive_only_when_running_sum_is_below_minus_theta_i():
    ep = BettingEProcess(theta=0.0, alpha=0.025, c=0.5)
    assert ep.next_lambda() == 0.0  # prior mean 0: no bet before data
    ep.update(1.0)
    assert ep.next_lambda() == 0.0
    ep.update(-1.0)
    assert ep.next_lambda() == 0.0  # sum 0, not < 0
    ep.update(-1.0)
    assert ep.next_lambda() > 0.0
