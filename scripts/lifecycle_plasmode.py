"""T1-T3 of docs/preregistration_main.md section 14 (0 USD). Writes results/lifecycle_plasmode.json.

All trials are real A/A no-skill pairs of E1/E2 (true effect exactly 0, registered endpoint
loss == 0) with known effects spiked in (plasmode_real.make_cell / spike).

  python scripts/lifecycle_plasmode.py --xrepo <XRepoSkill clone at 26fd703> --reps 1000
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import gates  # noqa: E402
import plasmode_real as pr  # noqa: E402

from gatekeeper.eprocess import BettingEProcess  # noqa: E402

ALPHA = 0.025
SEED = 20271108
LOOK = 10
# Library Drift section 5.1 (snapshot `library_drift_2026`): N_min = 100, tau = 0.10
LD_NMIN, LD_TAU = 100, 0.10


def e_bh(e: list[float], alpha: float) -> list[bool]:
    """e-BH (Wang & Ramdas 2022): reject the k* largest e, k* = max{k: e_(k) >= K/(alpha k)}."""
    k_tot = len(e)
    order = sorted(range(k_tot), key=lambda i: -e[i])
    kstar = 0
    for k in range(1, k_tot + 1):
        if e[order[k - 1]] >= k_tot / (alpha * k):
            kstar = k
    rej = [False] * k_tot
    for i in order[:kstar]:
        rej[i] = True
    return rej


def final_e(z, alpha_cell, n):
    ep = BettingEProcess(theta=0.0, alpha=alpha_cell)
    for v in z[:n]:
        ep.update(v)
    return float(np.exp(ep.log_e))


def t1(rng, tasks, base, score, reps):
    deltas = pr.DELTAS
    k, n = len(deltas), 200
    a_cell = ALPHA / k
    looks = list(range(LOOK, n + 1, LOOK))
    rules = [
        "gatekeeper",
        "e_bh_fdr",
        "b_x2_once",
        "b_x2_monitored",
        "b_g3",
        "b_gall_monitored",
        "plug_in_monitored",
        "b_x1",
    ]
    adm = {r: np.zeros((reps, k), bool) for r in rules}
    for rep in range(reps):
        cells = [pr.make_cell(rng, tasks, n, d, base, None) for d in deltas]
        p = {str(c): gates.gatekeeper_p(z, 0.0, a_cell, n) for c, (z, _) in enumerate(cells)}
        gk = gates.holm(p, ALPHA)
        eb = e_bh([final_e(z, a_cell, n) for z, _ in cells], ALPHA)
        for c, (z, prs) in enumerate(cells):
            adm["gatekeeper"][rep, c] = gk[str(c)]
            adm["e_bh_fdr"][rep, c] = eb[c]
            adm["b_x2_once"][rep, c] = gates.b_x2(prs, score)
            adm["b_x2_monitored"][rep, c] = any(gates.b_x2(prs[:t], score) for t in looks)
            adm["b_g3"][rep, c] = gates.b_g(z, 3)
            adm["b_gall_monitored"][rep, c] = any(gates.b_g(z[:t], None) for t in looks)
            adm["plug_in_monitored"][rep, c] = any(gates.plug_in(z[:t]) for t in looks)
            adm["b_x1"][rep, c] = True
    bad = [c for c, d in enumerate(deltas) if d <= 0]
    good = [c for c, d in enumerate(deltas) if d > 0]
    out = {}
    for r, m in adm.items():
        fdp = [m[i, bad].sum() / max(1, m[i].sum()) for i in range(reps)]
        out[r] = {
            "fwer": float(m[:, bad].any(axis=1).mean()),
            "fdr": float(np.mean(fdp)),
            "coverage": float(m[:, good].mean()),
        }
    return out


def drift_stream(rng, tasks, base, n, d_before, d_after, change_at):
    """Trials with effect d_before before change_at and d_after from change_at on."""
    z = []
    for t in range(n):
        d = d_before if t < change_at else d_after
        zz, _ = pr.make_cell(rng, tasks, 1, d, base, None)
        z.append(zz[0])
    return z


def t2(rng, tasks, base, reps):
    n, change = 400, 100
    out = {}
    for scen, d_after in (("drift", -0.20), ("no_drift", 0.20)):
        res = {
            "library_drift": [],
            "gk_fingerprint_visible": [],
            "gk_fingerprint_hidden": [],
            "gk_outcome_monitor": [],
        }
        for _ in range(reps):
            z = drift_stream(rng, tasks, base, n, 0.20, d_after, change)
            gain = -np.array(z)  # resolved gain: + = the skill helps
            # Library Drift: retired at the first t >= N_min with mean gain <= -tau
            ld = next((t for t in range(LD_NMIN, n + 1) if gain[:t].mean() <= -LD_TAU), None)
            res["library_drift"].append(ld)
            res["gk_fingerprint_visible"].append(change if scen == "drift" else None)
            res["gk_fingerprint_hidden"].append(None)
            ep = BettingEProcess(theta=0.0, alpha=ALPHA)  # harm monitor: certifies E[Z] > 0
            mon = None
            for t, v in enumerate(z, 1):
                ep.update(-v)
                if ep.crossed:
                    mon = t
                    break
            res["gk_outcome_monitor"].append(mon)
        summ = {}
        for r, v in res.items():
            hits = [t for t in v if t is not None]
            summ[r] = {
                "retired_share": len(hits) / reps,
                "median_retire_trial": float(np.median(hits)) if hits else None,
                "median_delay_after_change": float(
                    np.median([t - change for t in hits if t >= change])
                )
                if scen == "drift" and any(t >= change for t in hits)
                else None,
                "retired_before_change_share": sum(1 for t in hits if t < change) / reps,
            }
        out[scen] = summ
    return out


def t3(rng, tasks, base, reps):
    n = 200
    a_each = ALPHA / 3
    naive = gk = 0
    for _ in range(reps):
        za, _ = pr.make_cell(rng, tasks, n, 0.20, base, None)
        zb, _ = pr.make_cell(rng, tasks, n, 0.20, base, None)
        zc, _ = pr.make_cell(rng, tasks, n, -0.05, base, None)  # composite: negative interaction
        pa = gates.gatekeeper_p(za, 0.0, a_each, n) <= a_each
        pb = gates.gatekeeper_p(zb, 0.0, a_each, n) <= a_each
        naive += pa and pb
        gk += gates.gatekeeper_p(zc, 0.0, a_each, n) <= a_each
    return {"naive_both_components_admitted": naive / reps, "gatekeeper_composite_cell": gk / reps}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xrepo", type=Path, required=True)
    ap.add_argument("--reps", type=int, required=True)
    a = ap.parse_args()
    score = gates.load_xreposkill_score(a.xrepo)
    tasks = pr.no_skill_runs()
    base = float(np.mean([np.mean(t) for t in tasks]))
    rng = np.random.default_rng(SEED)
    out = {"base_solve_rate": base, "reps": a.reps}
    out["T3"] = t3(rng, tasks, base, a.reps)
    print("T3", out["T3"], flush=True)
    out["T2"] = t2(rng, tasks, base, a.reps)
    print("T2", json.dumps(out["T2"]), flush=True)
    out["T1"] = t1(rng, tasks, base, score, a.reps)
    print("T1", json.dumps(out["T1"]), flush=True)
    Path("results/lifecycle_plasmode.json").write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
