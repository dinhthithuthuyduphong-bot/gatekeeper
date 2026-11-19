"""Caps of W7's learning run (docs/preregistration_main.md section 45, note 45-5), by lesson L66.

  python kaggle/scripts/w7_caps.py --run-zip kaggle/results/w7/w7_A_measure2_run.zip \
      --mj-zip kaggle/results/w7/w7_A_measure2_mjprobe.zip --pairs-a 62 --pairs-b 24 \
      --spent-a 1.844426 --quantile 0.999 --reps 20000 --seed 4506 --workers 3 \
      --max-call-chars 35000 --out kaggle/results/w7/w7_caps.json

Simulated spend of the rest of the run of one pool:
  discover  each remaining pair draws, for each of the three analysts, one measured (cost,
            candidates) outcome of the same analyst (re-prompts included), with replacement;
  merge     XRepoSkill merges per category in batches of `batch_size` (merge.py); each
            candidate draws a category from the measured candidates; a call costs a + b * batch,
            a and b fitted by least squares on the measured merge calls;
  judge     one call per candidate (an upper bound: merging only lowers the number of rules),
            each drawing a measured judge call cost.
Cap of a pool = spent so far + the `quantile` of its simulated spend + a reserve of `workers`
worst-case calls (the guard of w7_run_cell.py refuses a call when spent + reserved + worst
case > cap, so up to `workers` calls are in flight at the end), rounded up to 3 decimals.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import random
import zipfile
from collections import defaultdict
from pathlib import Path

PIN, POUT, MAX_OUT, CHARS_PER_TOKEN = 2e-6, 12e-6, 24000, 3.09  # as in w7_run_cell.py
CATEGORIES = ("lookup", "verification", "replay", "search_recipe")  # XRepoSkill schemas.py
BATCH = 32  # XRepoSkill configs/pipeline.yaml merge.batch_size at 26fd703


def usd(row: dict) -> float:
    return row["in_tokens"] * PIN + row["out_tokens"] * POUT


def jsonl(z: zipfile.ZipFile, name: str) -> list[dict]:
    return [json.loads(x) for x in io.TextIOWrapper(z.open(name)) if x.strip()]


def measured(run_zip: Path, mj_zip: Path) -> dict:
    with zipfile.ZipFile(run_zip) as z:
        cost = jsonl(z, "cost_log.jsonl")
        cands = [
            c
            for n in z.namelist()
            if n.startswith("candidates/") and n.endswith(".jsonl") and "failed" not in n
            for c in jsonl(z, n)
        ]
    slot = defaultdict(float)
    for r in cost:
        if r["stage"] == "discover":
            slot[(r["extra"]["pair_id"], r["sub"])] += usd(r)
    sub_of = {"process_delta": "A_diff", "skipped_step": "A-", "discipline_observer": "A+"}
    ncand = defaultdict(int)
    for c in cands:
        ncand[(c["pair_id"], sub_of[c["analyst_type"]])] += 1
    by_sub = defaultdict(list)
    for (pid, sub), v in slot.items():
        by_sub[sub].append((v, ncand[(pid, sub)]))
    with zipfile.ZipFile(mj_zip) as z:
        mj = [r for r in jsonl(z, "cost_log.jsonl") if r["stage"] in ("merge", "judge")]
    merge = [(r["extra"]["batch_size"], usd(r)) for r in mj if r["stage"] == "merge"]
    judge = [usd(r) for r in mj if r["stage"] == "judge"]
    return {
        "slots": dict(by_sub),
        "categories": [c["category"] for c in cands],
        "merge": merge,
        "judge": judge,
        "n_pairs_measured": len({p for p, _ in slot}),
    }


def fit(points: list[tuple[int, float]]) -> tuple[float, float]:
    n = len(points)
    mx = sum(x for x, _ in points) / n
    my = sum(y for _, y in points) / n
    sxx = sum((x - mx) ** 2 for x, _ in points)
    b = sum((x - mx) * (y - my) for x, y in points) / sxx
    return my - b * mx, b


def simulate(m: dict, pairs: int, cands_so_far: int, reps: int, rng: random.Random) -> list[float]:
    a, b = fit(m["merge"])
    out = []
    for _ in range(reps):
        total, n = 0.0, cands_so_far
        for _ in range(pairs):
            for outcomes in m["slots"].values():
                c, k = rng.choice(outcomes)
                total += c
                n += k
        per_cat = defaultdict(int)
        for _ in range(n):
            per_cat[rng.choice(m["categories"])] += 1
        for k in per_cat.values():
            full, rest = divmod(k, BATCH)
            total += full * (a + b * BATCH) + ((a + b * rest) if rest else 0.0)
        total += sum(rng.choice(m["judge"]) for _ in range(n))
        out.append(total)
    return sorted(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    for k, t in (
        ("--run-zip", Path),
        ("--mj-zip", Path),
        ("--pairs-a", int),
        ("--pairs-b", int),
        ("--spent-a", float),
        ("--quantile", float),
        ("--reps", int),
        ("--seed", int),
        ("--workers", int),
        ("--max-call-chars", int),
        ("--out", Path),
    ):
        ap.add_argument(k, type=t, required=True)
    a = ap.parse_args()
    m = measured(a.run_zip, a.mj_zip)
    rng = random.Random(a.seed)
    reserve = a.workers * (a.max_call_chars / CHARS_PER_TOKEN * PIN + MAX_OUT * POUT)
    done_a = m["n_pairs_measured"]
    res = {}
    for pool, pairs, spent, cands in (
        ("A", a.pairs_a - done_a, a.spent_a, len(m["categories"])),
        ("B", a.pairs_b, 0.0, 0),
    ):
        tots = simulate(m, pairs, cands, a.reps, rng)
        q = tots[math.ceil(a.quantile * a.reps) - 1]
        res[pool] = {
            "pairs_left": pairs,
            "spent_so_far": spent,
            "expected_rest": sum(tots) / a.reps,
            "quantile_rest": q,
            "reserve": reserve,
            "cap": math.ceil((spent + q + reserve) * 1000) / 1000,
        }
    out = {
        "_registration": "docs/preregistration_main.md section 45, note 45-5",
        "quantile": a.quantile,
        "reps": a.reps,
        "seed": a.seed,
        "measured": {
            "pairs": done_a,
            "slots_per_analyst": {k: len(v) for k, v in m["slots"].items()},
            "candidates": len(m["categories"]),
            "merge_fit_a_b": fit(m["merge"]),
            "judge_calls": len(m["judge"]),
        },
        "pools": res,
        "cap_total": round(res["A"]["cap"] + res["B"]["cap"], 3),
        "expected_total": round(
            res["A"]["spent_so_far"] + res["A"]["expected_rest"] + res["B"]["expected_rest"], 3
        ),
    }
    a.out.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
