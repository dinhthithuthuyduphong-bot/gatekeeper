"""Numerical check of every decision method used in E1, E2 and RQ1 (docs/method_check.md).

Two questions per method:
  (1) VALID?  Under H0 the rejection (or admission) rate must be <= its nominal level.
  (2) USEFUL? Power to detect effects of published size, for the actual designs.

Plasmode simulation (Franklin et al. 2014): per-task baseline solve probabilities are resampled
from the MEASURED no-skill arms of the G1 confirmation runs (g1-c-s11/21/31: 32 tasks x 3 seeds).
E1 outcome data are NOT used (preregistration_e1.md: no look before the analysis).
Effect sizes delta (absolute change in the solve rate) are the published SWE-Skills-Bench
reference points used in the design (results/sskb_analysis.json, docs/g1_verdict.md section 2),
plus larger values to show the whole curve.
Monte Carlo size: SE of a simulated rate = sqrt(p(1-p)/R) (Morris, White & Crowther 2019):
R_VALID = 12,000 keeps SE < alpha/10 at the smallest level used (0.025/3);
R_POWER = 2,500 keeps SE <= 0.01 for power. Writes results/method_check.json.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from itertools import product
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import analyze_g1_final as gf  # noqa: E402
import rq1_mini as rq  # noqa: E402

ALPHA = gf.ALPHA_FAMILY  # 0.025 one-sided per direction
R_VALID = 12_000
R_POWER = 2_500
SEEDS = 3
DELTAS = [0.02, 0.05, 0.109, 0.15, 0.20, 0.30]


def measured_q() -> np.ndarray:
    """Per-task solve probability of the no-skill arm: mean over the 3 G1 confirmation seeds."""
    acc: dict[str, list[float]] = {}
    for n in ("g1-c-s11", "g1-c-s21", "g1-c-s31"):
        d = json.loads(Path(f"results/pilot/{n}.json").read_text())
        for p in d["skills"]["validation-error"]["pairs"]:
            acc.setdefault(p["instance_id"], []).append(float(gf.resolved(p["loss_without"])))
    return np.array([np.mean(v) for v in acc.values() if len(v) == 3])


def clusters_of(ids: list[str]) -> list[int]:
    c = Counter(gf.repo_of(i) for i in ids)
    return sorted(c.values(), reverse=True)


def simulate(rng, q, n, sizes, delta, seeds=SEEDS):
    """Per-task mean Z over seeds (Z = 1[unresolved|skill] - 1[unresolved|none]; < 0 helps) and
    the task ids carrying the repository clusters. delta > 0: the skill raises the solve rate."""
    qi = rng.choice(q, size=n, replace=True)
    qs = np.clip(qi + delta, 0.0, 1.0)
    r0 = rng.random((n, seeds)) < qi[:, None]  # resolved without skill (per-task row)
    r1 = rng.random((n, seeds)) < qs[:, None]  # resolved with skill
    z = (~r1).astype(float) - (~r0).astype(float)
    assert z.shape == (n, seeds), z.shape  # broadcasting must never widen the sample (review R-6)
    ids, k = [], 0
    for g, s in enumerate(sizes):
        for _ in range(s):
            ids.append(f"o{g}__r{g}-{k}")
            k += 1
    return dict(zip(ids[:n], z.mean(axis=1), strict=True)), z, (qs - qi).mean()


def decide(zt: dict[str, float], level: float) -> dict[str, bool]:
    x = list(zt.values())
    prim = gf.sign_flip_p(x) <= level
    s1 = gf.paired_t_p(x) <= level
    s2 = gf.cluster_sign_flip_p(zt)[0] <= level
    return {"primary": prim, "robust": prim and s1 and s2}


def design(name, rng, q, n, sizes, level, reps_valid, reps_power):
    out = {"n": n, "clusters": sizes, "level": level}
    # (1) validity: delta = 0, both arms identical (H0: exchangeable)
    rej = Counter()
    for _ in range(reps_valid):
        zt, _, _ = simulate(rng, q, n, sizes, 0.0)
        for k, v in decide(zt, level).items():
            rej[k] += v
        rej["s2_alone"] += gf.cluster_sign_flip_p(zt)[0] <= level
    out["type1"] = {k: v / reps_valid for k, v in rej.items()}
    out["type1_mcse"] = math.sqrt(level * (1 - level) / reps_valid)
    # (2) power (helpful direction)
    out["power"] = {}
    for d in DELTAS:
        acc, eff = Counter(), []
        for _ in range(reps_power):
            zt, _, e = simulate(rng, q, n, sizes, d)
            eff.append(e)
            for k, v in decide(zt, level).items():
                acc[k] += v
        out["power"][str(d)] = {
            "realised_mean_effect": float(np.mean(eff)),
            **{k: v / reps_power for k, v in acc.items()},
        }
    print(name, json.dumps(out["type1"]), flush=True)
    return out


def aa_check(rng, q, n, reps):
    """A/A: two no-skill seeds, exact two-sided sign-flip at 2 * ALPHA; rate must be <= 0.05."""
    hit = 0
    for _ in range(reps):
        qi = rng.choice(q, size=n, replace=True)
        a = (rng.random(n) >= qi).astype(float)
        b = (rng.random(n) >= qi).astype(float)
        hit += gf.sign_flip_p(list(a - b), two_sided=True) < 2 * ALPHA
    return {"n": n, "level": 2 * ALPHA, "rate": hit / reps}


def rq1_check(rng, q, k_cells=7, budget=rq.BUDGET, reps=R_POWER):
    """RQ1 screening (one seed, 40 trials): admission rate of Gatekeeper and of the plug-in rule
    as a function of the true effect; delta < 0 = harmful skill. Validity: harmful or null cells
    must be admitted by Gatekeeper at rate <= alpha_cell."""
    a_cell = rq.ALPHA / k_cells
    out = {"alpha_cell": a_cell, "budget": budget, "by_delta": {}}
    for d in [-0.20, -0.10, -0.05, 0.0, 0.05, 0.109, 0.15, 0.20, 0.30, 0.40]:
        reps_d = R_VALID if d <= 0 else reps
        gk = pl = 0
        for _ in range(reps_d):
            _, z, _ = simulate(rng, q, budget, [budget], d, seeds=1)
            dec = rq.decide(list(z[:, 0]), a_cell)
            gk += dec["Gatekeeper"]
            pl += dec["Plug-in (mean < 0)"]
        out["by_delta"][str(d)] = {
            "gatekeeper": gk / reps_d,
            "plug_in": pl / reps_d,
            "reps": reps_d,
        }
        print("rq1", d, out["by_delta"][str(d)], flush=True)
    return out


def exact_vs_bruteforce(rng) -> bool:
    """The convolution p-value equals full enumeration of the 2^n sign flips (n = 12)."""
    for _ in range(50):
        x = list(rng.integers(-3, 4, size=12) / 3)
        obs = sum(x)
        brute = (
            sum(
                sum(s * abs(v) for s, v in zip(signs, x, strict=True)) <= obs + 1e-12
                for signs in product((-1, 1), repeat=12)
            )
            / 2**12
        )
        if abs(brute - gf.sign_flip_p(x)) > 1e-12:
            return False
    return True


def main() -> int:
    rng = np.random.default_rng(20271103)
    q = measured_q()
    out: dict = {
        "inputs": {
            "baseline_solve_rate_per_task": "G1 confirmation no-skill arms, 32 tasks x 3 seeds",
            "n_tasks_q": int(q.size),
            "mean_q": float(q.mean()),
            "R_valid": R_VALID,
            "R_power": R_POWER,
        }
    }
    # plasmode sanity: discordance P(Z = +1) at delta 0 vs the measured 0.08 (design_table_plasmode)
    _, z, _ = simulate(rng, q, 4000, [4000], 0.0, seeds=1)
    out["inputs"]["simulated_p_plus_at_delta0"] = float((z == 1).mean())
    out["exact_test_matches_enumeration"] = exact_vs_bruteforce(rng)
    sets = json.loads(Path("configs/pools/e1_task_sets.json").read_text())
    e1_sizes = clusters_of(sets["null-guard"])
    e2_ids = json.loads(Path("configs/pools/e2.json").read_text())["instances"]
    e2_sizes = clusters_of(e2_ids)
    out["E1"] = design("E1", rng, q, 40, e1_sizes, ALPHA / 3, R_VALID, R_POWER)
    out["E2"] = design("E2", rng, q, 119, e2_sizes, ALPHA, R_VALID, R_POWER)
    out["AA_E1"] = aa_check(rng, q, 40, R_VALID)
    out["AA_E2"] = aa_check(rng, q, 119, R_VALID)
    out["RQ1"] = rq1_check(rng, q)
    Path("results/method_check.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k in ("inputs", "AA_E1", "AA_E2")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
