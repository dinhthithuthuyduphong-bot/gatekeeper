"""Choose the candidate task pool for the G1 / R15 mini-pilot (TODO.md section 0.1, Phase 3).

From SWE-bench Verified: at most PER_REPO tasks per repository (diversity), preferring tasks with
few PASS_TO_PASS tests (fast to evaluate), excluding repositories that also appear in SWE-Gym.
Writes configs/pools/default.json; scripts/validate_pool.py then checks each task in CI.
"""

from __future__ import annotations

import csv
import json
import random
from collections import defaultdict
from pathlib import Path

N = 40
PER_REPO = 6
SEED = 2027


def main() -> None:
    csv.field_size_limit(2**31 - 1)
    with open("data/benchmarks/swe-bench-verified.csv", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    with open("data/benchmarks/swe-gym.csv", encoding="utf-8") as fh:
        train_repos = {r["repo"] for r in csv.DictReader(fh)}
    rng = random.Random(SEED)
    by_repo: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        if r["repo"] in train_repos:
            continue
        by_repo[r["repo"]].append(r)
    picked = []
    for repo in sorted(by_repo):
        cand = sorted(
            by_repo[repo], key=lambda r: (int(r["n_pass_to_pass"] or 0), r["instance_id"])
        )
        head = cand[: max(PER_REPO * 3, PER_REPO)]
        rng.shuffle(head)
        picked += head[:PER_REPO]
    rng.shuffle(picked)
    picked = sorted(picked[:N], key=lambda r: r["instance_id"])
    out = {
        "seed": SEED,
        "per_repo": PER_REPO,
        "source": "SWE-bench/SWE-bench_Verified (test)",
        "instances": [r["instance_id"] for r in picked],
        "repos": sorted({r["repo"] for r in picked}),
    }
    Path("configs").mkdir(exist_ok=True)
    Path("configs/pools/default.json").write_text(json.dumps(out, indent=2) + "\n")
    print(len(out["instances"]), "tasks from", len(out["repos"]), "repos:", out["repos"])


if __name__ == "__main__":
    main()
