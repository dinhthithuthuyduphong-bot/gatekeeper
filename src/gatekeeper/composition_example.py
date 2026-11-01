"""Executable counterexample behind the corrected Theorem 7 (TODO.md section 3, rows 1-2).

Mechanism (replaces the paper's self-contradictory "handler no longer matches but still
swallows"): S2 converts a blocking write to ``async``; S1 is a *synchronous* bounded-retry
wrapper. Composed, S1 calls the async function without awaiting it. The call returns a
coroutine object, never raises, and the write never executes: a silent failure.

* baseline         - flaky blocking write; fails on a transient error.
* S1 (retry-wrap)  - retries the sync write; fixes the transient failure.
* S2 (sync->async) - awaited async write with its own transient handling; fixes the failure.
* S1 o S2          - sync retry wraps the async write; returns a coroutine; row never written.

Order of composition: ``S1 o S2`` means S2's edit is applied first, then S1 wraps the result.
"""

from __future__ import annotations

import asyncio
import warnings
from collections.abc import Callable
from typing import Any


class TransientError(Exception):
    """A retryable infrastructure failure (e.g. a dropped connection)."""


class FlakyDB:
    """Raises TransientError on the first `fail_first` calls, then succeeds."""

    def __init__(self, fail_first: int = 1) -> None:
        self.rows: list[Any] = []
        self._remaining_failures = fail_first

    def _maybe_fail(self) -> None:
        if self._remaining_failures > 0:
            self._remaining_failures -= 1
            raise TransientError("connection reset")

    def insert(self, row: Any) -> None:
        self._maybe_fail()
        self.rows.append(row)

    async def ainsert(self, row: Any) -> None:
        await asyncio.sleep(0)
        self._maybe_fail()
        self.rows.append(row)


def retry(fn: Callable[[], Any], attempts: int = 3) -> Any:
    """S1's synchronous bounded retry. Correct for sync callables."""
    for k in range(attempts):
        try:
            return fn()
        except TransientError:
            if k == attempts - 1:
                raise
    return None


# --- the four program variants on one target call site ----------------------------------


def write_baseline(db: FlakyDB, row: Any) -> None:
    db.insert(row)


def write_s1(db: FlakyDB, row: Any) -> None:
    retry(lambda: db.insert(row))


async def _awrite_with_retry(db: FlakyDB, row: Any, attempts: int = 3) -> None:
    for k in range(attempts):
        try:
            await db.ainsert(row)
            return
        except TransientError:
            if k == attempts - 1:
                raise


def write_s2(db: FlakyDB, row: Any) -> None:
    asyncio.run(_awrite_with_retry(db, row))


def write_s1_o_s2(db: FlakyDB, row: Any) -> None:
    # S1's sync retry wrapped around S2's async call: returns an un-awaited coroutine.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        coro = retry(lambda: db.ainsert(row))
        if asyncio.iscoroutine(coro):
            coro.close()  # what garbage collection would eventually do; nothing ran


def retry_async_aware(make_call: Callable[[], Any], attempts: int = 3) -> Any:
    """S1': same intent as S1, but awaits the call when it is a coroutine."""
    for k in range(attempts):
        try:
            result = make_call()
            if asyncio.iscoroutine(result):
                result = asyncio.run(result)
            return result
        except TransientError:
            if k == attempts - 1:
                raise
    return None


def write_s1prime(db: FlakyDB, row: Any) -> None:
    retry_async_aware(lambda: db.insert(row))


def write_s1prime_o_s2(db: FlakyDB, row: Any) -> None:
    retry_async_aware(lambda: db.ainsert(row))


VARIANTS: dict[str, Callable[[FlakyDB, Any], None]] = {
    "baseline": write_baseline,
    "S1": write_s1,
    "S2": write_s2,
    "S1oS2": write_s1_o_s2,
    "S1prime": write_s1prime,
    "S1primeoS2": write_s1prime_o_s2,
}


def task_loss(variant: str, fail_first: int) -> float:
    """Functional loss in [0, 1] of one target task: 0 iff the row is written exactly once."""
    db = FlakyDB(fail_first=fail_first)
    try:
        VARIANTS[variant](db, {"id": 1})
    except TransientError:
        return 1.0
    return 0.0 if db.rows == [{"id": 1}] else 1.0


def scope_str(variant: str, theta: float, n_tasks: int = 100) -> float:
    """STR of `variant` on a scope where a fraction theta of tasks hit a transient failure.

    The no-skill loss is exactly theta, matching the corrected proof (l(x, empty) = theta).
    """
    n_flaky = round(theta * n_tasks)
    tasks = [1] * n_flaky + [0] * (n_tasks - n_flaky)
    base = sum(task_loss("baseline", t) for t in tasks) / n_tasks
    with_skill = sum(task_loss(variant, t) for t in tasks) / n_tasks
    return with_skill - base
