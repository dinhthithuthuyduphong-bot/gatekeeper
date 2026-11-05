"""Section 19 A, B, D, F (docs/preregistration_main.md): a placebo test for skill-evaluation rules.
0 USD. Writes results/placebo_suite.json.

A: published (or published-based) decision rules on real A/A no-skill pairs of E1 + E2.
B: calibration of SWE-Skills-Bench's per-cell exact sign-flip test on its public data.
D: placebo-calibrated attribution rules (recurrence, count test, Gatekeeper) in the D-M8 model.
F: seeds needed for the recurrence rule.

  python scripts/placebo_suite.py --xrepo <XRepoSkill clone at 26fd703> --reps 10000
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import binomtest

sys.path.insert(0, str(Path(__file__).parent))
import gates  # noqa: E402
import heterogeneity_power_v2 as hp  # noqa: E402
import plasmode_real as pr  # noqa: E402
import replicate_attribution as ra  # noqa: E402
import two_stage_retirement as tsr  # noqa: E402

from gatekeeper.eprocess import BettingEProcess, run_admission  # noqa: E402

SEED = 20271113
ALPHA = 0.025  # Gatekeeper / e-SR level, as sections 14-15
N_STREAM, LOOK, N_RETIRE = 200, 10, 400
GEPA_M, GEPA_K = 3, (100, 200)  # minibatch 3; 600 rollouts / 6 or / 3 per proposal
SSKB_N, SSKB_ALPHA, SSKB_CELLS = 10, 0.05, 98 * 4
LD_NMIN, LD_TAU = 100, 0.10  # Library Drift
ESR_LAMBDA = 0.5
QS = (0.0, 0.1, 0.2, 0.3)
F_RULES = {1: 1, 2: 2, 3: 2, 5: 3, 10: 6}  # k seeds -> strict majority r
SSKB_CSV = Path("data/external/swe-skills-bench/ALL_combined_cells.csv")


# ---------- pure helpers (tests/test_placebo_suite.py) ----------


def signflip_p_exact(d: list[float]) -> float:
    """Exact two-sided sign-flip p-value of sum(d) (zeros carry no sign)."""
    nz = [x for x in d if x != 0]
    if not nz:
        return 1.0
    obs = abs(sum(nz))
    tot = hits = 0
    for signs in itertools.product((-1, 1), repeat=len(nz)):
        tot += 1
        hits += abs(sum(s * x for s, x in zip(signs, nz, strict=True))) >= obs - 1e-12
    return hits / tot


def signflip_p_mc(d: np.ndarray, reps: int, rng) -> float:
    nz = d[d != 0]
    if nz.size == 0:
        return 1.0
    obs = abs(nz.sum())
    s = rng.choice([-1.0, 1.0], size=(reps, nz.size))
    return float(((np.abs(s @ nz) >= obs - 1e-12).sum() + 1) / (reps + 1))


def library_drift_retires(z: list[float]) -> bool:
    gain = -np.asarray(z)
    c = np.cumsum(gain) / np.arange(1, len(gain) + 1)
    return bool((c[LD_NMIN - 1 :] <= -LD_TAU).any())


def esr_alarms(z: list[float]) -> bool:
    m = 0.0
    for v in z:
        m = (1 + ESR_LAMBDA * v) * (m + 1)
        if m >= 1 / ALPHA:
            return True
    return False


def binom_count_p(s: int, p_: int) -> float:
    """D2: one-sided P(S >= s) under S ~ Bin(S + P, 1/2)."""
    return float(binomtest(s, s + p_, 0.5, alternative="greater").pvalue) if s + p_ else 1.0


def gk_harm(x: list[float], alpha: float) -> bool:
    """D3: e-process that certifies E[X] > 0 for X = skill candidate - placebo candidate."""
    ep = BettingEProcess(theta=0.0, alpha=alpha)
    for v in x:
        ep.update(-v)
        if ep.crossed:
            return True
    return False


# ---------- A ----------


def aa_tasks() -> list[list[int]]:
    """Per task, the resolved outcomes (1/0) of its three no-skill runs (E1 + E2)."""
    out = []
    for stage in ("e1", "e2"):
        rec = ra.load(stage)
        seen = {}
        for tasks in rec.values():
            for i, v in tasks.items():
                if all(s in v for s in ra.SEEDS):
                    seen[i] = [int(v[s][1]) for s in ra.SEEDS]
        out += list(seen.values())
    return out


def part_a(rng, tasks, score, reps: int) -> dict:
    base = float(np.mean([np.mean(t) for t in tasks]))
    looks = list(range(LOOK, N_STREAM + 1, LOOK))
    c = defaultdict(int)
    gepa = 0
    for _ in range(reps):
        z, prs = pr.make_cell(rng, tasks, N_RETIRE, 0.0, base, None)
        zs, ps = z[:N_STREAM], prs[:N_STREAM]
        c["plug_in_once"] += gates.plug_in(zs)
        c["plug_in_monitored"] += any(gates.plug_in(zs[:t]) for t in looks)
        c["b_x2_once"] += gates.b_x2(ps, score)
        c["b_x2_monitored"] += any(gates.b_x2(ps[:t], score) for t in looks)
        c["sskb_cell"] += signflip_p_exact(zs[:SSKB_N]) < SSKB_ALPHA
        c["library_drift"] += library_drift_retires(z)
        c["e_sr"] += esr_alarms(z)
        c["gatekeeper_admit"] += run_admission(zs, 0.0, ALPHA, budget=N_STREAM).admitted
        c["gatekeeper_two_stage_retire"] += tsr.two_stage(z)[0] is not None
        gz, _ = pr.make_cell(rng, tasks, GEPA_M, 0.0, base, None)
        gepa += gates.b_g(gz, None)
    out = {k: v / reps for k, v in c.items()}
    p = gepa / reps
    out["gepa_accept_per_proposal"] = p
    for k in GEPA_K:
        out[f"gepa_P_accept_any_K{k}"] = 1 - (1 - p) ** k
        out[f"gepa_expected_accepted_K{k}"] = k * p
    out["sskb_expected_false_cells_of_392"] = out["sskb_cell"] * SSKB_CELLS
    out["mc_halfwidth_95"] = {
        k: 1.96 * math.sqrt(v * (1 - v) / reps) for k, v in out.items() if 0 < v < 1
    }
    return out


# ---------- B ----------


def part_b(rng) -> dict:
    cells = defaultdict(list)
    with SSKB_CSV.open() as f:
        for r in csv.DictReader(f):
            cells[(r["harness_model"], r["skill"])].append(float(r["delta_pp"]))
    ps = {k: signflip_p_exact(v) for k, v in cells.items()}
    sig = [k for k, p in ps.items() if p < SSKB_ALPHA]
    n = len(ps)
    hist = np.histogram(list(ps.values()), bins=10, range=(0, 1))[0].tolist()
    by_skill = defaultdict(list)
    for (_cfg, sk), v in cells.items():
        by_skill[sk] += v
    pooled = {sk: signflip_p_mc(np.array(v), 200_000, rng) for sk, v in by_skill.items()}
    gp = sum(1 for sk, p in pooled.items() if p < SSKB_ALPHA and sum(by_skill[sk]) > 0)
    hp_ = sum(1 for sk, p in pooled.items() if p < SSKB_ALPHA and sum(by_skill[sk]) < 0)
    return {
        "cells": n,
        "cells_p_below_0.05": len(sig),
        "expected_under_null": SSKB_ALPHA * n,
        "binomial_two_sided_p": float(binomtest(len(sig), n, SSKB_ALPHA).pvalue),
        "p_histogram_10_bins": hist,
        "pooled_per_skill_golden_harmful_ineffective": [gp, hp_, len(pooled) - gp - hp_],
        "paper_reports": [4, 2, 92],
    }


# ---------- D, F ----------


def simulate_cell(rng, a, b, n_tasks, k, q):
    """Resolved outcomes of k no-skill and k skill runs per task; the skill turns a run that
    would solve the task into a failure with probability q (skill-induced failure)."""
    p = rng.beta(a, b, n_tasks)
    none = rng.random((n_tasks, k)) < p[:, None]
    skill = (rng.random((n_tasks, k)) < p[:, None]) & ~(rng.random((n_tasks, k)) < q)
    return none, skill


def candidates(none, skill):
    k = none.shape[1]
    sk = (~skill) & none  # skill run fails, same-seed reference solves
    order = [(i, (i - 1) % k) for i in range(k)]  # (51,41), (61,51), (41,61) for k = 3
    pl = np.stack([(~none[:, a]) & none[:, b] for a, b in order], axis=1)
    return sk, pl


def part_d(rng, a, b, n_tasks, reps) -> dict:
    out = {}
    for q in QS:
        d1 = d1_any = d2 = d3 = 0
        for _ in range(reps):
            none, skill = simulate_cell(rng, a, b, n_tasks, 3, q)
            sk, pl = candidates(none, skill)
            att = sk.sum(1) >= 2
            d1 += att.sum()
            d1_any += att.any()
            d2 += binom_count_p(int(sk.sum()), int(pl.sum())) < 0.05
            x = (sk.astype(float) - pl.astype(float)).ravel()
            d3 += gk_harm(list(rng.permutation(x)), ALPHA)
        out[str(q)] = {
            "D1_mean_attributed_tasks": d1 / reps,
            "D1_P_any_attribution": d1_any / reps,
            "D2_rejection_rate": d2 / reps,
            "D3_rejection_rate": d3 / reps,
        }
        print("D", q, out[str(q)], flush=True)
    return out


def part_f(rng, a, b, n_tasks, reps) -> dict:
    out = {}
    for k, r in F_RULES.items():
        row = {}
        for q in (0.0, 0.2):
            tot = 0.0
            for _ in range(reps):
                none, skill = simulate_cell(rng, a, b, n_tasks, k, q)
                sk = (~skill) & none
                tot += (sk.sum(1) >= r).mean()
            row[f"attributed_share_q{q}"] = tot / reps
        out[f"k{k}_r{r}"] = row
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xrepo", type=Path, required=True)
    ap.add_argument("--reps", type=int, required=True)
    ap.add_argument("--d-reps", type=int, required=True)
    a_ = ap.parse_args()
    rng = np.random.default_rng(SEED)
    score = gates.load_xreposkill_score(a_.xrepo)
    tasks = aa_tasks()
    out = {"seed": SEED, "args": {k: str(v) for k, v in vars(a_).items()}, "aa_tasks": len(tasks)}
    out["A"] = part_a(rng, tasks, score, a_.reps)
    print("A", json.dumps(out["A"])[:600], flush=True)
    out["B"] = part_b(rng)
    print("B", out["B"], flush=True)
    e2 = ra.load("e2")["xreposkill"]
    _, ids = ra.zmatrix(e2)
    k = np.array([sum(e2[i][s][1] for s in ra.SEEDS) for i in ids], float)
    a, b = hp.beta_mom(k, len(ra.SEEDS))
    out["beta"] = [a, b]
    out["D"] = part_d(rng, a, b, len(ids), a_.d_reps)
    out["F"] = part_f(rng, a, b, len(ids), a_.d_reps)
    real = json.loads(Path("results/replicate_attribution.json").read_text())["stages"]
    out["D2_on_real_data"] = {
        f"{st}/{sk}": binom_count_p(
            v["attribution"]["functional"]["skill_candidates"],
            v["attribution"]["functional"]["placebo_candidates"],
        )
        for st, d in real.items()
        for sk, v in d.items()
    }
    Path("results/placebo_suite.json").write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
