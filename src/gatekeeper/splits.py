"""Repository-level train/test split and per-scope task counts (TODO.md Phase 4).

Train split: SWE-Gym (skills are induced only from these repositories).
Test split: SWE-bench (+ Verified, SWE-bench-Live) repositories that never appear in train.
A scope here is (repo, version) — the finest unit the benchmarks expose; behavioural classes
are added by hand in the scope-family declaration (a human task).

For each scope we report whether it has enough *distinct* tasks for a given number of paired
trials (R2: drawing a fresh task per trial needs |T_s| >= n).
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path

__all__ = ["load_tasks", "make_split"]

TEST_SOURCES = ("swe-bench", "swe-bench-verified", "swe-bench-live")
TRAIN_SOURCES = ("swe-gym",)


def load_tasks(bench_dir: str | Path) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for p in sorted(Path(bench_dir).glob("*.csv")):
        with p.open(encoding="utf-8") as fh:
            out[p.stem] = list(csv.DictReader(fh))
    return out


def make_split(
    tasks: Mapping[str, list[dict]],
    thresholds: Iterable[int] = (30, 50, 100, 200, 500),
) -> dict:
    train_repos = {r["repo"] for s in TRAIN_SOURCES for r in tasks.get(s, [])}
    test_rows: dict[str, dict] = {}
    for s in TEST_SOURCES:
        for r in tasks.get(s, []):
            test_rows.setdefault(r["instance_id"], {**r, "source": s})
    test_repos_all = {r["repo"] for r in test_rows.values()}
    leaked = sorted(train_repos & test_repos_all)
    test_rows = {k: r for k, r in test_rows.items() if r["repo"] not in train_repos}

    per_scope: Counter[str] = Counter()
    versions: dict[str, set[str]] = defaultdict(set)
    for r in test_rows.values():
        v = r.get("version") or "unknown"
        per_scope[f"{r['repo']}@{v}"] += 1
        versions[r["repo"]].add(v)
    per_repo = Counter(r["repo"] for r in test_rows.values())
    thresholds = sorted(set(thresholds))
    return {
        "train_sources": list(TRAIN_SOURCES),
        "test_sources": list(TEST_SOURCES),
        "train_repos": sorted(train_repos),
        "test_repos": sorted(per_repo),
        "repos_removed_from_test_for_overlap": leaked,
        "n_train_tasks": sum(len(tasks.get(s, [])) for s in TRAIN_SOURCES),
        "n_test_tasks": len(test_rows),
        "test_tasks_per_repo": dict(per_repo.most_common()),
        "regime_A_candidates": sorted(r for r, vs in versions.items() if len(vs) >= 2),
        "tasks_per_scope": dict(per_scope.most_common()),
        "scopes_with_at_least": {
            t: sum(1 for n in per_scope.values() if n >= t) for t in thresholds
        },
        "repos_with_at_least": {t: sum(1 for n in per_repo.values() if n >= t) for t in thresholds},
        "test_instance_ids": sorted(test_rows),
    }
