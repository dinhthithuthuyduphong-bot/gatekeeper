"""Control conditions that need no third-party code (TODO.md Phase 2, 'Dieu kien doi chung').

Each policy answers, for one reuse of skill S on task x: run the skill or not, and at what cost
(in units of one agent+test run). Third-party baselines (XRepoSkill, MemGovern, gskill) are run
from their own repositories via adapters, never re-implemented here.

* B1 NoSkills            - never uses a skill.
* B2 UnrestrictedReuse   - always uses the skill.
* B8 AlwaysRetest        - before every reuse, runs the task with and without the skill and keeps
                           the skill only if it is not worse on that task (2 extra runs per reuse).
* B9 BudgetMatchedRetries- no skills; spends the same budget as Gatekeeper on extra repair attempts.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

__all__ = ["AlwaysRetest", "BudgetMatchedRetries", "Decision", "NoSkills", "UnrestrictedReuse"]


@dataclass(frozen=True)
class Decision:
    use_skill: bool
    extra_runs: int = 0


class NoSkills:
    name = "B1 No skills"

    def decide(self, skill_id: str, task_id: str, **_: object) -> Decision:
        return Decision(False)


class UnrestrictedReuse:
    name = "B2 Unrestricted reuse"

    def decide(self, skill_id: str, task_id: str, **_: object) -> Decision:
        return Decision(True)


class AlwaysRetest:
    name = "B8 Always-retest"

    def __init__(self, paired_run: Callable[[str, str], tuple[float, float]]) -> None:
        self.paired_run = paired_run  # (skill_id, task_id) -> (loss_with, loss_without)

    def decide(self, skill_id: str, task_id: str, **_: object) -> Decision:
        with_, without = self.paired_run(skill_id, task_id)
        return Decision(with_ <= without, extra_runs=2)


class BudgetMatchedRetries:
    """B9: attempts = 1 + floor(budget / cost_per_attempt); success if any attempt succeeds."""

    name = "B9 Budget-matched retries"

    def __init__(self, budget_runs: float, attempt: Callable[[str, int], bool]) -> None:
        if budget_runs < 0:
            raise ValueError("budget must be non-negative")
        self.budget_runs = budget_runs
        self.attempt = attempt  # (task_id, attempt_index) -> solved?

    def solve(self, task_id: str) -> tuple[bool, int]:
        n = 1 + int(self.budget_runs)
        for k in range(n):
            if self.attempt(task_id, k):
                return True, k + 1
        return False, n
