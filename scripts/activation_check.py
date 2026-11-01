"""How well do issue-text activation predicates I(x) predict where a skill family applies?
(docs/theory/corrections.md §1.2: P_s = tasks where I(x) holds.)

For every skill in configs/skills/ with `procedure.family` and `issue_regex` predicates: on the
SWE-Gym train split and the test split (SWE-bench + Verified + Live, minus train repos), compare
I(x) evaluated on the problem statement with "the gold patch contains the family" (oracle).
Runs in GitHub Actions (needs HuggingFace). Writes data/activation.json.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from gatekeeper.patches import edit_patterns, parse_patch
from gatekeeper.scope import TargetContext, screen
from gatekeeper.skill import Skill

SOURCES = {
    "train": [("SWE-Gym/SWE-Gym", "train")],
    "test": [
        ("princeton-nlp/SWE-bench", "test"),
        ("princeton-nlp/SWE-bench_Verified", "test"),
        ("SWE-bench-Live/SWE-bench-Live", "full"),
    ],
}


def load(split: str) -> list[dict]:
    from datasets import load_dataset

    rows: dict[str, dict] = {}
    for ds_id, sp in SOURCES[split]:
        try:
            for r in load_dataset(ds_id, split=sp):
                rows.setdefault(
                    r["instance_id"],
                    {k: r.get(k) for k in ("instance_id", "repo", "problem_statement", "patch")},
                )
        except Exception as exc:  # noqa: BLE001
            print(f"skip {ds_id}:{sp}: {exc!r}")
    return list(rows.values())


def confusion(skill: Skill, rows: list[dict]) -> dict:
    fam = skill.procedure["family"]
    tp = fp = fn = tn = 0
    for r in rows:
        act = screen(
            skill,
            TargetContext(name=r["repo"], fingerprints={}, issue_text=r["problem_statement"] or ""),
        ).in_scope
        has = fam in edit_patterns(parse_patch(r["patch"] or ""))
        tp += act and has
        fp += act and not has
        fn += (not act) and has
        tn += (not act) and not has
    n = tp + fp + fn + tn
    return {
        "n": n,
        "activation_rate": (tp + fp) / n if n else 0.0,
        "family_rate": (tp + fn) / n if n else 0.0,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "lift": (tp / (tp + fp)) / ((tp + fn) / n) if tp + fp and tp + fn else None,
        "activated_tasks": tp + fp,
    }


def main() -> int:
    skills = [Skill.load(p) for p in sorted(Path("configs/skills").glob("*.json"))]
    skills = [s for s in skills if s.procedure.get("family")]
    train, test = load("train"), load("test")
    train_repos = {r["repo"] for r in train}
    test = [r for r in test if r["repo"] not in train_repos]
    out = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_train": len(train),
        "n_test": len(test),
        "skills": {},
    }
    for s in skills:
        out["skills"][s.id] = {
            "family": s.procedure["family"],
            "train": confusion(s, train),
            "test": confusion(s, test),
        }
        print(s.id, json.dumps(out["skills"][s.id]))
    Path("data").mkdir(exist_ok=True)
    Path("data/activation.json").write_text(json.dumps(out, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
