"""E2 task set (docs/preregistration_e2.md section 3): usable tasks (validated pool) on which
XRepoSkill's own selection chose >= 1 rule, in the pool's pre-fixed RANDOM order.

  python scripts/make_e2_selection.py --guidance <scratchpad>/e2work/guidance_by_instance.json

Inputs: configs/pools/e2.json (random_order), results/pool_validation/e2/summary.json (usable),
results/e2_selection.json (rule ids per task, scripts/xreposkill_select.py).
Writes configs/pools/e2_selected.json and configs/pools/e2_task_sets.json. Stops (no output) if
any check fails: every checked task must have a selection result without error, and every task in
the set must have non-empty guidance (else the skill arm would equal the no-skill arm)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def build(pool: dict, usable: set[str], selection: dict, guidance: dict) -> list[str]:
    per = selection["per_task"]
    missing = sorted(usable - set(per))
    if missing:
        raise SystemExit(f"{len(missing)} usable tasks have no selection result: {missing[:5]}")
    errors = sorted(i for i in usable if per[i]["error"])
    if errors:
        raise SystemExit(f"selection errors for {errors[:5]}")
    chosen = [i for i in pool["random_order"] if i in usable and per[i]["rule_ids"]]
    no_text = [i for i in chosen if not (guidance.get(i) or "").strip()]
    if no_text:
        raise SystemExit(f"activated tasks without guidance text: {no_text[:5]}")
    extra = sorted((set(guidance) & usable) - set(chosen))  # guidance but no rule id recorded
    if extra:
        raise SystemExit(f"guidance for tasks outside the set: {extra[:5]}")
    return chosen


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--guidance", required=True, type=Path)
    a = ap.parse_args()
    pool = json.loads(Path("configs/pools/e2.json").read_text())
    usable = set(json.loads(Path("results/pool_validation/e2/summary.json").read_text())["usable"])
    selection = json.loads(Path("results/e2_selection.json").read_text())
    guidance = json.loads(a.guidance.read_text())
    chosen = build(pool, usable, selection, guidance)
    per = selection["per_task"]
    n_empty = sum(1 for i in usable if not per[i]["rule_ids"])
    out = {
        "_comment": "E2 task set: usable AND >= 1 rule selected, in the pool's random order "
        "(docs/preregistration_e2.md section 3). Fixed before any agent run.",
        "dataset": pool["dataset"],
        "harness": pool["harness"],
        "n_usable": len(usable),
        "n_no_rule_selected": n_empty,
        "instances": chosen,
    }
    Path("configs/pools/e2_selected.json").write_text(json.dumps(out, indent=1) + "\n")
    Path("configs/pools/e2_task_sets.json").write_text(
        json.dumps({"xreposkill": chosen}, indent=1) + "\n"
    )
    print({"n_usable": len(usable), "activated": len(chosen), "no_rule": n_empty})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
