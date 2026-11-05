"""Section 18 (docs/preregistration_main.md): is it the skill or the dice? 0 USD.
H18-1 consistency across seeds, H18-2 task-level heterogeneity tau^2, H18-3/4/5 A/A placebo for the
candidate step of skill-failure attribution (Dong et al., skill_induced_failures_2026), and the
plasmode power check of execution note 18-2. Writes results/replicate_attribution.json.

  python scripts/run_metrics.py --stage e1 && python scripts/run_metrics.py --stage e2
  python scripts/replicate_attribution.py --null-reps 10000 --boot 10000 --power-reps 1000
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import analyze_g1_final as gf  # noqa: E402

SEEDS = ("s41", "s51", "s61")
# placebo (target none seed, reference none seed): three ordered pairs, as many as on the skill side
PLACEBO = (("s51", "s41"), ("s61", "s51"), ("s41", "s61"))
T_EFF = 2.0  # Dong et al.: "at least one must more than double (T = 2.0)"
SEED = 20271111
POWER_TAUS = (0.0, 0.10, 0.15, 0.20)
STAGE_FILES = {
    "e1": "results/pilot/g1-e1-s*-p[0-9][0-9].json",
    "e2": "results/e2/g2-e2-s*-k*-p*.json",
}


# ---------- pure functions (tests/test_replicate_attribution.py) ----------


def consistency(M: np.ndarray) -> float:
    """Share of rows (tasks) whose entries (seeds) are all nonzero and of one sign."""
    nz = (M != 0).all(axis=1)
    same = (np.sign(M) == np.sign(M[:, :1])).all(axis=1)
    return float(np.mean(nz & same))


def signflip_null(M: np.ndarray, reps: int, rng: np.random.Generator) -> np.ndarray:
    """Consistency of M after flipping the sign of each entry with probability 1/2."""
    out = np.empty(reps)
    for r in range(reps):
        out[r] = consistency(M * rng.choice([-1.0, 1.0], size=M.shape))
    return out


def tau2_mom(M: np.ndarray) -> float:
    """Method of moments: Var(task means) - mean(within-task variance) / k."""
    k = M.shape[1]
    return float(M.mean(axis=1).var(ddof=1) - M.var(axis=1, ddof=1).mean() / k)


def boot_ci(stat, M: np.ndarray, groups: list[str] | None, reps: int, rng) -> tuple[float, float]:
    """95% percentile CI, resampling tasks (or groups of tasks) with replacement."""
    if groups is None:
        idx = [np.array([i]) for i in range(len(M))]
    else:
        g = defaultdict(list)
        for i, k in enumerate(groups):
            g[k].append(i)
        idx = [np.array(v) for v in g.values()]
    vals = []
    for _ in range(reps):
        pick = rng.integers(0, len(idx), len(idx))
        vals.append(stat(M[np.concatenate([idx[j] for j in pick])]))
    lo, hi = np.nanpercentile(vals, [2.5, 97.5])  # a resample with no candidates gives nan
    return float(lo), float(hi)


def functional(target_resolved: bool, ref_resolved: bool) -> bool:
    """Dong et al. candidate: the target run fails and the reference run solves the same task."""
    return (not target_resolved) and ref_resolved


def efficiency(t: dict, r: dict, both_pass: bool, token_only: bool) -> bool | None:
    """Dong et al.: PASS/PASS, min(r_tok, r_time) > 1, max(...) > T. None if not measured."""
    if not both_pass:
        return False
    if not t or not r or not r.get("tokens"):
        return None
    rt = t["tokens"] / r["tokens"]
    if token_only:
        return rt > T_EFF
    if t.get("seconds") is None or not r.get("seconds"):
        return None
    rs = t["seconds"] / r["seconds"]
    return min(rt, rs) > 1.0 and max(rt, rs) > T_EFF


def recurrence(counts: np.ndarray) -> float | None:
    """H18-5: among candidates at one seed, the share whose task also has a candidate at both other
    seeds = 3 * #(tasks with 3 candidates) / #candidates."""
    total = counts.sum()
    return float(3 * (counts == 3).sum() / total) if total else None


# ---------- data ----------


def seed_of(part: str) -> str:
    m = re.search(r"-(s\d\d)-", part)
    if not m:
        raise ValueError(part)
    return m.group(1)


def load(stage: str) -> dict:
    """rec[skill][task][seed] = (resolved_with, resolved_without, metrics_with, metrics_without)."""
    met = json.loads(Path(f"results/run_metrics_{stage}.json").read_text())["runs"]
    rec: dict = defaultdict(lambda: defaultdict(dict))
    for f in sorted(glob.glob(STAGE_FILES[stage])):
        part = Path(f).stem
        s = seed_of(part)
        d = json.loads(Path(f).read_text())
        m = met.get(part, {})
        for skill, v in d.get("skills", {}).items():
            for p in v.get("pairs", []):
                i = p["instance_id"]
                if s in rec[skill][i]:
                    raise SystemExit(f"duplicate pair {skill} {i} {s} ({part})")
                arm = next((a for a in (skill, skill.replace("-", "_")) if f"{a}/{i}" in m), skill)
                rec[skill][i][s] = (
                    gf.resolved(p["loss_with"]),
                    gf.resolved(p["loss_without"]),
                    m.get(f"{arm}/{i}"),
                    m.get(f"none/{i}"),
                )
    return rec


