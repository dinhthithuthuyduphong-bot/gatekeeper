"""Gatekeeper admission controller: Algorithm 1 plus composition, allocation and retirement.

Validity does not depend on how trials are allocated across cells: every cell (a skill or a
composite in one scope) owns a pre-allocated alpha from the AlphaLedger and an e-process that is
valid under optional stopping, so steering budget towards ambiguous cells (section 5.3) only
changes efficiency. Theorem 4' (docs/theory/corrections.md) then bounds the family-wise error.
"""

from __future__ import annotations

import json
import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol

import numpy as np

from gatekeeper.alpha_ledger import AlphaLedger
from gatekeeper.eprocess import BettingEProcess
from gatekeeper.footprint import overlaps
from gatekeeper.scope import TargetContext, compare_fingerprints, screen
from gatekeeper.skill import Skill

__all__ = ["Cell", "Gatekeeper", "TaskSampler", "TrialRunner"]

QUARANTINE, ADMITTED, OUT_OF_SCOPE, RETIRED = "quarantine", "admitted", "out_of_scope", "retired"


class TrialRunner(Protocol):
    def run_pair(self, procedures: tuple[str, ...], task_id: str, seed: int) -> tuple[float, float]:
        """Run one task twice from the same snapshot and seed: with the procedures applied in
        order, and without any. Return (loss_with, loss_without), both in [0, 1]."""


class TaskSampler(Protocol):
    def sample(self, scope: str, rng: np.random.Generator) -> str: ...


@dataclass
class Cell:
    skills: tuple[str, ...]  # application order; length 2 for a composite
    scope: str
    kind: str  # "skill" | "composite"
    alpha: float
    eprocess: BettingEProcess
    target_fingerprints: Mapping[str, str]
    status: str = QUARANTINE
    readmission: bool = False
    screen_reasons: tuple[str, ...] = ()
    trial_log: list[tuple[str, int, float, float]] = field(default_factory=list)

    @property
    def key(self) -> str:
        return f"{'∘'.join(self.skills)}@{self.scope}"

    @property
    def n(self) -> int:
        return self.eprocess.n


