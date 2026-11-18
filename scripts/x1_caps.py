"""Caps of X2' and X1' (docs/plan_vs_review.md section 11; sections 46-47), by lesson L66. 0 USD.

For every arm that runs a fixed number of tasks with scripts/f1_probe.py (whose guard stops before
a task when spent + cost_limit > cap): cap = the `quantile` of the simulated total spend over the
arm's n tasks + cost_limit, rounded up to 3 decimals (L65). Simulated spend: each task's cost is
drawn with replacement from the per-task costs of the measured run of the same kind (same agent
model, same environment, same skill status), named in ARMS. Learning runs keep the registered cap
of section 30 (14.50 USD per run, both halves), given here as a constant from that registration.

  python scripts/x1_caps.py --trial <worktree of origin/trial> --quantile 0.999 --reps 20000 \
      --seed 4701 --cost-limit 0.30 --total 20 --out configs/x1.json

Execution note 47-1 (18/11/2026): the Vertex total for the remaining paid runs is 20 USD, so the
one-commit learning run and its scoring arms (NOT_ON_VERTEX) move to Kaggle (section 48). They are
still simulated, in the same order with the same seed, so the caps of the arms that stay are the
same as before the note; they are marked "vertex": false and left out of the sums and guards.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

LEARN_CAP = 14.50  # section 30, "trần cộng dồn hai nửa 14,50" (approved 10/11/2026)
LEARN_EXPECTED = {"learn_ship": 12.254, "learn_lf": 10.990}  # section 25 step 2; section 30
# note 47-1: moved to Kaggle (section 48)
NOT_ON_VERTEX = {"score_lf_none", "score_lf_skill", "score_lfskill_on_ship34", "learn_lf"}
# arm -> (n tasks, measured run whose per-task costs are resampled, from trial or main)
ARMS = {
    "x2_none": (34, "main:results/c10r_A_none_all70.json"),
    "x2_skill": (34, "main:results/c10r_A_skill_all70.json"),
    "score_ship_none": (100, "trial:results/f1_probe.json"),
    "score_ship_skill": (100, "trial:results/f1_skill_probe.json"),
    "score_lf_none": (100, "trial:results/s25_leakfree_none.json"),
    "score_lf_skill": (100, "trial:results/s25_leakfree_skill.json"),
    "score_lfskill_on_ship34": (34, "main:results/s30_shipped34.json"),
}


def costs_of(spec: str, trial: Path) -> list[float]:
    where, path = spec.split(":", 1)
    base = trial if where == "trial" else Path(__file__).resolve().parents[1]
    runs = json.loads((base / path).read_text())["runs"]
    return [float(r["cost_usd"]) for r in runs if "infra_error" not in r]


def cap(costs: list[float], n: int, quantile: float, reps: int, rng, cost_limit: float):
    tot = sorted(sum(rng.choice(costs) for _ in range(n)) for _ in range(reps))
    q = tot[min(reps - 1, math.ceil(quantile * reps) - 1)]
    return math.ceil((q + cost_limit) * 1000) / 1000, sum(costs) / len(costs) * n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trial", required=True, type=Path)
    ap.add_argument("--quantile", required=True, type=float)
    ap.add_argument("--reps", required=True, type=int)
    ap.add_argument("--seed", required=True, type=int)
    ap.add_argument("--cost-limit", required=True, type=float)
    ap.add_argument("--total", required=True, type=float, help="approved cumulative cap (USD)")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    out = {"quantile": a.quantile, "reps": a.reps, "seed": a.seed, "cost_limit": a.cost_limit}
    arms = {}
    for name, (n, spec) in ARMS.items():
        c = costs_of(spec, a.trial)
        k, mean_total = cap(c, n, a.quantile, a.reps, rng, a.cost_limit)
        arms[name] = {
            "n": n,
            "source": spec,
            "n_costs": len(c),
            "expected": round(mean_total, 3),
            "cap": k,
        }
    for name, e in LEARN_EXPECTED.items():
        arms[name] = {"expected": e, "cap": LEARN_CAP, "source": "section 25 step 2 / section 30"}
    for name, v in arms.items():
        v["vertex"] = name not in NOT_ON_VERTEX
    out["arms"] = arms
    kept = [v for v in arms.values() if v["vertex"]]
    out["sum_expected"] = round(sum(v["expected"] for v in kept), 3)
    out["sum_caps"] = round(sum(v["cap"] for v in kept), 3)
    out["approved_total"] = a.total
    out["note"] = (
        "each arm's cap is a guard; before every arm the runner also stops when the cumulative "
        "actual spend of X2' and X1' plus the arm's cap would pass approved_total; arms with "
        "vertex false moved to Kaggle (note 47-1, section 48) and are not run by pilot.yml"
    )
    a.out.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
