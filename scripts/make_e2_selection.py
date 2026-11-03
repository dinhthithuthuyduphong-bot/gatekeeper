"""E2 task set (docs/preregistration_e2.md section 3): usable tasks (validated pool) on which
XRepoSkill's own selection chose >= 1 rule, in the pool's pre-fixed RANDOM order.

  python scripts/make_e2_selection.py --guidance <scratchpad>/e2work/guidance_by_instance.json \
      --blocks e2 e2b --n 121

Blocks (execution note 3): each tag is configs/pools/<tag>.json (a slice of the SAME random_order)
with results/pool_validation/<tag>/summary.json. The validated blocks together must be a prefix
of random_order (else "the first n" would skip unvalidated tasks), and only the first n activated
usable tasks in that order are kept (n from the resource constraint, section 3; no default).

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


def validated_prefix(order: list[str], blocks: list[list[str]]) -> int:
    """Length k such that the union of the blocks is exactly order[:k]; stops otherwise."""
    seen = [i for b in blocks for i in b]
    if len(seen) != len(set(seen)):
        raise SystemExit("a task is in two validation blocks")
    k = len(seen)
    if set(seen) != set(order[:k]):
        raise SystemExit("validation blocks are not a prefix of random_order")
    return k


def first_n(chosen: list[str], n: int) -> list[str]:
    if len(chosen) < n:
        raise SystemExit(
            f"only {len(chosen)} activated usable tasks < n = {n}: validate another block"
        )
    return chosen[:n]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--guidance", required=True, type=Path)
    ap.add_argument("--blocks", required=True, nargs="+")
    ap.add_argument("--n", required=True, type=int)
    a = ap.parse_args()
    pools = [json.loads(Path(f"configs/pools/{t}.json").read_text()) for t in a.blocks]
    pool = pools[0]
    if any(p["random_order"] != pool["random_order"] for p in pools):
        raise SystemExit("blocks come from different random orders")
    k = validated_prefix(pool["random_order"], [p["instances"] for p in pools])
    usable: set[str] = set()
    for t in a.blocks:
        usable |= set(
            json.loads(Path(f"results/pool_validation/{t}/summary.json").read_text())["usable"]
        )
    selection = json.loads(Path("results/e2_selection.json").read_text())
    guidance = json.loads(a.guidance.read_text())
    activated = build(pool, usable, selection, guidance)
    chosen = first_n(activated, a.n)
    per = selection["per_task"]
    n_empty = sum(1 for i in usable if not per[i]["rule_ids"])
    out = {
        "_comment": "E2 task set: usable AND >= 1 rule selected, in the pool's random order "
        "(docs/preregistration_e2.md section 3). Fixed before any agent run.",
        "dataset": pool["dataset"],
        "harness": pool["harness"],
        "blocks": a.blocks,
        "n_validated": k,
        "n_usable": len(usable),
        "n_activated": len(activated),
        "n_no_rule_selected": n_empty,
        "instances": chosen,
    }
    Path("configs/pools/e2_selected.json").write_text(json.dumps(out, indent=1) + "\n")
    Path("configs/pools/e2_task_sets.json").write_text(
        json.dumps({"xreposkill": chosen}, indent=1) + "\n"
    )
    print(
        {
            "validated": k,
            "n_usable": len(usable),
            "activated": len(activated),
            "kept": len(chosen),
            "no_rule": n_empty,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
