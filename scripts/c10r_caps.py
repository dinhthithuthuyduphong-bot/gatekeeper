"""Caps of the C10 replication (docs/preregistration_main.md section 44), by lesson L66. 0 USD.

  python scripts/c10r_caps.py --prefix c10 --part all70 --quantile 0.999 --reps 20000 \
      --seed 4401 --cost-limit 0.30 --out configs/c10r.json

The guard of scripts/f1_probe.py stops an arm before a task when spent + cost_limit > cap, so an
arm runs all its tasks when its total spend on the first n - 1 tasks is at most cap - cost_limit.
Cap of an arm = the `quantile` of its simulated total spend over all tasks + cost_limit, rounded up
to 3 decimals (rounded up, L65). Simulated spend: each task's cost is drawn with replacement from
the costs the same arm had in the first run, in two strata (tasks 1-45, the shortest arm; tasks
46-70). An arm with fewer than MIN_LATER later costs observed draws its later costs from its
earlier ones times the largest later/earlier ratio of mean cost among the arms that have
MIN_LATER or more (later tasks cost more in every such arm).
"""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARMS = [f"{v}_{s}" for v in "ABCD" for s in ("none", "skill")]
MIN_LATER = 10  # fewer later costs than this: too few to resample (operational)


def caps(costs: dict[str, list[float]], n_tasks, split, quantile, reps, seed, cost_limit):
    later = {a: c[split:] for a, c in costs.items() if len(c[split:]) >= MIN_LATER}
    ratio = max(
        (sum(c[split:]) / len(c[split:])) / (sum(c[:split]) / split)
        for a, c in costs.items()
        if a in later
    )
    rng = random.Random(seed)
    out, detail = {}, {}
    for a in sorted(costs):
        early = costs[a][:split]
        late = later.get(a) or [x * ratio for x in early]
        tots = sorted(
            sum(rng.choice(early) for _ in range(split))
            + sum(rng.choice(late) for _ in range(n_tasks - split))
            for _ in range(reps)
        )
        q = tots[math.ceil(quantile * reps) - 1]
        out[a] = math.ceil((q + cost_limit) * 1000) / 1000
        detail[a] = {
            "expected": sum(tots) / reps,
            "quantile_spend": q,
            "later_costs": "observed" if a in later else f"earlier x {ratio:.3f}",
        }
    return out, detail, ratio


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--part", required=True)
    ap.add_argument("--quantile", type=float, required=True)
    ap.add_argument("--reps", type=int, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--cost-limit", type=float, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    runs = {
        x: json.loads((ROOT / "results" / f"{a.prefix}_{x}_{a.part}.json").read_text())["runs"]
        for x in ARMS
    }
    split = min(len(r) for r in runs.values())
    n_tasks = max(len(r) for r in runs.values())
    costs = {x: [r["cost_usd"] for r in rr] for x, rr in runs.items()}
    c, detail, ratio = caps(costs, n_tasks, split, a.quantile, a.reps, a.seed, a.cost_limit)
    base = json.loads((ROOT / "configs" / "c10.json").read_text())
    cfg = {
        "_registration": "docs/preregistration_main.md section 44",
        "neutral_message": base["neutral_message"],
        "seed": 61,
        "caps_all70": c,
        "_caps_rule": (
            f"scripts/c10r_caps.py: quantile {a.quantile} of the simulated spend over "
            f"{n_tasks} tasks + cost_limit {a.cost_limit}, rounded up; strata 1-{split} and "
            f"{split + 1}-{n_tasks}; later/earlier ratio {ratio:.3f}"
        ),
        "_caps_total": round(sum(c.values()), 3),
        "_expected_total": round(sum(d["expected"] for d in detail.values()), 3),
        "_detail": detail,
    }
    a.out.write_text(json.dumps(cfg, indent=1) + "\n")
    print(json.dumps({k: v for k, v in cfg.items() if k != "_detail"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
