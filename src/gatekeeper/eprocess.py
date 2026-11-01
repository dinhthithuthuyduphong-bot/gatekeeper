"""Betting e-process for skill admission (TODO.md section 3, "E-process viet tuong minh").

Paired trial i gives Z_i = loss(with skill) - loss(without skill), Z_i in [-1, 1].
Null hypothesis H0: E[Z] >= -theta  (the skill does NOT help by at least theta).

    E_n = prod_{i<=n} (1 + lambda_i * (-theta - Z_i)),   0 <= lambda_i <= c / (1 + theta),  c < 1

lambda_i is chosen from Z_1..Z_{i-1} only (predictable). Under H0 each factor has
conditional mean <= 1 and is >= 1 - c > 0, so E_n is a nonnegative supermartingale with
E_0 = 1 and Ville's inequality gives Pr[exists n: E_n >= 1/alpha] <= alpha. Admission when
E_n >= 1/alpha is therefore valid at any data-dependent stopping time.

Computation is in log space to avoid overflow for small alpha.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass

__all__ = ["AdmissionResult", "BettingEProcess", "run_admission"]


class BettingEProcess:
    """Predictable plug-in (aGRAPA-style) betting e-process for H0: E[Z] >= -theta.

    Parameters
    ----------
    theta:
        Benefit margin; admission certifies STR <= -theta.
    alpha:
        Per-cell error budget alpha_{S,s}.
    c:
        Fraction of the maximal safe bet 1/(1+theta); must be in (0, 1). Using c < 1 keeps every
        factor >= 1 - c, so log E stays finite.
    prior_mean, prior_var, prior_weight:
        Pseudo-observations used before data arrive, so the first bets are cautious.
    """

    def __init__(
        self,
        theta: float,
        alpha: float,
        c: float = 0.5,
        prior_mean: float = 0.0,
        prior_var: float = 0.25,
        prior_weight: float = 1.0,
    ) -> None:
        if not 0.0 < theta < 1.0:
            raise ValueError("theta must be in (0, 1)")
        if not 0.0 < alpha < 1.0:
            raise ValueError("alpha must be in (0, 1)")
        if not 0.0 < c < 1.0:
            raise ValueError("c must be in (0, 1)")
        self.theta = theta
        self.alpha = alpha
        self.c = c
        self.lambda_max = c / (1.0 + theta)
        self.log_threshold = math.log(1.0 / alpha)
        self._w0 = prior_weight
        self._s = prior_mean * prior_weight
        self._s2 = (prior_var + prior_mean**2) * prior_weight
        self.n = 0
        self.log_e = 0.0

    @property
    def mean(self) -> float:
        return self._s / (self.n + self._w0)

    @property
    def var(self) -> float:
        m = self.mean
        return max(self._s2 / (self.n + self._w0) - m * m, 1e-6)

    def next_lambda(self) -> float:
        """Bet for the next observation; depends only on past data (predictable)."""
        gap = -self.theta - self.mean  # > 0 when the data look like the skill helps
        if gap <= 0.0:
            return 0.0
        lam = gap / (self.var + gap * gap)
        return min(lam, self.lambda_max)

    def update(self, z: float) -> float:
        """Consume one paired difference and return the new log E_n."""
        if not -1.0 <= z <= 1.0:
            raise ValueError(f"paired difference must lie in [-1, 1], got {z}")
        lam = self.next_lambda()
        self.log_e += math.log1p(lam * (-self.theta - z))
        self.n += 1
        self._s += z
        self._s2 += z * z
        return self.log_e

    @property
    def crossed(self) -> bool:
        return self.log_e >= self.log_threshold


@dataclass(frozen=True)
class AdmissionResult:
    admitted: bool
    n_trials: int
    log_e: float

    @property
    def decision(self) -> str:
        return "Admit" if self.admitted else "Quarantine"


def run_admission(
    paired_differences: Iterable[float],
    theta: float,
    alpha: float,
    budget: int,
    **kwargs: float,
) -> AdmissionResult:
    """Algorithm 1, lines 3-9: consume trials until E >= 1/alpha or the budget is exhausted."""
    ep = BettingEProcess(theta=theta, alpha=alpha, **kwargs)
    for z in paired_differences:
        if ep.n >= budget:
            break
        ep.update(z)
        if ep.crossed:
            return AdmissionResult(True, ep.n, ep.log_e)
    return AdmissionResult(False, ep.n, ep.log_e)
