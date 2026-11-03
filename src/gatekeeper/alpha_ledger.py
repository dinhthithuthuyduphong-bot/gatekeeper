"""Pre-allocated alpha budget (TODO.md R7, corrected Theorem 4).

Union bound over every (skill, scope) cell, every composite admission problem and every
re-admission after retirement:

    sum_{(S,s)} alpha_{S,s} + sum_{(S o S', s)} alpha_{S o S', s} + alpha_re <= alpha

The number of composites and re-admissions is not known in advance, so their shares are spent
with the convergent sequence  share * 6 / (pi^2 k^2)  for the k-th request, which sums to at
most `share` however many requests arrive.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

__all__ = ["AlphaLedger"]

_BASEL = 6.0 / math.pi**2


class AlphaLedger:
    def __init__(
        self,
        total_alpha: float,
        cell_weights: Mapping[str, float],
        *,
        cell_frac: float,
        composite_frac: float,
        readmit_frac: float,
    ) -> None:
        """Explicit split only (no default): use from_plan() for the equal-weight split, which is
        the Bonferroni rule without prior ranking (docs/number_provenance.md section 3)."""
        if not 0.0 < total_alpha < 1.0:
            raise ValueError("total_alpha must be in (0, 1)")
        fracs = (cell_frac, composite_frac, readmit_frac)
        if any(f < 0 for f in fracs) or sum(fracs) > 1.0 + 1e-12:
            raise ValueError("fractions must be non-negative and sum to at most 1")
        if not cell_weights or any(w <= 0 for w in cell_weights.values()):
            raise ValueError("cell_weights must be non-empty and positive")
        self.total_alpha = total_alpha
        wsum = float(sum(cell_weights.values()))
        cell_budget = cell_frac * total_alpha
        # Fixed before any trial is run (predictable): proportional to expected reuse frequency.
        self.cell_alpha: dict[str, float] = {
            k: cell_budget * w / wsum for k, w in cell_weights.items()
        }
        self.composite_budget = composite_frac * total_alpha
        self.readmit_budget = readmit_frac * total_alpha
        self._k_comp = 0
        self._k_re = 0
        self.spent_composite = 0.0
        self.spent_readmit = 0.0

    @classmethod
    def from_plan(
        cls,
        total_alpha: float,
        cells: list[str],
        n_composite: int = 0,
        n_readmit: int = 0,
    ) -> AlphaLedger:
        """Equal weight per PLANNED hypothesis (Bonferroni with no prior ranking): every cell gets
        alpha / K with K = cells + planned composites + planned re-admissions, and the composite /
        re-admission shares equal their planned counts / K (spent with 6/(pi^2 k^2), so requests
        beyond the plan still keep the total <= alpha). Replaces the hand-picked 70/20/10 split
        (docs/number_provenance.md); FWER holds for any split, only power changes."""
        k = len(cells) + n_composite + n_readmit
        if not cells or k <= 0:
            raise ValueError("need at least one cell")
        return cls(
            total_alpha,
            dict.fromkeys(cells, 1.0),
            cell_frac=len(cells) / k,
            composite_frac=n_composite / k,
            readmit_frac=n_readmit / k,
        )

    def cell(self, key: str) -> float:
        return self.cell_alpha[key]

    def next_composite(self) -> float:
        self._k_comp += 1
        a = self.composite_budget * _BASEL / self._k_comp**2
        self.spent_composite += a
        return a

    def next_readmission(self) -> float:
        self._k_re += 1
        a = self.readmit_budget * _BASEL / self._k_re**2
        self.spent_readmit += a
        return a

    @property
    def committed(self) -> float:
        """Upper bound on total alpha ever spendable, including all future requests."""
        return sum(self.cell_alpha.values()) + self.composite_budget + self.readmit_budget

    @property
    def spent(self) -> float:
        return sum(self.cell_alpha.values()) + self.spent_composite + self.spent_readmit

    def check(self) -> None:
        if self.spent > self.total_alpha + 1e-15 or self.committed > self.total_alpha + 1e-12:
            raise AssertionError(
                f"alpha budget exceeded: spent={self.spent}, committed={self.committed}"
            )
