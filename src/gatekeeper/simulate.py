"""Monte-Carlo feasibility study (TODO.md section 4).

Paired differences Z in {-1, 0, +1} with P(Z=+1) = p_plus and P(Z=-1) = p_plus - STR, so
E[Z] = STR. Each replicate runs the same e-process as :mod:`gatekeeper.eprocess`, vectorised
across replicates.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import numpy as np

__all__ = ["SimResult", "simulate"]


@dataclass(frozen=True)
class SimResult:
    str_true: float
    alpha: float
    theta: float
    p_plus: float
    budget: int
    reps: int
    admit_rate: float
    median_trials_admitted: float | None
    mean_trials_all: float

    def to_dict(self) -> dict:
        return asdict(self)


def simulate(
    str_true: float,
    alpha: float,
    theta: float = 0.05,
    p_plus: float = 0.10,
    budget: int = 2000,
    reps: int = 200,
    seed: int = 0,
    c: float = 0.5,
    prior_mean: float = 0.0,
    prior_var: float = 1.0,
    prior_weight: float = 1.0,
) -> SimResult:
    p_minus = p_plus - str_true
    p_zero = 1.0 - p_plus - p_minus
    if min(p_plus, p_minus, p_zero) < 0:
        raise ValueError("invalid (STR, p_plus) combination")
    rng = np.random.default_rng(seed)
    z = rng.choice(np.array([-1.0, 0.0, 1.0]), size=(reps, budget), p=[p_minus, p_zero, p_plus])

    lam_max = c / (1.0 + theta)
    thr = math.log(1.0 / alpha)
    s = np.full(reps, prior_mean * prior_weight)
    s2 = np.full(reps, (prior_var + prior_mean**2) * prior_weight)
    log_e = np.zeros(reps)
    active = np.ones(reps, dtype=bool)
    stop_n = np.full(reps, budget)
    admitted = np.zeros(reps, dtype=bool)

    for i in range(budget):
        w = i + prior_weight
        mean = s / w
        var = np.maximum(s2 / w - mean**2, 0.0)  # as eprocess.var: gap^2 > 0 keeps the ratio finite
        gap = -theta - mean
        safe = np.where(gap > 0, var + gap**2, 1.0)  # avoid 0/0 where gap <= 0 (bet is 0 there)
        lam = np.where(gap > 0, np.minimum(gap / safe, lam_max), 0.0)
        zi = z[:, i]
        log_e = np.where(active, log_e + np.log1p(lam * (-theta - zi)), log_e)
        s = s + zi
        s2 = s2 + zi * zi
        newly = active & (log_e >= thr)
        admitted |= newly
        stop_n = np.where(newly, i + 1, stop_n)
        active &= ~newly
        if not active.any():
            break

    med = float(np.median(stop_n[admitted])) if admitted.any() else None
    return SimResult(
        str_true=str_true,
        alpha=alpha,
        theta=theta,
        p_plus=p_plus,
        budget=budget,
        reps=reps,
        admit_rate=float(admitted.mean()),
        median_trials_admitted=med,
        mean_trials_all=float(stop_n.mean()),
    )
