"""E1 task sets from the validated pool (docs/preregistration_e1.md): for each skill, the first
N_PER_SKILL USABLE tasks in its pre-fixed random order; the harmful-by-construction skills get the
first N tasks of the union in their own random order (scripts/make_harm_skills.py).
Writes configs/pools/e1_selected.json (instances = union) and configs/pools/e1_task_sets.json."""

from __future__ import annotations

import json
import random
from pathlib import Path

HARM = ["harm-swallow-exceptions", "harm-minimal-edit", "harm-skip-verification"]
HARM_SEED = "2027-harm"


def main() -> int:
    pool = json.loads(Path("configs/pools/e1.json").read_text())
    usable = set(json.loads(Path("results/pool_validation/e1/summary.json").read_text())["usable"])
    n = pool["n_per_skill"]
    sets: dict[str, list[str]] = {}
    for sid, order in pool["random_order"].items():
        chosen = [i for i in order if i in usable][:n]
        if len(chosen) < n:
            raise SystemExit(f"{sid}: only {len(chosen)} usable among validated; validate more")
        sets[sid] = sorted(chosen)
    union = sorted({i for ids in sets.values() for i in ids})
    rnd = list(union)
    random.Random(HARM_SEED).shuffle(rnd)
    harm_ids = sorted(rnd[:n])
    for sid in HARM:
        sets[sid] = harm_ids
    Path("configs/pools/e1_selected.json").write_text(
        json.dumps({"dataset": pool["dataset"], "instances": union, "per_skill": sets}, indent=1)
        + "\n"
    )
    Path("configs/pools/e1_task_sets.json").write_text(json.dumps(sets, indent=1) + "\n")
    print({k: len(v) for k, v in sets.items()}, "union", len(union))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
