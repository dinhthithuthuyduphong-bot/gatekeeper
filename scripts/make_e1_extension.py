"""E1 extension to n = 53 per E1 skill (docs/preregistration_e1.md, execution note 4; audit A38).

Same sampling rule as the registered design: for each E1 skill, the first N usable tasks in its
pre-fixed random order; the extension is tasks 41..53 of that order. The 40 tasks already in
configs/pools/e1_task_sets.json must be exactly the first 40 (checked).

The extension runs as its OWN stage (g1-e1x-s<seed>): 5 extension tasks already ran in E1 for
another skill, and re-running a task inside the same stage replaces ALL its earlier pairs (the
batch driver's merge rule, audit A18), which would delete those other skills' data. In a separate
stage every (skill, no-skill) pair is run in the same batch, and no skill shares a task between
the two stages. The harmful-by-construction skills and RQ1-mini keep their registered 40 tasks.
Writes configs/pools/e1x_selected.json and configs/pools/e1x_task_sets.json."""

from __future__ import annotations

import json
from pathlib import Path

E1_SKILLS = ["null-guard", "type-guard", "exception-handling"]
N_TOTAL = 53  # (z(1 - 0.025/3) + z(0.8))^2 * V / delta^2, V = 0.060, delta = 0.109 (A38)


def extension(pool: dict, usable: set[str], current: dict[str, list[str]]) -> dict[str, list[str]]:
    out = {}
    for sid in E1_SKILLS:
        order = [i for i in pool["random_order"][sid] if i in usable]
        if set(order[:40]) != set(current[sid]):
            raise SystemExit(f"{sid}: current 40 tasks are not the first 40 of the random order")
        if len(order) < N_TOTAL:
            raise SystemExit(f"{sid}: only {len(order)} usable tasks")
        out[sid] = order[40:N_TOTAL]
    return out


def main() -> int:
    pool = json.loads(Path("configs/pools/e1.json").read_text())
    usable = set(json.loads(Path("results/pool_validation/e1/summary.json").read_text())["usable"])
    current = json.loads(Path("configs/pools/e1_task_sets.json").read_text())
    ext = extension(pool, usable, current)
    union = sorted({i for v in ext.values() for i in v})
    Path("configs/pools/e1x_task_sets.json").write_text(json.dumps(ext, indent=1) + "\n")
    Path("configs/pools/e1x_selected.json").write_text(
        json.dumps(
            {
                "_comment": "E1 extension (tasks 41..53 per E1 skill), its own stage g1-e1x",
                "dataset": pool["dataset"],
                "instances": union,
                "per_skill": ext,
            },
            indent=1,
        )
        + "\n"
    )
    print({k: len(v) for k, v in ext.items()}, "union", len(union))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
