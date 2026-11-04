"""Admission rules compared in RQ1 (docs/preregistration_main_draft.md sections 7, 11, 11b).

Every rule sees the SAME trials of a cell. Trial value z = loss(with skill) - loss(without) in
[-1, 1] (loss 1 = unresolved), so z < 0 means the skill helped.

  gatekeeper   e-process (gatekeeper.eprocess), p = min(1, 1 / max_t E_t) (Ville), Holm over K cells
  plug_in      admit if mean(z) < 0
  b_x1         XRepoSkill as published: no admission gate, admit whatever retrieval selects
  b_x2         XRepoSkill's statistic used as a gate (our variant): its own mh_risk_difference
               (Mantel-Haenszel, Sato variance), imported from the pinned clone (no LICENSE: not
               copied), admit if rd - Z95 * se > 0 on the resolution scale
  b_g          GEPA / gskill acceptance: admit if sum of scores with > sum without, on the first
               m trials (m = 3, gskill's reflection_minibatch_size) and on all trials
"""

from __future__ import annotations

import math
import sys
from collections.abc import Sequence
from pathlib import Path

from gatekeeper.eprocess import BettingEProcess

GSKILL_MINIBATCH = 3  # gepa@8c7b697 gskill/train_optimize_anything.py: reflection_minibatch_size=3


def gatekeeper_p(z: Sequence[float], theta: float, alpha_cell: float, budget: int) -> float:
    """Anytime-valid p-value of one cell: min(1, 1 / max_t E_t) over its first `budget` trials."""
    ep = BettingEProcess(theta=theta, alpha=alpha_cell)
    best = 0.0
    for v in list(z)[:budget]:
        ep.update(v)
        best = max(best, ep.log_e)
    return min(1.0, math.exp(-best))


def holm(pvalues: dict[str, float], alpha: float) -> dict[str, bool]:
    """Holm (1979) step-down: reject the k-th smallest p while p_(k) <= alpha / (K - k + 1)."""
    order = sorted(pvalues, key=lambda c: pvalues[c])
    k_total = len(order)
    out = {c: False for c in order}
    for k, c in enumerate(order):
        if pvalues[c] <= alpha / (k_total - k):
            out[c] = True
        else:
            break
    return out


def plug_in(z: Sequence[float]) -> bool:
    return bool(z) and sum(z) / len(z) < 0


def b_x1(z: Sequence[float]) -> bool:
    return True


def b_g(z: Sequence[float], m: int | None) -> bool:
    """sum(resolved with) > sum(resolved without)  <=>  sum(z) < 0, on the first m trials."""
    zz = list(z) if m is None else list(z)[:m]
    return bool(zz) and sum(zz) < 0


def load_xreposkill_score(xrepo_root: Path):
    sys.path.insert(0, str(xrepo_root / "src"))
    import xreposkill.score as score  # pinned 26fd703, imported, not copied

    return score


def b_x2(pairs: Sequence[tuple[int, int, str]], score) -> bool:
    """pairs: (resolved with skill, resolved without, stratum id); one stratum per task and seed."""
    strata = [score.Stratum(sid, a=int(rw), n1=1, c=int(r0), n0=1) for rw, r0, sid in pairs]
    res = score.mh_risk_difference(strata)
    if res is None:
        return False
    rd, se = res
    return se > 0 and rd - score.Z95 * se > 0


def decide_cell(
    z: Sequence[float],
    pairs: Sequence[tuple[int, int, str]],
    theta: float,
    alpha_cell: float,
    budget: int,
    score,
) -> dict:
    return {
        "gatekeeper_p": gatekeeper_p(z, theta, alpha_cell, budget),
        "plug_in": plug_in(z),
        "b_x1": b_x1(z),
        "b_x2": b_x2(pairs, score) if score is not None else None,
        "b_g3": b_g(z, GSKILL_MINIBATCH),
        "b_gall": b_g(z, None),
        "n_trials": min(len(z), budget),
    }
