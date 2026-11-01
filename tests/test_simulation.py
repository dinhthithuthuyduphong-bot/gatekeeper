"""Monte-Carlo validity checks (TODO.md Phase 0 'Mo phong 1.000 lan voi STR = -theta')."""

import math

import numpy as np

from gatekeeper.eprocess import run_admission
from gatekeeper.simulate import simulate


def test_type_one_error_at_boundary_null():
    # STR = -theta is the least favourable null; false admission rate must be <= alpha.
    alpha = 0.05
    reps = 1000
    res = simulate(str_true=-0.05, alpha=alpha, reps=reps, budget=2000, seed=123)
    # allow 3 binomial standard errors of Monte-Carlo noise above alpha
    assert res.admit_rate <= alpha + 3 * math.sqrt(alpha * (1 - alpha) / reps)


def test_harmful_skill_never_admitted():
    res = simulate(str_true=0.10, alpha=0.05, reps=300, budget=1000, seed=7)
    assert res.admit_rate == 0.0


def test_power_increases_with_effect_size():
    weak = simulate(str_true=-0.10, alpha=0.05, reps=200, budget=500, seed=3)
    strong = simulate(str_true=-0.25, alpha=0.05, reps=200, budget=500, seed=3)
    assert strong.admit_rate >= weak.admit_rate
    assert strong.admit_rate == 1.0


def test_vectorised_simulation_matches_scalar_eprocess():
    rng = np.random.default_rng(42)
    z = rng.choice([-1.0, 0.0, 1.0], size=(1, 400), p=[0.30, 0.60, 0.10])
    scalar = run_admission(z[0], theta=0.05, alpha=0.01, budget=400)

    # re-run the vectorised path on the very same draws
    import gatekeeper.simulate as sim

    class _FixedRng:
        def choice(self, *_args, **_kwargs):
            return z

    orig = sim.np.random.default_rng
    sim.np.random.default_rng = lambda _seed: _FixedRng()
    try:
        vec = sim.simulate(str_true=-0.20, alpha=0.01, reps=1, budget=400)
    finally:
        sim.np.random.default_rng = orig
    assert bool(vec.admit_rate) == scalar.admitted
    if scalar.admitted:
        assert vec.median_trials_admitted == scalar.n_trials
