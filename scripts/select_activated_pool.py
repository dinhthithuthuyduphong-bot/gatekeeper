"""G1 task pool: SWE-bench Verified tasks where each family skill's activation predicate I(x)
holds on the issue text (TODO.md section 0.1, gate G1; corrections.md 1.2: P_s = activated tasks).

Up to PER_SKILL tasks per skill (fixed seed), repositories of the SWE-Gym train split excluded,
preferring tasks with few PASS_TO_PASS tests (faster, cheaper to evaluate). Runs in GitHub Actions
(needs HuggingFace). Writes data/g1_pool.json; copy it to configs/pools/g1.json to validate it.
"""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path

from gatekeeper.patches import edit_patterns, parse_patch
from gatekeeper.scope import TargetContext, screen
from gatekeeper.skill import Skill

PER_SKILL = 30
SEED = 2027


def main() -> int:
    from datasets import load_dataset

    csv.field_size_limit(2**31 - 1)
    train_repos = set()
    gym = Path("data/benchmarks/swe-gym.csv")
    if gym.exists():
        with gym.open(encoding="utf-8") as fh:
            train_repos = {r["repo"] for r in csv.DictReader(fh)}
    rows = [
        r
        for r in load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
        if r["repo"] not in train_repos
    ]
    skills = [Skill.load(p) for p in sorted(Path("configs/skills").glob("*.json"))]
    skills = [s for s in skills if s.procedure.get("family")]
    rng = random.Random(SEED)
    per_skill: dict[str, list[str]] = {}
    stats: dict[str, dict] = {}
    for s in skills:
        act = [
            r
            for r in rows
            if screen(
                s,
                TargetContext(
                    name=r["repo"], fingerprints={}, issue_text=r["problem_statement"] or ""
                ),
            ).in_scope
        ]
        fam = s.procedure["family"]
        has = sum(fam in edit_patterns(parse_patch(r["patch"] or "")) for r in act)
        act.sort(
            key=lambda r: (
                len(
                    json.loads(r["PASS_TO_PASS"])
                    if isinstance(r["PASS_TO_PASS"], str)
                    else r["PASS_TO_PASS"]
                ),
                r["instance_id"],
            )
        )
        head = act[: PER_SKILL * 2]
        rng.shuffle(head)
        chosen = sorted(r["instance_id"] for r in head[:PER_SKILL])
        per_skill[s.id] = chosen
        stats[s.id] = {
            "activated_in_verified": len(act),
            "family_in_gold_among_activated": has,
            "chosen": len(chosen),
        }
        print(s.id, stats[s.id])
    union = sorted({i for ids in per_skill.values() for i in ids})
    out = {
        "seed": SEED,
        "per_skill_max": PER_SKILL,
        "source": "princeton-nlp/SWE-bench_Verified (test)",
        "instances": union,
        "per_skill": per_skill,
        "stats": stats,
    }
    Path("data").mkdir(exist_ok=True)
    Path("data/g1_pool.json").write_text(json.dumps(out, indent=2) + "\n")
    print("union:", len(union), "tasks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
