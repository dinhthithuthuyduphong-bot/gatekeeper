"""P1-P3 of docs/preregistration_main.md section 9 (0 USD). Writes results/plasmode_extra.json.

python scripts/plasmode_extra.py --xrepo <XRepoSkill clone at 26fd703> --reps 1000
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import gates  # noqa: E402
import plasmode_real as pr  # noqa: E402

ALPHA = 0.025
SEED = 20271105
LOOK_EVERY = 10  # P1: interim look every 10 trials (section 9)
SSKB = Path("data/external/swe-skills-bench/ALL_combined_cells.csv")


def p1(score, tasks, base_r, reps: int) -> dict:
    """Continuous monitoring: baselines admit if their criterion holds at ANY look."""
    k, n = len(pr.DELTAS), 200
    a_cell = ALPHA / k
    rng = np.random.default_rng(SEED)
    rules = ["gatekeeper", "plug_in", "b_x2", "b_gall"]
    adm = {r: np.zeros((reps, k), bool) for r in rules}
    looks = list(range(LOOK_EVERY, n + 1, LOOK_EVERY))
    for rep in range(reps):
        cells = [pr.make_cell(rng, tasks, n, d, base_r, None) for d in pr.DELTAS]
        p = {str(c): gates.gatekeeper_p(z, 0.0, a_cell, n) for c, (z, _) in enumerate(cells)}
        gk = gates.holm(p, ALPHA)
        for c, (z, pairs) in enumerate(cells):
            adm["gatekeeper"][rep, c] = gk[str(c)]
            adm["plug_in"][rep, c] = any(gates.plug_in(z[:t]) for t in looks)
            adm["b_gall"][rep, c] = any(gates.b_g(z[:t], None) for t in looks)
            adm["b_x2"][rep, c] = any(gates.b_x2(pairs[:t], score) for t in looks)
    return summarise(adm, pr.DELTAS)


def summarise(adm: dict, deltas: list[float]) -> dict:
    bad = [c for c, d in enumerate(deltas) if d <= 0]
    good = [c for c, d in enumerate(deltas) if d > 0]
    return {
        r: {
            "fwer": float(m[:, bad].any(axis=1).mean()),
            "false_admit_rate": float(m[:, bad].mean()),
            "coverage": float(m[:, good].mean()),
        }
        for r, m in adm.items()
    }


def sskb_cells() -> dict[str, list[tuple[str, float]]]:
    """(config, skill) -> [(batch, Z = (none - one)/100)]; Z > 0 means the skill hurt."""
    cells: dict[str, list[tuple[str, float]]] = {}
    for row in csv.DictReader(SSKB.open()):
        z = (float(row["none_pass_rate"]) - float(row["one_pass_rate"])) / 100.0
        cells.setdefault(f"{row['harness_model']}|{row['skill']}", []).append(
            (row["requirement_batch"], z)
        )
    return cells


def mom_tau2(cells) -> tuple[float, float]:
    """Mean effect and between-cell variance, method of moments with equal weights (the
    DerSimonian-Laird family, Veroniki et al. 2016): tau^2 = Var(y_i) - mean(s_i^2 / m_i).
    Equal weights because many cells have zero within-cell variance (DL weights 1/v undefined)."""
    y = np.array([np.mean([z for _, z in v]) for v in cells.values()])
    s = np.array([np.var([z for _, z in v], ddof=1) / len(v) for v in cells.values()])
    return float(y.mean()), max(0.0, float(y.var(ddof=1) - s.mean()))


def p2(score, tasks, base_r, mu_z: float, tau2: float, reps: int) -> dict:
    lo, hi = -base_r, 1 - base_r  # keep the spike probability <= 1
    out = {}
    for n in (109, 200):
        rng = np.random.default_rng(SEED)
        k = 9
        a_cell = ALPHA / k
        rules = ["gatekeeper", "plug_in", "b_x1", "b_x2", "b_g3", "b_gall"]
        tot = {r: {"bad_admitted": 0, "good_admitted": 0, "delta_sum": 0.0} for r in rules}
        n_bad = n_good = 0
        for _ in range(reps):
            ds = np.clip(rng.normal(-mu_z, np.sqrt(tau2), k), lo + 1e-9, hi - 1e-9)
            cells = [pr.make_cell(rng, tasks, n, float(d), base_r, None) for d in ds]
            dec = [gates.decide_cell(z, prs, 0.0, a_cell, n, score) for z, prs in cells]
            gk = gates.holm({str(c): dec[c]["gatekeeper_p"] for c in range(k)}, ALPHA)
            n_bad += int((ds <= 0).sum())
            n_good += int((ds > 0).sum())
            for c in range(k):
                for r in rules:
                    a = gk[str(c)] if r == "gatekeeper" else bool(dec[c][r])
                    if a:
                        tot[r]["bad_admitted" if ds[c] <= 0 else "good_admitted"] += 1
                        tot[r]["delta_sum"] += float(ds[c])
        cells_total = reps * k
        out[str(n)] = {
            "share_cells_delta_le_0": n_bad / cells_total,
            **{
                r: {
                    "bad_admitted_per_100_cells": 100 * v["bad_admitted"] / cells_total,
                    "good_admitted_per_100_cells": 100 * v["good_admitted"] / cells_total,
                    "share_of_beneficial_admitted": v["good_admitted"] / max(1, n_good),
                    "mean_delta_of_admitted": v["delta_sum"]
                    / max(1, v["bad_admitted"] + v["good_admitted"]),
                }
                for r, v in tot.items()
            },
        }
    return out


def p3(cells) -> dict:
    screen_b = {f"batch{i}" for i in range(1, 6)}
    data = {}
    for c, v in cells.items():
        s = [z for b, z in sorted(v) if b in screen_b]
        h = [z for b, z in v if b not in screen_b]
        data[c] = (s, h)
    a_cell = ALPHA / len(data)
    gk = gates.holm({c: gates.gatekeeper_p(s, 0.0, a_cell, 5) for c, (s, _) in data.items()}, ALPHA)
    rules = {
        "gatekeeper": lambda c, s: gk[c],
        "plug_in": lambda c, s: gates.plug_in(s),
        "b_g3": lambda c, s: gates.b_g(s, 3),
        "b_gall": lambda c, s: gates.b_g(s, None),
        "b_x1": lambda c, s: True,
    }
    rng = np.random.default_rng(SEED)
    out = {"cells": len(data)}
    for r, f in rules.items():
        held = [np.mean(h) for c, (s, h) in data.items() if f(c, s)]
        if held:
            boots = [np.mean(rng.choice(held, len(held))) for _ in range(2000)]
            ci = [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]
        else:
            ci = None
        out[r] = {
            "admitted": len(held),
            "held_out_mean_z": float(np.mean(held)) if held else None,
            "ci95": ci,
            "admitted_with_held_out_harm": int(sum(1 for x in held if x > 0)),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xrepo", type=Path, required=True)
    ap.add_argument("--reps", type=int, required=True)
    a = ap.parse_args()
    score = gates.load_xreposkill_score(a.xrepo)
    tasks = pr.no_skill_runs()
    base_r = float(np.mean([np.mean(r) for r in tasks]))
    cells = sskb_cells()
    mu_z, tau2 = mom_tau2(cells)
    out = {"base_solve_rate": base_r, "sskb_mu_z": mu_z, "sskb_tau2": tau2}
    out["P3"] = p3(cells)
    print("P3", json.dumps(out["P3"]), flush=True)
    out["P2"] = p2(score, tasks, base_r, mu_z, tau2, a.reps)
    print("P2", json.dumps(out["P2"]), flush=True)
    out["P1"] = p1(score, tasks, base_r, a.reps)
    print("P1", json.dumps(out["P1"]), flush=True)
    Path("results/plasmode_extra.json").write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
