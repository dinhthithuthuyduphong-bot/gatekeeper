#!/usr/bin/env python3
"""Sensitivity of the end-of-pool test to dependence between tasks (R-102; 0 USD, simulation only).

Assumption 1 of the paper (tasks independent given the run state C) cannot be checked on data.
This script measures how often the end-of-pool test (lambda = 0.5, theta = 0, threshold 40) and
the registered exact sign test certify a skill when the pool mean of E[Z] is exactly 0 but tasks
are linked in their run order. Every scenario and every value below is reported; none is chosen
after seeing the output.

Scenarios (per arm, tasks in run order 1..N, marginal solve rate of task i kept at its base rate):
  a) within-arm AR(1): each arm has its own latent Gaussian AR(1) series with correlation rho;
     models feedback inside one run (a rate limit that slows the following tasks).
  b) shared AR(1): both arms of a task share one latent series; models an outage that hits both
     arms of the same tasks when they run in one job.
  c) block outage: in each arm, with probability 1/2, a stretch of L consecutive tasks fails
     outright; models an outage in one run. This dependence is part of the run state C (T1 covers
     it); it is reported as the error for the mean over runs (T2), like the shared-state case.
Grids: rho in {0.2, 0.5, 0.8} spans weak to strong correlation; L in {5, 10, 20} is 5-20 % of
the pool. They are a sensitivity grid, not thresholds: no decision depends on picking one value.

Base rates: the 100 Jinja test tasks (verify_methods.jinja_q). Nulls: homogeneous (skill =
baseline per task) and heterogeneous (half +0.3, half -0.3, recentred to pool mean 0).

  python scripts/dependence_sensitivity.py   # writes results/dependence_sensitivity.json
"""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).parent))
import verify_methods as vm  # noqa: E402

SEED = 20261125
REPS = vm.R_VALID  # 12,000: Monte Carlo SE about 0.0014 at alpha = 0.025
RHOS = (0.2, 0.5, 0.8)
BLOCKS = (5, 10, 20)


def ar1_latent(rng, reps: int, n: int, rho: float) -> np.ndarray:
    """Stationary Gaussian AR(1) series, unit variance, shape (reps, n)."""
    x = np.empty((reps, n))
    x[:, 0] = rng.standard_normal(reps)
    s = np.sqrt(1.0 - rho * rho)
    for i in range(1, n):
        x[:, i] = rho * x[:, i - 1] + s * rng.standard_normal(reps)
    return x


def resolved(latent: np.ndarray, p: np.ndarray) -> np.ndarray:
    """Gaussian copula: P(resolved) = p per task exactly, dependence through the latent series."""
    return norm.cdf(latent) < p[None, :]


def z_from(r0: np.ndarray, r1: np.ndarray) -> np.ndarray:
    z = (~r1).astype(float) - (~r0).astype(float)
    assert z.shape == r0.shape == r1.shape, (z.shape, r0.shape, r1.shape)
    return z


def block_fail(rng, r: np.ndarray, length: int) -> np.ndarray:
    """With probability 1/2 per replicate, set a random stretch of `length` tasks to unresolved."""
    reps, n = r.shape
    hit = rng.random(reps) < 0.5
    start = rng.integers(0, n - length + 1, size=reps)
    idx = np.arange(n)[None, :]
    mask = hit[:, None] & (idx >= start[:, None]) & (idx < start[:, None] + length)
    out = r.copy()
    out[mask] = False
    return out


