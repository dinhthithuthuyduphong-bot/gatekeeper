import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import dependence_sensitivity as ds  # noqa: E402


def test_copula_keeps_marginals_and_creates_correlation():
    rng = np.random.default_rng(1)
    p = np.array([0.1, 0.5, 0.9, 0.3])
    lat = ds.ar1_latent(rng, 40_000, 4, 0.8)
    r = ds.resolved(lat, p)
    assert r.shape == (40_000, 4)
    assert np.allclose(r.mean(axis=0), p, atol=0.01)
    assert np.corrcoef(lat[:, 0], lat[:, 1])[0, 1] > 0.75


def test_block_outage_sets_exactly_a_stretch():
    rng = np.random.default_rng(2)
    r = np.ones((2000, 30), dtype=bool)
    out = ds.block_fail(rng, r, 5)
    fails = (~out).sum(axis=1)
    assert set(np.unique(fails)) <= {0, 5}
    assert 0.45 < (fails == 5).mean() < 0.55
    for row in (~out)[fails == 5][:50]:
        idx = np.flatnonzero(row)
        assert idx[-1] - idx[0] == 4


def test_z_shape_guard():
    a = np.zeros((3, 4), dtype=bool)
    assert ds.z_from(a, a).shape == (3, 4)


def test_vectorised_eprocess_matches_registered_class():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from gatekeeper.eprocess import BettingEProcess

    rng = np.random.default_rng(3)
    z = rng.choice([-1.0, 0.0, 1.0], size=(300, 60), p=[0.35, 0.5, 0.15])
    got = ds.eprocess_crossed(z, 0.0, 0.5, 0.025)
    want = []
    for row in z:
        ep = BettingEProcess(theta=0.0, alpha=0.025, c=0.5)
        hit = False
        for v in row:
            ep.update(float(v))
            hit = hit or ep.crossed
        want.append(hit)
    assert got.tolist() == want
    assert 0 < got.sum() < len(got)
