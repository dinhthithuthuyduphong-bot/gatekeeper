"""Candidate edit-program skills and composition pairs from gold-patch metadata (TODO.md Phase 4).

Input: data/benchmarks/*.csv with the `patterns` / `functions` columns written by
scripts/fetch_benchmarks.py. Output: results/skill_mining.json.

* Train side (SWE-Gym only, to respect the repository split): for each edit-pattern family, the
  number of training repositories and tasks where it appears. Families seen in >= MIN_REPOS
  repositories are candidate *transferable* skills.
* Test side (SWE-bench + Verified + Live, minus train repos): how often each family appears,
  i.e. how many target tasks a skill of that family could plausibly apply to.
* Composition candidates: test tasks of one repository whose gold patches touch the same function.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from gatekeeper.patches import PATTERNS, composition_candidates

csv.field_size_limit(2**31 - 1)  # some gold patches touch thousands of functions
BENCH = Path("data/benchmarks")
MIN_REPOS = 3


def rows(name: str) -> list[dict]:
    p = BENCH / f"{name}.csv"
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def split_list(v: str) -> list[str]:
    return [x for x in (v or "").split(";") if x]


def main() -> int:
    train = rows("swe-gym")
    if not train or "patterns" not in train[0]:
        print("no pattern metadata yet: rerun the 'Data snapshots' workflow")
        return 1
    train_repos = {r["repo"] for r in train}
    test: dict[str, dict] = {}
    for name in ("swe-bench", "swe-bench-verified", "swe-bench-live"):
        for r in rows(name):
            if r["repo"] not in train_repos:
                test.setdefault(r["instance_id"], r)
    test_rows = list(test.values())

    fam_repos: dict[str, set[str]] = defaultdict(set)
    fam_tasks: Counter[str] = Counter()
    for r in train:
        for f in split_list(r["patterns"]):
            fam_repos[f].add(r["repo"])
            fam_tasks[f] += 1
    test_tasks: Counter[str] = Counter()
    test_repos: dict[str, set[str]] = defaultdict(set)
    for r in test_rows:
        for f in split_list(r["patterns"]):
            test_tasks[f] += 1
            test_repos[f].add(r["repo"])
    families = []
    for f in PATTERNS:
        families.append(
            {
                "family": f,
                "train_repos": len(fam_repos[f]),
                "train_tasks": fam_tasks[f],
                "train_share": fam_tasks[f] / len(train),
                "test_tasks": test_tasks[f],
                "test_repos": len(test_repos[f]),
                "test_share": test_tasks[f] / max(len(test_rows), 1),
                "transferable_candidate": len(fam_repos[f]) >= MIN_REPOS,
            }
        )
    families.sort(key=lambda d: (-d["train_repos"], -d["train_tasks"]))

    comp_in = [
        {
            "instance_id": r["instance_id"],
            "repo": r["repo"],
            "functions": split_list(r["functions"]),
        }
        for r in test_rows
        if r.get("functions")
    ]
    pairs = composition_candidates(comp_in)
    by_repo = Counter(p["a"].split("__")[0] for p in pairs)
    out = {
        "n_train_tasks": len(train),
        "n_train_repos": len(train_repos),
        "n_test_tasks": len(test_rows),
        "min_repos_for_transferable": MIN_REPOS,
        "families": families,
        "composition_candidates": {
            "n_pairs": len(pairs),
            "n_tasks_involved": len({t for p in pairs for t in (p["a"], p["b"])}),
            "pairs_by_repo_owner": dict(by_repo.most_common()),
            "examples": pairs[:25],
        },
    }
    Path("results").mkdir(exist_ok=True)
    Path("results/skill_mining.json").write_text(json.dumps(out, indent=2) + "\n")
    for f in families:
        print(
            f"{f['family']:<20} train repos={f['train_repos']:>2} tasks={f['train_tasks']:>4} "
            f"test tasks={f['test_tasks']:>4} candidate={f['transferable_candidate']}"
        )
    print(
        "composition candidate pairs:",
        len(pairs),
        "tasks:",
        out["composition_candidates"]["n_tasks_involved"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
