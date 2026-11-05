"""Section 21 (docs/preregistration_main.md). 0 USD. Writes results/section21.json.

P-A (deviation D-M10): misattribution bound with a bootstrap that resamples *tasks* (all
(skill, task) units of a drawn task together), since 45/112 E1 tasks belong to >= 2 skills.
P-B: exact permutation test of T = S - P. Under H0 the 2k runs of a task (k with the skill,
k without) are exchangeable; labels are permuted within task, the identity is included, and
p = (1 + #{T* >= T}) / (1 + B) is valid (hemerik_goeman_2018, citing Lehmann and Romano 2005,
p. 636).
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import analyze_g1_final as gf  # noqa: E402
import heterogeneity_power_v2 as hp  # noqa: E402
import placebo_suite as ps  # noqa: E402
import replicate_attribution as ra  # noqa: E402

SEED = 20271115


# ---------- pure (tests/test_placebo_suite.py) ----------


def t_stat(skill: np.ndarray, none: np.ndarray) -> float:
    """S - P for boolean arrays tasks x k (1 = resolved), pairing as section 18."""
    sk, pl = ps.candidates(none, skill)
    return float(sk.sum() - pl.sum())


def perm_test(skill: np.ndarray, none: np.ndarray, B: int, rng) -> float:
    """One-sided (harm) exact permutation p-value; labels permuted within task."""
    k = skill.shape[1]
    allr = np.concatenate([skill, none], axis=1)
    t0 = t_stat(skill, none)
    hits = 0
    for _ in range(B):
        idx = np.argsort(rng.random(allr.shape), axis=1)
        perm = np.take_along_axis(allr, idx, axis=1)
        hits += t_stat(perm[:, :k], perm[:, k:]) >= t0 - 1e-12
    return (1 + hits) / (1 + B)


def t_help(skill1, ref1, none3) -> float:
    """S3 statistic: help candidates (skill solves, ref fails) minus placebo help candidates / 3."""
    s = (skill1 & ~ref1).sum()
    p = sum((none3[:, a] & ~none3[:, b]).sum() for a, b in ((1, 0), (2, 1), (0, 2)))
    return float(s - p / 3)


def perm_test_help(skill1, ref1, none3, B: int, rng) -> float:
    allr = np.stack([skill1, ref1, *none3.T], axis=1)
    t0 = t_help(skill1, ref1, none3)
    hits = 0
    for _ in range(B):
        idx = np.argsort(rng.random(allr.shape), axis=1)
        perm = np.take_along_axis(allr, idx, axis=1)
        hits += t_help(perm[:, 0], perm[:, 1], perm[:, 2:]) >= t0 - 1e-12
    return (1 + hits) / (1 + B)


# ---------- data ----------


def arrays(tasks: dict) -> tuple[np.ndarray, np.ndarray]:
    _, ids = ra.zmatrix(tasks)
    skill = np.array([[tasks[i][s][0] for s in ra.SEEDS] for i in ids], bool)
    none = np.array([[tasks[i][s][1] for s in ra.SEEDS] for i in ids], bool)
    return skill, none


def p_a(rng, boot: int) -> dict:
    rec = ra.load("e1")
    by_task = defaultdict(list)  # task -> [(S, P) per skill]
    for _skill, tasks in sorted(rec.items()):
        _, ids = ra.zmatrix(tasks)
        for i, row in zip(ids, ra.attribution(tasks, ids), strict=True):
            by_task[i].append((sum(bool(x) for x in row[0]), sum(bool(x) for x in row[1])))
    groups = [np.array(v, float) for v in by_task.values()]

    def share(gs):
        X = np.concatenate(gs)
        s = X[:, 0].sum()
        return (s - X[:, 1].sum()) / s if s else np.nan

    vals = [
        share([groups[j] for j in rng.integers(0, len(groups), len(groups))]) for _ in range(boot)
    ]
    upper = float(np.nanpercentile(vals, 97.5))
    old = json.loads(Path("results/section20.json").read_text())["S2"]
    out = {
        "tasks": len(groups),
        "share_hat": share(groups),
        "upper95_task_cluster": upper,
        "upper95_old_unit_bootstrap": old["upper95"],
        "auditors": {},
    }
    for name, v in old["auditors"].items():
        a = v["attributed_real"]
        out["auditors"][name] = {
            "attributed_real": a,
            "lower_bound_new": max(0.0, a - upper),
            "lower_bound_old": v["misattribution_lower_bound"],
        }
    return out


def p_b(rng, B: int, power_reps: int, power_B: int) -> dict:
    out = {"real": {}}
    for stage in ("e1", "e2"):
        for skill, tasks in sorted(ra.load(stage).items()):
            sk, no = arrays(tasks)
            out["real"][f"{stage}/{skill}"] = {"T": t_stat(sk, no), "p": perm_test(sk, no, B, rng)}
    # S3, help direction
    t4 = {}
    for f in sorted(glob.glob("results/pilot/t4-s41-p[0-9][0-9].json")):
        for p in json.loads(Path(f).read_text())["skills"]["control-oracle-patch"]["pairs"]:
            t4[p["instance_id"]] = (gf.resolved(p["loss_with"]), gf.resolved(p["loss_without"]))
    e2 = ra.load("e2")["xreposkill"]
    ids = [i for i in sorted(t4) if i in e2 and all(s in e2[i] for s in ra.SEEDS)]
    s1 = np.array([t4[i][0] for i in ids], bool)
    r1 = np.array([t4[i][1] for i in ids], bool)
    n3 = np.array([[e2[i][s][1] for s in ra.SEEDS] for i in ids], bool)
    out["S3_help"] = {
        "tasks": len(ids),
        "T": t_help(s1, r1, n3),
        "p": perm_test_help(s1, r1, n3, B, rng),
    }
    # level and power in the D-M8 model (section 19 D)
    _, ids2 = ra.zmatrix(e2)
    k = np.array([sum(e2[i][s][1] for s in ra.SEEDS) for i in ids2], float)
    a, b = hp.beta_mom(k, len(ra.SEEDS))
    out["level_power"] = {}
    for q in (0.0, 0.2, 0.3):
        rej = 0
        for _ in range(power_reps):
            none, skill = ps.simulate_cell(rng, a, b, len(ids2), 3, q)
            rej += perm_test(skill, none, power_B, rng) <= 0.05
        out["level_power"][str(q)] = rej / power_reps
        print("level/power", q, rej / power_reps, flush=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, required=True)
    ap.add_argument("--perms", type=int, required=True)
    ap.add_argument("--power-reps", type=int, required=True)
    ap.add_argument("--power-perms", type=int, required=True)
    a = ap.parse_args()
    rng = np.random.default_rng(SEED)
    out = {"P_A": p_a(rng, a.boot)}
    print("P-A", json.dumps(out["P_A"]), flush=True)
    out["P_B"] = p_b(rng, a.perms, a.power_reps, a.power_perms)
    Path("results/section21.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out["P_B"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
