"""Numerical checks of the corrected theory (docs/theory/corrections.md)."""

import math

import numpy as np

from gatekeeper.alpha_ledger import AlphaLedger


def test_tv_shift_factor_two_is_tight():
    # P on Z in {-1, 0, 1}; Q moves mass xi from -1 to +1: TV(P, Q) = xi, mean shift = 2 xi.
    xi = 0.03
    p = np.array([0.30, 0.60, 0.10])
    q = p + np.array([-xi, 0.0, xi])
    vals = np.array([-1.0, 0.0, 1.0])
    tv = 0.5 * np.abs(p - q).sum()
    shift = q @ vals - p @ vals
    assert math.isclose(tv, xi)
    assert math.isclose(shift, 2 * xi)  # the paper's bound "<= xi" is violated
    # and the corrected bound 2 * TV holds for every perturbation of the same TV
    rng = np.random.default_rng(0)
    for _ in range(1000):
        d = rng.normal(size=3)
        d -= d.mean()
        d *= xi / (0.5 * np.abs(d).sum())
        q2 = p + d
        if (q2 < 0).any():
            continue
        assert abs(q2 @ vals - p @ vals) <= 2 * xi + 1e-12


def test_prop9_variance_ratio():
    rng = np.random.default_rng(1)
    n = 400_000
    sigma_t, sigma_s = 0.3, 0.2
    t1 = rng.normal(0, sigma_t, n)
    t2 = rng.normal(0, sigma_t, n)
    e_pi = rng.normal(0, sigma_s / math.sqrt(2), n)
    e_0 = rng.normal(0, sigma_s / math.sqrt(2), n)
    paired = (t1 + e_pi) - (t1 + e_0)
    unpaired = (t1 + e_pi) - (t2 + e_0)
    ratio = unpaired.var() / paired.var()
    expected = 1 + 2 * sigma_t**2 / sigma_s**2  # corrected Prop. 9
    assert abs(ratio - expected) / expected < 0.02
    assert abs(ratio - (1 + sigma_t**2 / sigma_s**2)) > 1.0  # paper's formula is off


def _boundary_null_cells(alphas, theta=0.05, budget=300, reps=200, seed=0):
    """Vectorised e-processes, one per cell, all at the least-favourable null STR = -theta."""
    rng = np.random.default_rng(seed)
    alphas = np.asarray(alphas)
    n_cells = len(alphas)
    p_plus = 0.10
    p_minus = p_plus + theta
    lam_max = 0.5 / (1 + theta)
    thr = np.log(1 / alphas)
    any_admit = np.zeros(reps, dtype=bool)
    shape = (reps, n_cells)
    s = np.zeros(shape)
    s2 = np.full(shape, 0.25)
    log_e = np.zeros(shape)
    crossed = np.zeros(shape, dtype=bool)
    for i in range(budget):
        z = rng.choice([-1.0, 0.0, 1.0], size=shape, p=[p_minus, 1 - p_minus - p_plus, p_plus])
        w = i + 1.0
        mean = s / w
        var = np.maximum(s2 / w - mean**2, 1e-6)
        gap = -theta - mean
        lam = np.where(gap > 0, np.minimum(gap / (var + gap**2), lam_max), 0.0)
        log_e = np.where(crossed, log_e, log_e + np.log1p(lam * (-theta - z)))
        crossed |= log_e >= thr
        s += z
        s2 += z * z
    any_admit = crossed.any(axis=1)
    return any_admit.mean()


def test_family_wise_error_with_ledger():
    # 50 cells sharing one alpha budget; every cell is at the boundary null.
    total = 0.10
    led = AlphaLedger(
        total,
        {f"c{i}": 1.0 for i in range(50)},
        cell_frac=0.7,
        composite_frac=0.2,
        readmit_frac=0.1,
    )
    fwer = _boundary_null_cells(list(led.cell_alpha.values()), reps=400)
    assert fwer <= total
    # without the union-bound split (each cell gets the full alpha) FWER blows up
    naive = _boundary_null_cells([total] * 50, reps=200, seed=1)
    assert naive > total
