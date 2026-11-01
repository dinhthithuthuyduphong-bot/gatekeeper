"""Resumable trial log and cost tracking (TODO.md Phase 2 'Log model ID...', Phase 6 'Script chay
hang loat, chay tiep duoc khi loi', 'Bang theo doi chi phi').

Every paired trial is one JSON line. Re-running a batch skips keys already present, so a crash
mid-batch loses at most the trial in flight. The record carries everything needed to
reproduce it: model id + access date, image digest, repo commit, seed, tokens, wall time, cost.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterable, Iterator
from dataclasses import asdict, dataclass, field
from pathlib import Path

__all__ = ["CostSummary", "ResumableLog", "TrialRecord", "run_batch"]

REQUIRED_FOR_REPRO = ("model_id", "model_access_date", "image_digest", "repo_commit", "seed")


@dataclass(frozen=True)
class TrialRecord:
    key: str  # unique: system/cell/task/seed
    system: str
    cell: str
    task_id: str
    seed: int
    loss_with: float
    loss_without: float
    model_id: str
    model_access_date: str
    image_digest: str
    repo_commit: str
    harness_commit: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    wall_seconds: float = 0.0
    cost_usd: float = 0.0
    extra: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        missing = [k for k in REQUIRED_FOR_REPRO if getattr(self, k) in ("", None)]
        if missing:
            raise ValueError(f"trial record {self.key} lacks reproducibility fields {missing}")
        if not self.image_digest.startswith("sha256:"):
            raise ValueError("image_digest must be pinned as sha256:<digest>")


class ResumableLog:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._repair_torn_tail()
        self._keys = {r["key"] for r in self._read()}

    def _repair_torn_tail(self) -> None:
        """Drop a partial final line left by a crash, so the next append starts on a new line."""
        if not self.path.exists() or self.path.stat().st_size == 0:
            return
        data = self.path.read_bytes()
        if data.endswith(b"\n"):
            return
        cut = data.rfind(b"\n") + 1  # 0 when the only line is torn
        with self.path.open("r+b") as fh:
            fh.truncate(cut)

    def _read(self) -> Iterator[dict]:
        if not self.path.exists():
            return
        with self.path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue  # a torn final line from a crash is ignored

    def __contains__(self, key: str) -> bool:
        return key in self._keys

    def __len__(self) -> int:
        return len(self._keys)

    def append(self, rec: TrialRecord) -> None:
        if rec.key in self._keys:
            return
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(rec), ensure_ascii=False) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        self._keys.add(rec.key)

    def records(self) -> list[dict]:
        seen, out = set(), []
        for r in self._read():
            if r["key"] not in seen:
                seen.add(r["key"])
                out.append(r)
        return out


def run_batch(
    log: ResumableLog, keys: Iterable[str], run_one: Callable[[str], TrialRecord]
) -> tuple[int, int]:
    """Run every key not yet logged. Returns (newly_run, skipped)."""
    new = skipped = 0
    for k in keys:
        if k in log:
            skipped += 1
            continue
        log.append(run_one(k))
        new += 1
    return new, skipped


@dataclass(frozen=True)
class CostSummary:
    trials: int
    tokens_in: int
    tokens_out: int
    wall_hours: float
    cost_usd: float
    budget_usd: float

    @property
    def remaining_usd(self) -> float:
        return self.budget_usd - self.cost_usd

    @property
    def over_budget(self) -> bool:
        return self.cost_usd > self.budget_usd

    @classmethod
    def from_log(cls, log: ResumableLog, budget_usd: float) -> CostSummary:
        rs = log.records()
        return cls(
            trials=len(rs),
            tokens_in=sum(r.get("tokens_in", 0) for r in rs),
            tokens_out=sum(r.get("tokens_out", 0) for r in rs),
            wall_hours=sum(r.get("wall_seconds", 0.0) for r in rs) / 3600,
            cost_usd=round(sum(r.get("cost_usd", 0.0) for r in rs), 4),
            budget_usd=budget_usd,
        )
