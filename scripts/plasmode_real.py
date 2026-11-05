"""Plasmode on the real E1/E2 runs (docs/preregistration_main.md section 8). 0 USD.

Null background with an exactly zero effect: two NO-SKILL runs of the same task (different seeds)
form an A/A pair (one plays "with skill"). Known effects are spiked into the "with skill" run:
beneficial = an unresolved run becomes resolved with probability pi; harmful = a resolved run
becomes unresolved with probability pi. Each replicate is a family of K = 9 cells (3 harmful, 3
null, 3 beneficial); every rule of scripts/gates.py sees the same trials. Writes
results/plasmode_real.json.

  python scripts/plasmode_real.py --xrepo <XRepoSkill clone at 26fd703> --reps 1000
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import analyze_g1_final as gf  # noqa: E402
import gates  # noqa: E402

RUNS = [f"g1-e1all-s{s}" for s in (41, 51, 61)] + [f"g2-e2-s{s}" for s in (41, 51, 61)]
DELTAS = [-0.20, -0.10, -0.05, 0.0, 0.0, 0.0, 0.10, 0.20, 0.30]  # solve-rate change, section 8
NS = [25, 50, 109, 200]
ALPHA = 0.025  # one-sided family level (ICH E9)
SEED = 20271105


def no_skill_runs() -> list[list[int]]:
    """Per task: resolved (0/1) of every no-skill run (one per seed), with the REGISTERED endpoint:
    resolved <=> loss == 0 (F = 0 and R = 0, SWE-bench "resolved"; analyze_g1_final.resolved).
    An earlier version used loss < 0.5, which also counted runs that broke PASS_TO_PASS (A76)."""
    by_task: dict[str, dict[str, int]] = {}
    for name in RUNS:
        d = json.loads(Path(f"results/pilot/{name}.json").read_text())
        stage = name.rsplit("-s", 1)[0]
        for sk in d["skills"].values():
            for p in sk["pairs"]:
                key = f"{stage}:{p['instance_id']}"
                by_task.setdefault(key, {})[name] = int(gf.resolved(p["loss_without"]))
    return [list(v.values()) for v in by_task.values() if len(v) >= 2]


def make_cell(rng, tasks, n, delta, base_r, conc):
    """n trials: (z, (r_with, r_without, stratum)) with the spiked effect `delta`."""
    z, pairs = [], []
    for t in rng.integers(0, len(tasks), n):
        runs = tasks[t]
        i, j = rng.choice(len(runs), 2, replace=False)
        rt, rc = runs[i], runs[j]
        if delta > 0:
            pi = delta / (1 - base_r)
            if conc:
                pi = rng.beta(pi * conc, (1 - pi) * conc)
            if rt == 0 and rng.random() < pi:
                rt = 1
        elif delta < 0:
            pi = -delta / base_r
            if conc:
                pi = rng.beta(pi * conc, (1 - pi) * conc)
            if rt == 1 and rng.random() < pi:
                rt = 0
        z.append(float((1 - rt) - (1 - rc)))
        pairs.append((rt, rc, f"t{len(pairs)}"))
    return z, pairs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xrepo", type=Path, required=True)
    ap.add_argument("--reps", type=int, required=True)
    a = ap.parse_args()
    score = gates.load_xreposkill_score(a.xrepo)
    tasks = no_skill_runs()
    base_r = float(np.mean([np.mean(r) for r in tasks]))
    assert max(DELTAS) / (1 - base_r) <= 1 and -min(DELTAS) / base_r <= 1, "spike prob > 1"
    k = len(DELTAS)
    a_cell = ALPHA / k
    out = {
        "n_tasks": len(tasks),
        "base_solve_rate": base_r,
        "K": k,
        "alpha": ALPHA,
        "deltas": DELTAS,
    }
    rules = ["gatekeeper", "plug_in", "b_x1", "b_x2", "b_g3", "b_gall"]
    for conc in (None, 2.0):
        res = {}
        for n in NS:
            rng = np.random.default_rng(SEED)
            adm = {r: np.zeros((a.reps, k), bool) for r in rules}
            for rep in range(a.reps):
                cells = [make_cell(rng, tasks, n, d, base_r, conc) for d in DELTAS]
                dec = [gates.decide_cell(z, pr, 0.0, a_cell, n, score) for z, pr in cells]
                gk = gates.holm({str(c): dec[c]["gatekeeper_p"] for c in range(k)}, ALPHA)
                for c in range(k):
                    adm["gatekeeper"][rep, c] = gk[str(c)]
                    for r in rules[1:]:
                        adm[r][rep, c] = bool(dec[c][r])
            bad = [c for c, d in enumerate(DELTAS) if d <= 0]
            good = [c for c, d in enumerate(DELTAS) if d > 0]
            res[str(n)] = {
                r: {
                    "false_admit_rate": float(m[:, bad].mean()),
                    "fwer": float(m[:, bad].any(axis=1).mean()),
                    "coverage": float(m[:, good].mean()),
                    "admit_by_delta": [float(m[:, c].mean()) for c in range(k)],
                }
                for r, m in adm.items()
            }
            print(
                conc,
                n,
                {r: (round(v["fwer"], 3), round(v["coverage"], 3)) for r, v in res[str(n)].items()},
                flush=True,
            )
        out["uniform" if conc is None else "heterogeneous_beta2"] = res
    out["mcse_max"] = float(np.sqrt(0.25 / a.reps))
    Path("results/plasmode_real.json").write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