def eprocess_crossed(z: np.ndarray, theta: float, c: float, alpha: float) -> np.ndarray:
    """Registered sequential e-process (src/.../eprocess.py BettingEProcess with its defaults
    prior_mean 0, prior_var 1, prior_weight 1), vectorised over replicates: True where log E_n
    reaches log(1/alpha) at any n. Added 25/11 after the first results, at a reviewer's request
    (R-104); it is computed on the same Z arrays, so the earlier numbers do not change."""
    reps, n = z.shape
    w0, s, s2 = 1.0, np.zeros(reps), np.ones(reps)
    log_e, crossed = np.zeros(reps), np.zeros(reps, dtype=bool)
    lam_max, thr = c / (1.0 + theta), np.log(1.0 / alpha)
    for i in range(n):
        mean = s / (i + w0)
        var = np.maximum(s2 / (i + w0) - mean * mean, 0.0)
        gap = -theta - mean
        lam = np.where(
            gap > 0, np.minimum(gap / np.where(gap > 0, var + gap * gap, 1.0), lam_max), 0.0
        )
        log_e += np.log1p(lam * (-theta - z[:, i]))
        crossed |= log_e >= thr
        s += z[:, i]
        s2 += z[:, i] * z[:, i]
    return crossed


def rates(z: np.ndarray) -> dict:
    return {
        "end_of_pool_reject": float(vm.eop_reject(z, vm.ALPHA).mean()),
        "sign_test_reject": float(vm.sign_reject(z, vm.ALPHA).mean()),
        "eprocess_cross": float(eprocess_crossed(z, 0.0, 0.5, vm.ALPHA).mean()),
    }


def run(rng, q: np.ndarray, reps: int) -> dict:
    n = q.size
    alt = np.where(np.arange(n) % 2 == 0, 1.0, -1.0)
    nulls = {
        "homogeneous": q.copy(),
        "heterogeneous_pm0.3": vm.recentre(q, np.clip(q + 0.3 * alt, 0, 1)),
    }
    out: dict = {}
    for name, ps in nulls.items():
        cell: dict = {"pool_mean_EZ": float((q - ps).mean())}
        cell["independent"] = rates(
            z_from(
                resolved(rng.standard_normal((reps, n)), q),
                resolved(rng.standard_normal((reps, n)), ps),
            )
        )
        for rho in RHOS:
            r0 = resolved(ar1_latent(rng, reps, n, rho), q)
            r1 = resolved(ar1_latent(rng, reps, n, rho), ps)
            cell[f"a_within_arm_rho{rho}"] = rates(z_from(r0, r1))
            lat = ar1_latent(rng, reps, n, rho)
            cell[f"b_shared_rho{rho}"] = rates(z_from(resolved(lat, q), resolved(lat, ps)))
        for length in BLOCKS:
            r0 = block_fail(rng, resolved(rng.standard_normal((reps, n)), q), length)
            r1 = block_fail(rng, resolved(rng.standard_normal((reps, n)), ps), length)
            cell[f"c_block_outage_L{length}"] = rates(z_from(r0, r1))
        out[name] = cell
    return out


def summarise(res: dict) -> dict:
    def mx(prefix: str, key: str) -> float:
        return max(v[key] for cell in res.values() for k, v in cell.items() if k.startswith(prefix))

    return {
        "max_eop_within_arm": mx("a_", "end_of_pool_reject"),
        "max_eop_shared": mx("b_", "end_of_pool_reject"),
        "max_eop_block_outage": mx("c_", "end_of_pool_reject"),
        "max_eop_independent": mx("independent", "end_of_pool_reject"),
        "max_sign_within_arm": mx("a_", "sign_test_reject"),
        "max_sign_block_outage": mx("c_", "sign_test_reject"),
        "max_ep_independent": mx("independent", "eprocess_cross"),
        "max_ep_within_arm": mx("a_", "eprocess_cross"),
        "max_ep_shared": mx("b_", "eprocess_cross"),
        "max_ep_block_outage": mx("c_", "eprocess_cross"),
        "alpha": vm.ALPHA,
        "mcse_at_alpha": float(np.sqrt(vm.ALPHA * (1 - vm.ALPHA) / REPS)),
    }


def main() -> int:
    q = vm.jinja_q()
    res = run(np.random.default_rng(SEED), q, REPS)
    out = {
        "inputs": {
            "n_tasks": int(q.size),
            "reps": REPS,
            "seed": SEED,
            "rhos": RHOS,
            "blocks": BLOCKS,
        },
        "results": res,
        "summary": summarise(res),
        "environment": {"python": platform.python_version(), "numpy": np.__version__},
    }
    Path("results/dependence_sensitivity.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out["summary"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
