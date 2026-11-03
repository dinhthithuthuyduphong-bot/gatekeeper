"""Task pool for experiment E1 (docs/preregistration_e1.md): for each remaining family skill, ALL
tasks of the full SWE-bench test split whose activation predicate I(x) holds on the issue text,
repositories of the SWE-Gym train split excluded, in a RANDOM order fixed by SEED.

The pool is validated in that order (scripts/validate_pool.py) and the first N_PER_SKILL usable
tasks of each skill are used: simple random sampling without replacement, so no margin for
rejected tasks has to be chosen. Runs in GitHub Actions (needs HuggingFace).
Writes data/e1_pool.json (copy to configs/pools/e1.json to validate it).
"""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path

from gatekeeper.scope import TargetContext, screen
from gatekeeper.skill import Skill

DATASET = "SWE-bench/SWE-bench"  # full test split, swebench>=5 format
SKILLS = ["null-guard", "type-guard", "exception-handling"]
SEED = 2027  # fixed before any E1 data exist; same seed convention as the G1 pools
N_PER_SKILL = 40  # docs/g1_verdict.md section 2: n for delta = 0.109, power 80%, 3 seeds


def main() -> int:
    from datasets import load_dataset

    csv.field_size_limit(2**31 - 1)
    with Path("data/benchmarks/swe-gym.csv").open(encoding="utf-8") as fh:
        train_repos = {r["repo"] for r in csv.DictReader(fh)}
    rows = [r for r in load_dataset(DATASET, split="test") if r["repo"] not in train_repos]
    order: dict[str, list[str]] = {}
    for sid in SKILLS:
        s = Skill.load(f"configs/skills/{sid}.json")
        act = sorted(
            r["instance_id"]
            for r in rows
            if screen(
                s,
                TargetContext(
                    name=r["repo"], fingerprints={}, issue_text=r["problem_statement"] or ""
                ),
            ).in_scope
        )
        random.Random(f"{SEED}-{sid}").shuffle(act)
        order[sid] = act
    # validate the first 2 * N_PER_SKILL of each random order: enough unless more than half are
    # unusable; if fewer than N_PER_SKILL are usable, the next ones in the same order are added
    take = {sid: ids[: 2 * N_PER_SKILL] for sid, ids in order.items()}
    instances = sorted({i for ids in take.values() for i in ids})
    out = {
        "_comment": __doc__.split("\n\n")[0],
        "dataset": DATASET,
        "seed": SEED,
        "n_per_skill": N_PER_SKILL,
        "random_order": order,
        "per_skill": take,
        "instances": instances,
        "stats": {sid: {"activated": len(ids)} for sid, ids in order.items()},
    }
    Path("data").mkdir(exist_ok=True)
    Path("data/e1_pool.json").write_text(json.dumps(out, indent=1) + "\n")
    print({sid: len(ids) for sid, ids in order.items()}, "instances to validate:", len(instances))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
