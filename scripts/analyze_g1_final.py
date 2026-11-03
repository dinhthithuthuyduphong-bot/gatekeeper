"""Pre-registered G1 verdict, standards-based (docs/preregistration_g1_v2.md, addendum 3).

  select : python scripts/analyze_g1_final.py select --stage-c g1-c
           -> skills with mean Z(resolved) < 0, and the number of confirmation seeds the budget pays
  verdict: python scripts/analyze_g1_final.py verdict --stage-c g1-c --confirm g1-c-s11 g1-c-s21 ...
           -> EXACT sign-flip permutation test per skill (confirmation data only), Holm at
              one-sided alpha 0.025, exact two-sided A/A test between the no-skill arms of two
              confirmation seeds, t-interval and critical effect. Writes results/g1_final.json.

Methods: SWE-bench resolved (Jimenez et al. 2024); data splitting (Cox 1975); sign-flip
permutation test (Fisher 1935, Pitman 1937), computed exactly by convolution; Holm (1979);
A/A test (Kohavi et al. 2020); Student t interval. Every number is either the value input
ALPHA_FAMILY or derived from it (docs/number_provenance.md, revision of addendum 3).
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

ALPHA_FAMILY = 0.025  # one-sided, ICH E9 standard (= two-sided 0.05); a value input (Wald)
CI_LEVEL = 1 - 2 * ALPHA_FAMILY  # derived: the two-sided interval matching the one-sided test
SEED_STEP = 10  # derived: seeds must differ from every seed used before and from seed+1 controls
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


def _lattice(x: list[float]) -> tuple[list[int], int]:
    """Per-task means of m values in {-1, 0, 1} are multiples of 1/m: return integers and m."""
    for m in range(1, 65):
        b = [round(v * m) for v in x]
        if all(abs(v * m - k) < 1e-9 for v, k in zip(x, b, strict=True)):
            return b, m
    raise ValueError("values are not on a lattice k/m; exact test not available")


def _null_dist(b: list[int]) -> dict[int, float]:
    """Exact distribution of sum(s_i * |b_i|), s_i = +-1 with prob 1/2 (convolution)."""
    dist = {0: 1.0}
    for v in (abs(k) for k in b):
        nxt: dict[int, float] = defaultdict(float)
        for s, pr in dist.items():
            nxt[s + v] += pr / 2
            nxt[s - v] += pr / 2
        dist = dict(nxt)
    return dist


def sign_flip_p(x: list[float], two_sided: bool = False) -> float:
    """EXACT sign-flip permutation p-value (Fisher 1935; Pitman 1937), no Monte Carlo.
    One-sided: H0 'no effect' against 'mean < 0'. Two-sided: against 'mean != 0'."""
    if not x:
        return 1.0
    b, _ = _lattice(x)
    obs = sum(b)
    dist = _null_dist(b)
    if two_sided:
        return float(sum(p for s, p in dist.items() if abs(s) >= abs(obs)))
    return float(sum(p for s, p in dist.items() if s <= obs))


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
        out[name] = {
            "p": pvals[name],
            "p_holm": running,
            "reject": reject,
            "p_holm_level": alpha / (k - i),
        }
    return out


def t_interval(x: list[float], level: float = CI_LEVEL) -> list[float]:
    """Student-t interval for the mean (CLT); level derived from ALPHA_FAMILY."""
    a = np.asarray(x, dtype=float)
    n = a.size
    if n < 2:
        return [float("nan"), float("nan")]
    se = a.std(ddof=1) / math.sqrt(n)
    q = stats.t.ppf(1 - (1 - level) / 2, n - 1)
    return [float(a.mean() - q * se), float(a.mean() + q * se)]


def critical_effect(x: list[float], n_tests: int) -> float:
    """Smallest helpful mean effect the EXACT sign-flip test can declare at Holm's first level
    a' = ALPHA_FAMILY / n_tests: the most negative-tail cut of the same null distribution the
    test uses (conditional on the observed |Z_i|). Returned as a positive magnitude."""
    if not x:
        return float("nan")
    b, m = _lattice(x)
    dist = _null_dist(b)
    a = ALPHA_FAMILY / max(1, n_tests)
    acc, cut = 0.0, None
    for s in sorted(dist):
        acc += dist[s]
        if acc <= a + 1e-15:
            cut = s
        else:
            break
    if cut is None:  # not even the most extreme outcome is significant
        return float("inf")
    return float(-cut / (m * len(x)))


def repo_of(instance_id: str) -> str:
    """SWE-bench ids are owner__repo-number; anything else is its own cluster."""
    if "__" not in instance_id:
        return instance_id
    owner, rest = instance_id.split("__", 1)
    return owner + "/" + rest.rsplit("-", 1)[0]


def paired_t_p(x: list[float]) -> float:
    """S1. One-sided paired t-test (Student 1908) on task means: H0 E[Z] >= 0 vs E[Z] < 0.
    Needs no symmetry/exchangeability, only the CLT (Miller 2024, recommendation 1)."""
    a = np.asarray(x, dtype=float)
    n = a.size
    if n < 2 or a.std(ddof=1) == 0:
        return 1.0 if n < 2 or a.mean() >= 0 else 0.0
    t_stat = a.mean() / (a.std(ddof=1) / math.sqrt(n))
    return float(stats.t.cdf(t_stat, n - 1))


def cluster_sign_flip_p(per_task: dict[str, float]) -> tuple[float, int]:
    """S2. Exact sign-flip test on REPOSITORY sums (Canay, Romano & Shaikh 2017; wild cluster
    with Rademacher weights, Cameron, Gelbach & Miller 2008): valid under within-repo dependence.
    One-sided p for 'mean < 0'. Returns (p, number of clusters)."""
    sums: dict[str, float] = defaultdict(float)
    for t_id, z in per_task.items():
        sums[repo_of(t_id)] += z
    vals = list(sums.values())
    return sign_flip_p(vals), len(vals)


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
    out: dict = {
        "skills": {},
        "alpha_family_one_sided": ALPHA_FAMILY,
        "ci_level": CI_LEVEL,
        "n_seeds": len(confirm),
    }
    pvals = {}
    for s in skills:
        zt = per_task_mean(confirm, s)
        x = list(zt.values())
        pvals[s] = sign_flip_p(x)
        lt = list(per_task_mean(confirm, s, endpoint="loss").values())
        out["skills"][s] = {
            "n_tasks": len(x),
            "mean_z_resolved": float(np.mean(x)) if x else None,
            "ci": t_interval(x) if x else None,
            "critical_effect": critical_effect(x, len(skills)),
            "mean_z_loss_secondary": float(np.mean(lt)) if lt else None,
            "helped_tasks": int(sum(v < 0 for v in x)),
            "hurt_tasks": int(sum(v > 0 for v in x)),
        }
    for s, h in holm(pvals, ALPHA_FAMILY).items():
        out["skills"][s].update(h)
    # sensitivity analyses (ICH E9 / E9(R1)): each removes one assumption of the primary test
    for s in skills:
        zt = per_task_mean(confirm, s)
        p_t = paired_t_p(list(zt.values()))
        p_c, g = cluster_sign_flip_p(zt)
        v = out["skills"][s]
        v["s1_paired_t_p"] = p_t
        v["s2_cluster_sign_flip_p"] = p_c
        v["s2_clusters"] = g
        # same Holm level as the primary decision for this skill
        lvl = v["p_holm_level"]
        v["robust"] = bool(v.get("reject") and p_t <= lvl and p_c <= lvl)
    # secondary (safety) hypothesis, reported only: the same tests in the HARM direction, Holm
    hp = {s: sign_flip_p([-v for v in per_task_mean(confirm, s).values()]) for s in skills}
    for s, h in holm(hp, ALPHA_FAMILY).items():
        zt = per_task_mean(confirm, s)
        x = [-v for v in zt.values()]
        out["skills"][s]["harm"] = {
            "p": h["p"],
            "p_holm": h["p_holm"],
            "reject": bool(
                h["reject"]
                and paired_t_p(x) <= h["p_holm_level"]
                and cluster_sign_flip_p({k: -v for k, v in zt.items()})[0] <= h["p_holm_level"]
            ),
        }
    # A/A on fresh data: no-skill arms of two confirmation seeds; exact two-sided sign-flip test
    # at the two-sided level matching ALPHA_FAMILY (Kohavi et al.: an A/A must not reject)
    if len(confirm) >= 2:
        a, b = no_skill_unresolved(confirm[0]), no_skill_unresolved(confirm[1])
        d = [a[t] - b[t] for t in a if t in b]
        p_aa = sign_flip_p(d, two_sided=True) if d else 1.0
        out["aa"] = {
            "n": len(d),
            "mean": float(np.mean(d)) if d else None,
            "ci": t_interval(d) if d else None,
            "p_two_sided": p_aa,
            "flag": bool(p_aa < 2 * ALPHA_FAMILY),
        }
    else:
        out["aa"] = {"note": "one confirmation seed: A/A not testable"}
    aa_bad = bool(out["aa"].get("flag"))
    passing = [s for s, v in out["skills"].items() if v.get("robust")]
    fragile = [s for s, v in out["skills"].items() if v.get("reject") and not v.get("robust")]
    if not skills:
        out["verdict"] = "G1 FAIL: no skill points in the helpful direction on stage C"
    elif aa_bad:
        out["verdict"] = "INCONCLUSIVE: the A/A check rejects (pipeline suspect)"
    elif passing:
        out["verdict"] = "G1 PASS: " + ", ".join(passing)
    elif fragile:
        out["verdict"] = (
            "INCONCLUSIVE: primary test rejects but a sensitivity analysis does not "
            "(" + ", ".join(fragile) + ")"
        )
    else:
        crit = max(v["critical_effect"] for v in out["skills"].values())
        out["verdict"] = (
            "G1 FAIL: no skill rejects H0 (effects smaller than the critical effect "
            f"~{crit:.2f} cannot be declared with these data)"
        )
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
