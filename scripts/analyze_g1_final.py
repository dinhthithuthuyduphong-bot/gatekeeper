"""Pre-registered G1 verdict, standards-based (docs/preregistration_g1_v2.md, addendum 3).

  select : python scripts/analyze_g1_final.py select --stage-c g1-c
           -> skills with mean Z(resolved) < 0, and the number of confirmation seeds the budget pays
  verdict: python scripts/analyze_g1_final.py verdict --stage-c g1-c --confirm g1-c-s11 g1-c-s21 ...
           -> sign-flip permutation test per skill (confirmation data only), Holm at one-sided
              alpha 0.025, A/A TOST between the no-skill arms of two confirmation seeds, MDE
              with Browne's variance bound. Writes results/g1_final.json.

Methods: SWE-bench resolved (Jimenez et al. 2024); data splitting (Cox 1975); sign-flip
permutation test (Fisher 1935, Pitman 1937); Holm (1979); TOST (Lakens et al. 2018); pilot
variance upper confidence limit (Browne 1995).
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

ALPHA_FAMILY = 0.025  # one-sided, = two-sided 0.05
POWER = 0.8
BROWNE_COVERAGE = 0.9
SEED_STEP = 10
RESULTS = Path("results/pilot")


def resolved(loss: float) -> bool:
    return abs(loss) < 1e-12  # loss = 0 <=> F = 0 and R = 0 <=> SWE-bench "resolved"


def z_resolved(pairs: list[dict]) -> dict[str, float]:
    """Z = 1[unresolved | skill] - 1[unresolved | no skill]; negative = the skill helps."""
    return {
        p["instance_id"]: float(not resolved(p["loss_with"]))
        - float(not resolved(p["loss_without"]))
        for p in pairs
    }


def no_skill_unresolved(run: dict) -> dict[str, float]:
    out = {}
    for s in run.get("skills", {}).values():
        for p in s["pairs"]:
            out[p["instance_id"]] = float(not resolved(p["loss_without"]))
    return out


def select(c: dict) -> list[tuple[str, float, int]]:
    """Skills whose mean Z(resolved) on stage C is < 0, best first: (skill, mean, n_tasks)."""
    out = []
    for sk, v in c.get("skills", {}).items():
        if sk.startswith("control-"):
            continue
        z = list(z_resolved(v["pairs"]).values())
        if z and sum(z) / len(z) < 0:
            out.append((sk, sum(z) / len(z), len(z)))
    return sorted(out, key=lambda t: t[1])


def usd_per_run(run: dict) -> float:
    u = run.get("usage") or {}
    runs = sum(v.get("runs") or 0 for v in u.values())
    usd = sum((v.get("usd_per_run") or 0.0) * (v.get("runs") or 0) for v in u.values())
    return usd / runs if runs else float("nan")


def plan_seeds(
    c: dict, selected: list[tuple[str, float, int]], spent: float, cap: float
) -> tuple[list[str], int, float]:
    """Number of confirmation seeds the remaining budget pays for; drop the weakest skill until
    at least one seed fits. Returns (skills, m, usd per seed)."""
    cpr = usd_per_run(c)
    skills = [s for s, _, _ in selected]
    while skills:
        tasks = {
            p["instance_id"] for s in skills for p in c["skills"][s]["pairs"]
        }  # no-skill arm runs once on the union
        runs = len(tasks) + sum(len(c["skills"][s]["pairs"]) for s in skills)
        per_seed = runs * cpr
        m = int((cap - spent) // per_seed) if per_seed > 0 else 0
        if m >= 1:
            return skills, m, per_seed
        skills = skills[:-1]
    return [], 0, 0.0


def sign_flip_p(x: list[float], n_mc: int = 200_000, seed: int = 0) -> float:
    """One-sided p-value for H0 'no effect' against 'mean < 0' (exact for n <= 16)."""
    a = np.asarray(x, dtype=float)
    n = a.size
    if n == 0:
        return 1.0
    obs = a.mean()
    if n <= 16:
        signs = np.array(list(itertools.product((1.0, -1.0), repeat=n)))
    else:
        rng = np.random.default_rng(seed)
        signs = rng.choice((1.0, -1.0), size=(n_mc, n))
    means = (signs * np.abs(a)).mean(axis=1)
    return float(
        (np.sum(means <= obs + 1e-12) + (0 if n <= 16 else 1))
        / (len(means) + (0 if n <= 16 else 1))
    )


def holm(pvals: dict[str, float], alpha: float) -> dict[str, dict]:
    """Holm step-down: adjusted p and rejection at family level alpha."""
    order = sorted(pvals, key=pvals.get)
    k = len(order)
    out, running, stop = {}, 0.0, False
    for i, name in enumerate(order):
        adj = min(1.0, (k - i) * pvals[name])
        running = max(running, adj)
        reject = not stop and pvals[name] <= alpha / (k - i)
        stop = stop or not reject
        out[name] = {"p": pvals[name], "p_holm": running, "reject": reject}
    return out


def tost(d: list[float], margin: float, alpha: float = 0.05) -> dict:
    """Two one-sided t-tests for equivalence |E[d]| < margin (Lakens et al. 2018)."""
    a = np.asarray(d, dtype=float)
    n = a.size
    if n < 2 or margin <= 0:
        return {"n": int(n), "equivalent": False, "note": "not testable"}
    m, se = a.mean(), a.std(ddof=1) / math.sqrt(n)
    if se == 0:
        return {"n": int(n), "mean": m, "margin": margin, "equivalent": abs(m) < margin}
    p_low = 1 - stats.t.cdf((m + margin) / se, n - 1)  # H0: mean <= -margin
    p_high = stats.t.cdf((m - margin) / se, n - 1)  # H0: mean >= margin
    p = max(p_low, p_high)
    return {"n": int(n), "mean": m, "margin": margin, "p": float(p), "equivalent": bool(p < alpha)}


def mde(z_task: list[float], n_tests: int) -> float:
    """Resource-based minimal detectable effect with Browne's (1995) variance upper bound."""
    a = np.asarray(z_task, dtype=float)
    n = a.size
    if n < 2:
        return float("nan")
    v = a.var(ddof=1)
    v_ucl = (n - 1) * v / stats.chi2.ppf(1 - BROWNE_COVERAGE, n - 1)
    za = stats.norm.ppf(1 - ALPHA_FAMILY / max(1, n_tests))
    return float((za + stats.norm.ppf(POWER)) * math.sqrt(v_ucl / n))


