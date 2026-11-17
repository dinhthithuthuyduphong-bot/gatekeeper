"""Analysis of C10 (docs/preregistration_main.md section 43), written before any paid run. 0 USD.

  python scripts/c10_analysis.py --prefix c10 --parts test34 extra36 --out results/c10_analysis.json

Z_i^v = 1[skill arm of variant v fails] - 1[no-skill arm of v fails] (SWE-smith grading, field S).
Contrast X - Y: D_i = (Z_i^X - Z_i^Y) / 2 over the tasks complete (no infra_error, not missing) in
the four arms involved; D_i < 0 means the skill gains more in X than in Y.
  main      A - C   (leaked pre-bug code present vs absent; same commits, same messages)
  secondary B - D   (bug diff without the message vs no bug commit)
            A - B   (message "Bug Patch" vs neutral message, diff present)
            C - D   (empty "Bug Patch" commit vs no bug commit)
  interaction (A - B) - (C - D): mean and bootstrap interval only
End-of-pool test: lam = 0.5, theta = 0, reject when E >= 40
(section 43; docs/method_end_of_pool.md).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gatekeeper.eprocess import end_of_pool_log_e  # noqa: E402

VARIANTS = ("A", "B", "C", "D")
CONTRASTS = {"main A-C": ("A", "C"), "B-D": ("B", "D"), "A-B": ("A", "B"), "C-D": ("C", "D")}


def passed(run: dict) -> bool:
    return bool((run.get("S") or {}).get("resolved"))


def load(results: Path, prefix: str, parts: list[str]) -> tuple[dict, dict, list[str]]:
    """runs[(variant, arm)][instance_id] -> record; checks; task order (parts in the given order,
    each in its registered order: field 'order')."""
    runs: dict = {}
    checks: dict = {}
    order: list[str] = []
    for part in parts:
        part_order = None
        for v in VARIANTS:
            for s in ("none", "skill"):
                d = json.loads((results / f"{prefix}_{v}_{s}_{part}.json").read_text())
                bad_hist = [
                    r["instance_id"]
                    for r in d["runs"]
                    if "infra_error" not in r and not r.get("history_check")
                ]
                checks[f"{v}_{s}_{part}"] = {
                    "n_runs": len(d["runs"]),
                    "stopped": d.get("stopped"),
                    "spent_usd": d.get("spent_usd"),
                    "infra_error": sum("infra_error" in r for r in d["runs"]),
                    "crashed": sum(bool(r.get("crashed")) for r in d["runs"]),
                    "history_variant": d.get("history_variant"),
                    "runs_without_history_check": bad_hist,
                }
                if d.get("history_variant") != v:
                    raise SystemExit(f"{v}_{s}_{part}: history_variant {d.get('history_variant')}")
                for r in d["runs"]:
                    runs.setdefault((v, s), {})[r["instance_id"]] = r
                ids = [r["instance_id"] for r in sorted(d["runs"], key=lambda r: r["order"])]
                if part_order is None or len(ids) > len(part_order):
                    part_order = ids
        order += part_order
    return runs, checks, order


def z(runs: dict, v: str, ids: list[str]) -> np.ndarray:
    return np.array(
        [
            float(not passed(runs[(v, "skill")][i])) - float(not passed(runs[(v, "none")][i]))
            for i in ids
        ]
    )


def complete(runs: dict, vs: tuple[str, ...], order: list[str]) -> list[str]:
    def ok(v, s, i):
        r = runs.get((v, s), {}).get(i)
        return r is not None and "infra_error" not in r

    return [i for i in order if all(ok(v, s, i) for v in vs for s in ("none", "skill"))]


def boot(x: np.ndarray, reps: int, seed: int) -> list[float]:
    rng = np.random.default_rng(seed)
    m = x[rng.integers(0, x.size, size=(reps, x.size))].mean(axis=1)
    return [float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975))]


def analyse(
    runs: dict, order: list[str], lam: float, theta: float, threshold: float, reps: int, seed: int
) -> dict:
    out: dict = {"solved": {}, "contrasts": {}}
    ids_all = complete(runs, VARIANTS, order)
    for v in VARIANTS:
        for s in ("none", "skill"):
            ids = [i for i in order if i in runs.get((v, s), {})]
            out["solved"][f"{v}_{s}"] = [sum(passed(runs[(v, s)][i]) for i in ids), len(ids)]
    for name, (x, y) in CONTRASTS.items():
        ids = complete(runs, (x, y), order)
        d = (z(runs, x, ids) - z(runs, y, ids)) / 2
        le = end_of_pool_log_e(d.tolist(), lam=lam, theta=theta)
        out["contrasts"][name] = {
            "n": len(ids),
            "n_negative": int((d < 0).sum()),
            "n_positive": int((d > 0).sum()),
            "mean_D": float(d.mean()) if d.size else None,
            "bootstrap_95": boot(d, reps, seed) if d.size else None,
            "E": math.exp(le),
            "reject_at_threshold": bool(le >= math.log(threshold)),
        }
    za, zb, zc, zd = (z(runs, v, ids_all) for v in VARIANTS)
    inter = ((za - zb) - (zc - zd)) / 2
    out["interaction (A-B)-(C-D)"] = {
        "n": len(ids_all),
        "mean": float(inter.mean()) if inter.size else None,
        "bootstrap_95": boot(inter, reps, seed) if inter.size else None,
    }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--parts", nargs="+", required=True)
    ap.add_argument("--results", type=Path, default=ROOT / "results")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    runs, checks, order = load(a.results, a.prefix, a.parts)
    # registered values (section 43)
    res = analyse(runs, order, lam=0.5, theta=0.0, threshold=40.0, reps=10000, seed=4302)
    res["checks"] = checks
    res["task_order_n"] = len(order)
    a.out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: res[k] for k in ("solved", "contrasts")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
