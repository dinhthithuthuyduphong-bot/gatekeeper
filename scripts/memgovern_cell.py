"""MemGovern cell (preregistration_main.md, notes M-1..M-3): Gatekeeper decision, cost check.

Trials are the 109 E2 tasks in E2's seed-41 order (model_unchanged_check.e2_tasks). Both arms
(none, memgovern) are new runs (section 5 failed, so no pairing with E2). Z of a task =
1[unresolved | memgovern] - 1[unresolved | none] (analyze_g1_final.z_resolved; negative = helps).

The e-process (BettingEProcess, theta = 0, c = 0.5, alpha_cell = 0.025 / 9) consumes Z in E2
order, over the longest PREFIX of that order whose tasks have all been run (so the order the bets
see is fixed in advance, whatever order the parallel shards finish in). A task that was run but has
no pair (infrastructure failure, per_task_mean rule) is skipped, as in E1/E2.

  python scripts/memgovern_cell.py --results-dir results/pilot --prefix mg-s41 \
      --alpha 0.0027777777777777779 --theta 0 --c 0.5 --cap 24.5 --out results/mg_cell.json

Exit 0 always; the JSON says `admit`, `stop_admit` (stop the cell: E crossed 1/alpha) and
`stop_cost` (after >= 10 tasks run: spent + mean cost per task x tasks left > cap).
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

COST_CHECK_AFTER = 10  # registered (draft section 11e): "Sau 10 trial đầu"
SKILL = "memgovern"


def merged_runs(results_dir: Path, prefix: str) -> list[dict]:
    """One merged result per shard (run_batched_pilot.merge: a later part replaces a re-run).

    merge() also WRITES <RESULTS>/<name>.json; the analysis only reads, so RESULTS is pointed at a
    temporary directory while merging (A99: a test had written fake merged files into results/)."""
    import tempfile

    import run_batched_pilot as rbp

    shards: dict[str, list[tuple[int, Path]]] = defaultdict(list)
    # <prefix>-f<first task of the dispatch>-k<shard>-p<part> (memgovern-trial.yml, cell modes)
    pat = re.compile(rf"^({re.escape(prefix)}(?:-f\d+)?-k\d+)-p(\d+)\.json$")
    for f in results_dir.iterdir():
        m = pat.match(f.name)
        if m:
            shards[m.group(1)].append((int(m.group(2)), f))
    saved = rbp.RESULTS
    with tempfile.TemporaryDirectory() as tmp:
        rbp.RESULTS = Path(tmp)
        try:
            return [
                rbp.merge(name, [f for _, f in sorted(parts)])
                for name, parts in sorted(shards.items())
            ]
        finally:
            rbp.RESULTS = saved


def analyse(
    order: list[str], runs: list[dict], alpha: float, theta: float, c: float, cap: float
) -> dict:
    from analyze_g1_final import z_resolved

    from gatekeeper.eprocess import BettingEProcess

    run_tasks: set[str] = set()
    z: dict[str, float] = {}
    spent = 0.0
    for r in runs:
        run_tasks |= set(r.get("instances", []))
        pairs = r.get("skills", {}).get(SKILL, {}).get("pairs", [])
        for t, v in z_resolved(pairs).items():
            if t in z:
                raise SystemExit(f"{t} paired in two shards")
            z[t] = v
        spent += float(r.get("spent_usd") or 0.0)
    unknown = (run_tasks | set(z)) - set(order)
    if unknown:
        raise SystemExit(f"tasks outside the cell: {sorted(unknown)[:5]}")
    prefix = 0
    while prefix < len(order) and order[prefix] in run_tasks:
        prefix += 1
    ep = BettingEProcess(theta=theta, alpha=alpha, c=c)
    path, crossed_at, used = [], None, []
    for t in order[:prefix]:
        if t not in z:
            continue  # run, but no pair (infrastructure failure): skipped, as in E1/E2
        ep.update(z[t])
        used.append(t)
        path.append(round(ep.log_e, 6))
        if crossed_at is None and ep.crossed:
            crossed_at = len(used)
    zs = [z[t] for t in used]
    n_run = len(run_tasks)
    per_task = spent / n_run if n_run else 0.0
    left = len(order) - n_run
    return {
        "n_cell": len(order),
        "n_run": n_run,
        "prefix_run": prefix,
        "n_trials": len(used),
        "n_no_pair": prefix - len(used),
        "alpha_cell": alpha,
        "log_threshold": math.log(1 / alpha),
        "log_e_final": path[-1] if path else 0.0,
        "log_e_max": max(path) if path else 0.0,
        "crossed_at_trial": crossed_at,
        "admit": crossed_at is not None,
        "b_helps": sum(1 for v in zs if v < 0),
        "c_hurts": sum(1 for v in zs if v > 0),
        "mean_z": sum(zs) / len(zs) if zs else None,
        "spent_usd": spent,
        "cost_per_task_usd": per_task,
        "projected_rest_usd": per_task * left,
        "cap_usd": cap,
        "stop_admit": crossed_at is not None,
        "stop_cost": n_run >= COST_CHECK_AFTER and spent + per_task * left > cap,
        "log_e_path": path,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", required=True, type=Path)
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--alpha", required=True, type=float)
    ap.add_argument("--theta", required=True, type=float)
    ap.add_argument("--c", required=True, type=float)
    ap.add_argument(
        "--cap", required=True, type=float, help="cell cap in USD (spend so far included)"
    )
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    from model_unchanged_check import e2_tasks

    out = analyse(e2_tasks(), merged_runs(a.results_dir, a.prefix), a.alpha, a.theta, a.c, a.cap)
    a.out.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "log_e_path"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