class Gatekeeper:
    def __init__(
        self,
        library: Mapping[str, Skill],
        ledger: AlphaLedger,
        runner: TrialRunner,
        sampler: TaskSampler,
        theta: float = 0.05,
        budget_per_cell: int = 2000,
        min_trials_before_abandon: int = 30,
        seed: int = 0,
    ) -> None:
        self.library = dict(library)
        self.ledger = ledger
        self.runner = runner
        self.sampler = sampler
        self.theta = theta
        self.budget_per_cell = budget_per_cell
        self.min_trials = min_trials_before_abandon
        self.rng = np.random.default_rng(seed)
        self.cells: dict[str, Cell] = {}
        self._retired: set[str] = set()
        self._seed = seed

    # ---- Algorithm 1, lines 1-3 ----------------------------------------------------------
    def request(self, skill_id: str, scope: str, target: TargetContext) -> Cell:
        skill = self.library[skill_id]
        key = f"{skill_id}@{scope}"
        existing = self.cells.get(key)
        if existing and existing.status in (QUARANTINE, ADMITTED):
            return existing

        result = screen(skill, target)
        readmit = key in self._retired
        if not result.in_scope:
            cell = Cell(
                (skill_id,),
                scope,
                "skill",
                0.0,
                BettingEProcess(self.theta, 0.5),
                dict(target.fingerprints),
                status=OUT_OF_SCOPE,
                screen_reasons=result.reasons,
            )
            self.cells[key] = cell
            return cell

        alpha = self.ledger.next_readmission() if readmit else self.ledger.cell(key)
        cell = Cell(
            (skill_id,),
            scope,
            "skill",
            alpha,
            BettingEProcess(self.theta, alpha),
            dict(target.fingerprints),
            readmission=readmit,
        )
        self.cells[key] = cell
        self._enqueue_composites(skill, scope, target)
        return cell

    def _enqueue_composites(self, skill: Skill, scope: str, target: TargetContext) -> None:
        for other in list(self.cells.values()):
            if other.kind != "skill" or other.scope != scope or other.skills[0] == skill.id:
                continue
            if other.status not in (QUARANTINE, ADMITTED):
                continue
            partner = self.library[other.skills[0]]
            if not overlaps(skill.footprint, partner.footprint):
                continue
            order = (partner.id, skill.id)  # partner already in the library is applied first
            ckey = f"{'∘'.join(order)}@{scope}"
            if ckey in self.cells and self.cells[ckey].status in (QUARANTINE, ADMITTED):
                continue
            a = self.ledger.next_composite()
            self.cells[ckey] = Cell(
                order,
                scope,
                "composite",
                a,
                BettingEProcess(self.theta, a),
                dict(target.fingerprints),
            )

    # ---- Algorithm 1, lines 4-9 ----------------------------------------------------------
    def step(self, cell: Cell, n: int = 1) -> Cell:
        if cell.status != QUARANTINE:
            return cell
        for _ in range(n):
            if cell.n >= self.budget_per_cell:
                break
            task = self.sampler.sample(cell.scope, self.rng)
            seed = int(self.rng.integers(2**31 - 1))
            with_, without = self.runner.run_pair(cell.skills, task, seed)
            if not (0.0 <= with_ <= 1.0 and 0.0 <= without <= 1.0):
                raise ValueError("trial runner returned loss outside [0, 1]")
            cell.eprocess.update(with_ - without)
            cell.trial_log.append((task, seed, with_, without))
            if cell.eprocess.crossed:
                cell.status = ADMITTED
                break
        return cell

    def _priority(self, cell: Cell) -> float:
        """Uncertainty-directed allocation (paper section 5.3). Heuristic; validity-neutral."""
        ep = cell.eprocess
        if cell.n < self.min_trials:
            return 2.0  # explore every cell a little first
        if ep.mean >= 0.0:
            return -math.inf  # looks neutral or harmful: stop spending on it
        return max(ep.log_e, 0.0) / ep.log_threshold  # closer to the threshold first

    def run(self, total_trials: int, batch: int = 5) -> int:
        """Spend up to `total_trials` paired trials on quarantined cells; return trials used."""
        used = 0
        while used < total_trials:
            open_cells = [
                c
                for c in self.cells.values()
                if c.status == QUARANTINE and c.n < self.budget_per_cell
            ]
            ranked = sorted(open_cells, key=self._priority, reverse=True)
            ranked = [c for c in ranked if self._priority(c) > -math.inf]
            if not ranked:
                break
            cell = ranked[0]
            before = cell.n
            self.step(cell, min(batch, total_trials - used))
            used += cell.n - before
        return used

    # ---- execution decision ----------------------------------------------------------------
    def may_execute(self, skill_ids: Iterable[str], scope: str) -> tuple[bool, list[str]]:
        """Functional admission of every skill AND of every overlapping pair AND capability
        approval. The capability verdict is a separate precondition, never mixed into the
        functional e-process."""
        ids = list(skill_ids)
        why: list[str] = []
        for sid in ids:
            c = self.cells.get(f"{sid}@{scope}")
            if c is None or c.status != ADMITTED:
                why.append(f"{sid}: functionally {c.status if c else 'not requested'}")
            if self.library[sid].capability_verdict != "approved":
                why.append(f"{sid}: capability {self.library[sid].capability_verdict}")
        for i, a in enumerate(ids):
            for b in ids[i + 1 :]:
                if not overlaps(self.library[a].footprint, self.library[b].footprint):
                    continue
                comps = [self.cells.get(f"{a}∘{b}@{scope}"), self.cells.get(f"{b}∘{a}@{scope}")]
                if not any(c is not None and c.status == ADMITTED for c in comps):
                    why.append(f"{a}+{b}: composite not admitted")
        return (not why, why)

    # ---- retirement (paper section 5.4) -------------------------------------------------
    def on_environment_change(self, scope: str, new_fingerprints: Mapping[str, str]) -> list[str]:
        retired = []
        for c in self.cells.values():
            if c.scope != scope or c.status not in (ADMITTED, QUARANTINE):
                continue
            if compare_fingerprints(c.target_fingerprints, new_fingerprints) or any(
                c.target_fingerprints.get(k) != v
                for k, v in new_fingerprints.items()
                if k.startswith("lock:")
            ):
                c.status = RETIRED
                if c.kind == "skill":
                    self._retired.add(c.key)
                retired.append(c.key)
        return retired

    # ---- certificate ---------------------------------------------------------------------
    def certificate(self, cell: Cell, xi_grid: Iterable[float] = (0.0, 0.01, 0.025, 0.05)) -> dict:
        skill_caps = {s: self.library[s].capability_verdict for s in cell.skills}
        return {
            "cell": cell.key,
            "kind": cell.kind,
            "decision": {ADMITTED: "Admit", QUARANTINE: "Quarantine"}.get(cell.status, cell.status),
            "theta": self.theta,
            "alpha_cell": cell.alpha,
            "alpha_family": self.ledger.total_alpha,
            "readmission": cell.readmission,
            "n_paired_trials": cell.n,
            "log_e": round(cell.eprocess.log_e, 6),
            "log_threshold": round(cell.eprocess.log_threshold, 6),
            "mean_paired_difference": round(cell.eprocess.mean, 6) if cell.n else None,
            "guarantee": [
                {
                    "xi": xi,
                    "statement": (
                        f"Pr[STR_Q > {-self.theta + 2 * xi:+.3f}] <= {self.ledger.total_alpha}"
                        " (family-wise, Theorem 4')"
                    ),
                    "implies_no_harm": 2 * xi <= self.theta,
                }
                for xi in xi_grid
            ],
            "screen_reasons": list(cell.screen_reasons),
            "capability_verdicts": skill_caps,
            "target_fingerprints": dict(cell.target_fingerprints),
            "issued_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }

    def certificates_json(self) -> str:
        return json.dumps(
            [self.certificate(c) for c in self.cells.values()], indent=2, ensure_ascii=False
        )