def zmatrix(tasks: dict) -> tuple[np.ndarray, list[str]]:
    ids = [i for i, v in sorted(tasks.items()) if all(s in v for s in SEEDS)]
    M = np.array(
        [[float(not tasks[i][s][0]) - float(not tasks[i][s][1]) for s in SEEDS] for i in ids]
    )
    return M, ids


def attribution(tasks: dict, ids: list[str]) -> dict:
    """Per-task candidate indicators for the skill side and the placebo side (3 pairs each)."""
    rows = []
    for i in ids:
        v = tasks[i]
        sk_f = [functional(v[s][0], v[s][1]) for s in SEEDS]
        pl_f = [functional(v[a][1], v[b][1]) for a, b in PLACEBO]
        sk_e = [efficiency(v[s][2], v[s][3], v[s][0] and v[s][1], False) for s in SEEDS]
        pl_e = [efficiency(v[a][3], v[b][3], v[a][1] and v[b][1], False) for a, b in PLACEBO]
        sk_t = [efficiency(v[s][2], v[s][3], v[s][0] and v[s][1], True) for s in SEEDS]
        pl_t = [efficiency(v[a][3], v[b][3], v[a][1] and v[b][1], True) for a, b in PLACEBO]
        rows.append((sk_f, pl_f, sk_e, pl_e, sk_t, pl_t))
    return rows


def summarise(rows, boot: int, rng) -> dict:
    def cnt(col):
        return np.array([[1.0 if x else 0.0 for x in r[col]] for r in rows])

    def unmeasured(col):
        return int(sum(x is None for r in rows for x in r[col]))

    out = {"tasks": len(rows)}
    for name, (a, b) in {
        "functional": (0, 1),
        "efficiency": (2, 3),
        "efficiency_token_only": (4, 5),
    }.items():
        S, P = cnt(a), cnt(b)
        both = np.stack([S, P], axis=1)  # tasks x 2 x 3

        def ratio(X):
            s = X[:, 0].sum()
            return float(X[:, 1].sum() / s) if s else float("nan")

        lo, hi = boot_ci(ratio, both, None, boot, rng) if S.sum() else (None, None)
        rec_s = S.sum(1)
        rec_p = P.sum(1)
        out[name] = {
            "skill_candidates": int(S.sum()),
            "placebo_candidates": int(P.sum()),
            "R": ratio(both),
            "R_ci95": [lo, hi],
            "unmeasured_skill": unmeasured(a),
            "unmeasured_placebo": unmeasured(b),
            "recurrence_skill": recurrence(rec_s),
            "recurrence_placebo": recurrence(rec_p),
        }
    return out


def heterogeneity(M, ids, null_reps, boot, rng) -> dict:
    c = consistency(M)
    null = signflip_null(M, null_reps, rng)
    repos = [i.rsplit("-", 1)[0] for i in ids]
    return {
        "tasks": len(ids),
        "mean_gain": float(-M.mean()),
        "C": c,
        "C_null_mean": float(null.mean()),
        "p_one_sided": float((null >= c).mean()),
        "tau2": tau2_mom(M),
        "tau2_ci95_task": boot_ci(tau2_mom, M, None, boot, rng),
        "tau2_ci95_repo": boot_ci(tau2_mom, M, repos, boot, rng),
    }


def power_check(tasks: dict, ids: list[str], reps: int, null_reps: int, boot: int, rng) -> dict:
    """Execution note 18-2: real no-skill noise of E2, planted effects delta_i ~ N(0, tau^2)."""
    none = np.array([[float(tasks[i][s][1]) for s in SEEDS] for i in ids])  # 1 = resolved
    m = none.mean(1)
    out = {}
    for tau in POWER_TAUS:
        rej, cover = 0, 0
        for _ in range(reps):
            p_with = np.clip(m + rng.normal(0, tau, len(m)), 0, 1)
            w = (rng.random(none.shape) < p_with[:, None]).astype(float)
            M = (1 - w) - (1 - none)
            c = consistency(M)
            rej += (signflip_null(M, null_reps, rng) >= c).mean() <= 0.05
            true_tau2 = float(np.var(p_with - m, ddof=1))
            lo, hi = boot_ci(tau2_mom, M, None, boot, rng)
            cover += lo <= true_tau2 <= hi
        out[str(tau)] = {"H18_1_rejection_rate": rej / reps, "tau2_ci_coverage": cover / reps}
        print("power", tau, out[str(tau)], flush=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--null-reps", type=int, required=True)
    ap.add_argument("--boot", type=int, required=True)
    ap.add_argument("--power-reps", type=int, required=True)
    ap.add_argument("--power-null-reps", type=int, required=True)
    ap.add_argument("--power-boot", type=int, required=True)
    a = ap.parse_args()
    rng = np.random.default_rng(SEED)
    out: dict = {"T": T_EFF, "seed": SEED, "args": vars(a), "stages": {}}
    for stage in ("e1", "e2"):
        rec = load(stage)
        st = {}
        for skill, tasks in sorted(rec.items()):
            M, ids = zmatrix(tasks)
            st[skill] = {
                "heterogeneity": heterogeneity(M, ids, a.null_reps, a.boot, rng),
                "attribution": summarise(attribution(tasks, ids), a.boot, rng),
            }
            print(stage, skill, json.dumps(st[skill])[:300], flush=True)
        out["stages"][stage] = st
    e2 = load("e2")["xreposkill"]
    _, ids = zmatrix(e2)
    out["power_check_e2"] = power_check(e2, ids, a.power_reps, a.power_null_reps, a.power_boot, rng)
    Path("results/replicate_attribution.json").write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