def boot_ci(x: list[float], level: float = 0.95, n_boot: int = 10_000, seed: int = 0):
    a = np.asarray(x, dtype=float)
    rng = np.random.default_rng(seed)
    b = a[rng.integers(0, a.size, (n_boot, a.size))].mean(axis=1)
    q = (1 - level) / 2
    return [float(np.quantile(b, q)), float(np.quantile(b, 1 - q))]


def per_task_mean(runs: list[dict], skill: str, endpoint: str = "resolved") -> dict[str, float]:
    acc: dict[str, list[float]] = defaultdict(list)
    for r in runs:
        pairs = r.get("skills", {}).get(skill, {}).get("pairs", [])
        if endpoint == "resolved":
            zs = z_resolved(pairs)
        else:
            zs = {p["instance_id"]: p["loss_with"] - p["loss_without"] for p in pairs}
        for t, z in zs.items():
            acc[t].append(z)
    need = len(runs)
    return {t: sum(v) / len(v) for t, v in acc.items() if len(v) == need}


def verdict(c: dict, confirm: list[dict], skills: list[str]) -> dict:
    out: dict = {"skills": {}, "alpha_family_one_sided": ALPHA_FAMILY, "n_seeds": len(confirm)}
    pvals = {}
    for s in skills:
        zt = per_task_mean(confirm, s)
        x = list(zt.values())
        pvals[s] = sign_flip_p(x)
        lt = list(per_task_mean(confirm, s, endpoint="loss").values())
        out["skills"][s] = {
            "n_tasks": len(x),
            "mean_z_resolved": float(np.mean(x)) if x else None,
            "ci95": boot_ci(x) if x else None,
            "mde": mde(x, len(skills)),
            "mean_z_loss": float(np.mean(lt)) if lt else None,
        }
    for s, h in holm(pvals, ALPHA_FAMILY).items():
        out["skills"][s].update(h)
    # A/A on fresh data: no-skill arms of the first two confirmation seeds
    if len(confirm) >= 2:
        a, b = no_skill_unresolved(confirm[0]), no_skill_unresolved(confirm[1])
        d = [a[t] - b[t] for t in a if t in b]
        margins = [v["mde"] for v in out["skills"].values() if v["mde"] == v["mde"]]
        out["aa_tost"] = tost(d, min(margins) if margins else float("nan"))
    else:
        out["aa_tost"] = {"note": "one confirmation seed: A/A not testable"}
    aa_bad = out["aa_tost"].get("note") is None and not out["aa_tost"]["equivalent"]
    passing = [s for s, v in out["skills"].items() if v.get("reject")]
    if not skills:
        out["verdict"] = "G1 FAIL: no skill points in the helpful direction on stage C"
    elif aa_bad:
        out["verdict"] = "INCONCLUSIVE: A/A check did not establish equivalence (pipeline suspect)"
    elif passing:
        out["verdict"] = "G1 PASS: " + ", ".join(passing)
    else:
        worst = max(v["mde"] for v in out["skills"].values())
        out["verdict"] = f"G1 FAIL: no skill rejects H0 (no effect >= MDE ~{worst:.2f} detected)"
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s1 = sub.add_parser("select")
    s1.add_argument("--stage-c", required=True)
    s1.add_argument("--cap-usd", type=float, default=34.0)
    s1.add_argument("--spent-usd", type=float, required=True)
    s2 = sub.add_parser("verdict")
    s2.add_argument("--stage-c", required=True)
    s2.add_argument("--confirm", nargs="+", required=True)
    s2.add_argument("--skills", required=True, help="comma list fixed by `select`")
    a = ap.parse_args()
    c = json.loads((RESULTS / f"{a.stage_c}.json").read_text())
    if a.cmd == "select":
        sel = select(c)
        skills, m, per_seed = plan_seeds(c, sel, a.spent_usd, a.cap_usd)
        out = {
            "selected": [{"skill": s, "mean_z_resolved_stage_c": z, "n": n} for s, z, n in sel],
            "confirm_skills": skills,
            "confirm_seeds": [1 + SEED_STEP * (i + 1) for i in range(m)],
            "usd_per_seed": per_seed,
            "usd_per_run_stage_c": usd_per_run(c),
        }
        Path("results/g1_selection.json").write_text(json.dumps(out, indent=2) + "\n")
    else:
        confirm = [json.loads((RESULTS / f"{r}.json").read_text()) for r in a.confirm]
        out = verdict(c, confirm, [s for s in a.skills.split(",") if s])
        out["confirm_runs"] = a.confirm
        Path("results/g1_final.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
