"""Audit of the cost-driven stop of C10 (docs/preregistration_main.md section 43, note 43-4). 0 USD.

  python scripts/c10_stop_audit.py --prefix c10 --part all70 --out results/c10_stop_audit.json

Checks, each from the result files alone:
  1. predictability: in every arm, the guard of scripts/f1_probe.py (stop before a task when
     spent + cost_limit > cap) is replayed from the per-run cost_usd; the recorded spend equals
     the sum of per-run costs, no run started after the guard would have stopped it, and an arm
     with fewer runs than tasks had spent + cost_limit > cap after its last run. Then the stop
     index of an arm depends only on the costs of its earlier tasks (a stopping time in task
     order), and so does the minimum over the arms of a contrast.
  2. selection: the runs of every arm are the first runs of one fixed task order, so a contrast
     uses the first n tasks of the registered order; only n depends on the spend.
  3. the E path of every contrast over k = 1..n (fixed lam, theta), the first k with E >= the
     threshold and the smallest E after it; and E on the 34 test tasks, the registered smaller
     pool (section 43, "the 34-task version uses the first part"), whose membership is fixed
     before any data.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gatekeeper.eprocess import end_of_pool_log_e  # noqa: E402

CONTRASTS = {"main A-C": ("A", "C"), "A-B": ("A", "B"), "B-D": ("B", "D"), "C-D": ("C", "D")}


def guard_replay(d: dict) -> dict:
    cum, started_after_stop = 0.0, 0
    for r in d["runs"]:
        if cum + d["cost_limit"] > d["cap"]:
            started_after_stop += 1
        cum += r["cost_usd"]
    stopped_early = len(d["runs"]) < d["n_tasks"]
    return {
        "runs": len(d["runs"]),
        "n_tasks": d["n_tasks"],
        "spend_equals_sum_of_run_costs": abs(cum - d["spent_usd"]) < 1e-9,
        "runs_started_after_guard": started_after_stop,
        "stop_explained_by_guard": (not stopped_early) or (cum + d["cost_limit"] > d["cap"]),
    }


def fails(run: dict) -> int:
    return int(not (run.get("S") or {}).get("resolved"))


def audit(arms: dict[str, dict], lam: float, theta: float, threshold: float, n_fixed: int):
    out = {"lam": lam, "theta": theta, "threshold": threshold, "arms": {}, "contrasts": {}}
    longest = max(arms.values(), key=lambda d: len(d["runs"]))
    order = [r["instance_id"] for r in longest["runs"]]
    for name, d in arms.items():
        g = guard_replay(d)
        g["prefix_of_task_order"] = [r["instance_id"] for r in d["runs"]] == order[: len(d["runs"])]
        out["arms"][name] = g
    for cname, (x, y) in CONTRASTS.items():
        names = [f"{x}_skill", f"{x}_none", f"{y}_skill", f"{y}_none"]
        n = min(len(arms[a]["runs"]) for a in names)
        ds = []
        for i in range(n):
            zx = fails(arms[names[0]]["runs"][i]) - fails(arms[names[1]]["runs"][i])
            zy = fails(arms[names[2]]["runs"][i]) - fails(arms[names[3]]["runs"][i])
            ds.append((zx - zy) / 2)
        path = [math.exp(end_of_pool_log_e(ds[: k + 1], lam, theta)) for k in range(n)]
        first = next((k + 1 for k, e in enumerate(path) if e >= threshold), None)
        fixed = ds[:n_fixed] if n >= n_fixed else None
        out["contrasts"][cname] = {
            "n": n,
            "set_by_arm": min(names, key=lambda a: len(arms[a]["runs"])),
            "E_at_n": path[-1],
            "first_k_E_at_threshold": first,
            "min_E_after_first": min(path[first - 1 :]) if first else None,
            f"E_on_first_{n_fixed}": (
                math.exp(end_of_pool_log_e(fixed, lam, theta)) if fixed else None
            ),
            f"neg_pos_on_first_{n_fixed}": [sum(d < 0 for d in fixed), sum(d > 0 for d in fixed)]
            if fixed
            else None,
            "E_path": [round(e, 4) for e in path],
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--part", required=True)
    ap.add_argument("--lam", type=float, required=True)
    ap.add_argument("--theta", type=float, required=True)
    ap.add_argument("--threshold", type=float, required=True)
    ap.add_argument("--n-fixed", type=int, required=True)
    ap.add_argument("--results", type=Path, default=ROOT / "results")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    arms = {
        f"{v}_{s}": json.loads((a.results / f"{a.prefix}_{v}_{s}_{a.part}.json").read_text())
        for v in "ABCD"
        for s in ("none", "skill")
    }
    res = audit(arms, a.lam, a.theta, a.threshold, a.n_fixed)
    a.out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: v for k, v in res["contrasts"].items()}, default=str)[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
