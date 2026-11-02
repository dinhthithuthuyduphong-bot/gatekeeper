"""Statistics for the pilot (Phase 3) and the analysis (Phase 7).

* variance_components   - sigma_T^2 (task difficulty) and sigma_S^2 (paired noise) from pilot data
* trials_needed         - simulation-calibrated paired trials for a target power (Prop. 9 corrected)
* endpoint_power        - power of the primary endpoint (harmful-acceptance margin)
* cluster_bootstrap_ci  - CI resampling whole repositories (Cameron et al. 2008)
* benjamini_hochberg    - BH step-up for secondary comparisons
* harm_coverage_curve / harm_at_coverage - comparison "at matched clean-reuse coverage"
* penalty_sweep         - ranking stability of systems for regression weights w in [0.2, 2.0]
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence

import numpy as np

from gatekeeper.simulate import simulate

__all__ = [
    "benjamini_hochberg",
    "cluster_bootstrap_ci",
    "endpoint_power",
    "harm_at_coverage",
    "harm_coverage_curve",
    "kendall_tau",
    "penalty_sweep",
    "trials_needed",
    "variance_components",
]


def variance_components(
    records: Sequence[tuple[str, float, float]],
) -> dict[str, float]:
    """records = (task_id, loss_with, loss_without), possibly several runs per task.

    Model (docs/theory/corrections.md section 6):
    l_with = mu_pi + T + e_pi,  l_without = mu_0 + T + e_0.
    Cov(l_with, l_without) across tasks estimates sigma_T^2; Var(l_with - l_without) estimates
    sigma_S^2. Returns also the implied unpaired/paired sample-size ratio 1 + 2 sT2/sS2.
    """
    if len(records) < 3:
        raise ValueError("need at least 3 paired records")
    w = np.array([r[1] for r in records], dtype=float)
    o = np.array([r[2] for r in records], dtype=float)
    z = w - o
    sigma_s2 = float(z.var(ddof=1))
    sigma_t2 = float(max(np.cov(w, o, ddof=1)[0, 1], 0.0))
    ratio = 1.0 + 2.0 * sigma_t2 / sigma_s2 if sigma_s2 > 0 else float("inf")
    return {
        "n": len(records),
        "n_tasks": len({r[0] for r in records}),
        "mean_Z": float(z.mean()),
        "sigma_S2": sigma_s2,
        "sigma_T2": sigma_t2,
        "unpaired_over_paired": ratio,
    }


def trials_needed(
    str_true: float,
    alpha: float,
    theta: float = 0.05,
    power: float = 0.8,
    p_plus: float = 0.10,
    max_budget: int = 5000,
    reps: int = 300,
    seed: int = 0,
) -> int | None:
    """Smallest budget n (on a doubling grid, then bisection) so that Pr[admit within n] >= power.
    None if not reachable within max_budget."""
    res = simulate(str_true, alpha, theta, p_plus, budget=max_budget, reps=reps, seed=seed)
    if res.admit_rate < power:
        return None
    # admission time quantile gives the answer directly: rerun recording stop times
    lo, hi = 1, max_budget
    while lo < hi:
        mid = (lo + hi) // 2
        r = simulate(str_true, alpha, theta, p_plus, budget=mid, reps=reps, seed=seed)
        if r.admit_rate >= power:
            hi = mid
        else:
            lo = mid + 1
    return lo


def endpoint_power(
    n_harmful: int,
    p_baseline: float,
    p_gatekeeper: float,
    margin: float = 0.05,
    reps: int = 4000,
    n_boot: int = 400,
    level: float = 0.95,
    seed: int = 0,
    coupling: str = "independent",
) -> float:
    """Power that the lower CI bound of (harmful acceptance baseline - Gatekeeper) exceeds
    `margin`, both systems judged on the same n_harmful pairs (paired bootstrap over pairs).

    coupling="independent": the two systems admit harmful pairs independently (pessimistic).
    coupling="nested": every harmful pair Gatekeeper admits is also admitted by the baseline
    (optimistic: smallest variance of the paired difference).
    margin=0 gives the superiority test.
    """
    if coupling not in ("independent", "nested"):
        raise ValueError("coupling must be 'independent' or 'nested'")
    if coupling == "nested" and p_gatekeeper > p_baseline:
        raise ValueError("nested coupling needs p_gatekeeper <= p_baseline")
    rng = np.random.default_rng(seed)
    wins = 0
    q = (1 - level) / 2
    for _ in range(reps):
        if coupling == "independent":
            b = rng.random(n_harmful) < p_baseline
            g = rng.random(n_harmful) < p_gatekeeper
            d = b.astype(float) - g.astype(float)
        else:
            d = (rng.random(n_harmful) < (p_baseline - p_gatekeeper)).astype(float)
        idx = rng.integers(0, n_harmful, size=(n_boot, n_harmful))
        boot = d[idx].mean(axis=1)
        if np.quantile(boot, q) > margin:
            wins += 1
    return wins / reps


def cluster_bootstrap_ci(
    values: Sequence[float],
    clusters: Sequence[str],
    stat: Callable[[np.ndarray], float] = np.mean,
    n_boot: int = 2000,
    level: float = 0.95,
    seed: int = 0,
) -> tuple[float, float, float]:
    """Point estimate and percentile CI, resampling whole clusters (repositories)."""
    if len(values) != len(clusters):
        raise ValueError("values and clusters must have the same length")
    groups: dict[str, list[float]] = defaultdict(list)
    for v, c in zip(values, clusters, strict=True):
        groups[c].append(float(v))
    keys = list(groups)
    arrays = [np.array(groups[k]) for k in keys]
    rng = np.random.default_rng(seed)
    stats = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.integers(0, len(keys), size=len(keys))
        stats[b] = stat(np.concatenate([arrays[i] for i in pick]))
    q = (1 - level) / 2
    return (
        float(stat(np.asarray(values, dtype=float))),
        float(np.quantile(stats, q)),
        float(np.quantile(stats, 1 - q)),
    )


def benjamini_hochberg(pvalues: Sequence[float], q: float = 0.05) -> list[bool]:
    """Reject flags under BH step-up at FDR level q."""
    p = np.asarray(pvalues, dtype=float)
    m = len(p)
    if m == 0:
        return []
    order = np.argsort(p)
    thresh = q * (np.arange(1, m + 1) / m)
    passed = p[order] <= thresh
    k = int(np.max(np.nonzero(passed)[0])) + 1 if passed.any() else 0
    reject = np.zeros(m, dtype=bool)
    reject[order[:k]] = True
    return reject.tolist()


def harm_coverage_curve(
    scores: Sequence[float], labels: Sequence[str]
) -> list[tuple[float, float, float]]:
    """Sweep the admission threshold of a system that admits pairs with score >= t.

    labels in {"harmful", "neutral", "beneficial"}. Returns (threshold, coverage, harmful_acc)
    with coverage = admitted beneficial / beneficial, harmful_acc = admitted harmful / harmful.
    """
    s = np.asarray(scores, dtype=float)
    lab = np.asarray(labels)
    nb = max(int((lab == "beneficial").sum()), 1)
    nh = max(int((lab == "harmful").sum()), 1)
    out = []
    for t in np.unique(np.concatenate([s, [np.inf]]))[::-1]:
        adm = s >= t
        out.append(
            (
                float(t),
                float((adm & (lab == "beneficial")).sum() / nb),
                float((adm & (lab == "harmful")).sum() / nh),
            )
        )
    return out


def harm_at_coverage(curve: Sequence[tuple[float, float, float]], coverage: float) -> float:
    """Harmful acceptance interpolated at a given clean-reuse coverage (matched comparison)."""
    cov = np.array([c[1] for c in curve])
    harm = np.array([c[2] for c in curve])
    order = np.argsort(cov, kind="stable")
    cov, harm = cov[order], harm[order]
    # for repeated coverage values keep the smallest harm (best operating point)
    uc, idx = np.unique(cov, return_index=True)
    best = np.array([harm[cov == c].min() for c in uc])
    return float(np.interp(coverage, uc, best))


def kendall_tau(a: Sequence[float], b: Sequence[float]) -> float:
    a, b = np.asarray(a), np.asarray(b)
    n = len(a)
    conc = disc = 0
    for i in range(n):
        for j in range(i + 1, n):
            s = np.sign(a[i] - a[j]) * np.sign(b[i] - b[j])
            conc += s > 0
            disc += s < 0
    pairs = n * (n - 1) / 2
    return float((conc - disc) / pairs) if pairs else 1.0


def penalty_sweep(
    systems: Mapping[str, tuple[float, float]],
    weights: Sequence[float] = (0.2, 0.5, 1.0, 1.5, 2.0),
    reference_w: float = 0.5,
) -> dict[str, object]:
    """systems = {name: (mean F, mean R)}. Mean loss is linear in (F, R), so the system ranking
    under each w follows from (F + w R)/(1 + w). Reports Kendall tau to the reference ranking."""
    names = list(systems)

    def losses(w: float) -> list[float]:
        return [(systems[n][0] + w * systems[n][1]) / (1 + w) for n in names]

    ref = losses(reference_w)
    taus = {w: kendall_tau(ref, losses(w)) for w in weights}
    return {
        "names": names,
        "reference_w": reference_w,
        "tau": taus,
        "stable": all(t == 1.0 for t in taus.values()),
    }


def mean_ci(z: Sequence[float], level: float = 0.90, n_boot: int = 4000, seed: int = 0):
    """Mean and two-sided bootstrap CI of paired differences (exploratory, not anytime-valid)."""
    arr = np.asarray(z, dtype=float)
    if arr.size == 0:
        return None, None, None
    rng = np.random.default_rng(seed)
    boot = arr[rng.integers(0, arr.size, size=(n_boot, arr.size))].mean(axis=1)
    q = (1 - level) / 2
    return float(arr.mean()), float(np.quantile(boot, q)), float(np.quantile(boot, 1 - q))


def g1_decision(
    skill_z: Mapping[str, Sequence[float]],
    noise_z: Sequence[float] | None = None,
    positive_z: Sequence[float] | None = None,
    effect: float = 0.10,
) -> dict[str, object]:
    """Pre-registered G1 rules (docs/budget_200.md), applied mechanically:

    * pipeline check: the noise control's 90% CI must contain 0 (else pairing is broken);
    * sensitivity check: the positive control's mean Z must be <= -effect (else the measurement
      cannot detect a large effect, and a null result on the skills would be uninformative);
    * G1 passes if some skill has mean Z <= -effect AND its 90% CI upper bound < 0.
    Exploratory screening only: the anytime-valid e-process is for the confirmatory study.
    """
    out: dict[str, object] = {"effect": effect, "skills": {}}
    ok_pipeline = True
    if noise_z is not None and len(noise_z):
        m, lo, hi = mean_ci(noise_z)
        ok_pipeline = lo <= 0.0 <= hi
        out["noise_control"] = {"n": len(noise_z), "mean": m, "ci90": [lo, hi], "ok": ok_pipeline}
    sensitive = True
    if positive_z is not None and len(positive_z):
        m, lo, hi = mean_ci(positive_z)
        sensitive = m <= -effect
        out["positive_control"] = {
            "n": len(positive_z),
            "mean": m,
            "ci90": [lo, hi],
            "ok": sensitive,
        }
    passing = []
    for sid, z in skill_z.items():
        m, lo, hi = mean_ci(z)
        hit = m is not None and m <= -effect and hi < 0.0
        out["skills"][sid] = {"n": len(z), "mean": m, "ci90": [lo, hi], "promising": hit}
        if hit:
            passing.append(sid)
    if not ok_pipeline:
        verdict = "STOP: noise control shows a non-zero effect (pairing or seeding is broken)"
    elif not sensitive:
        verdict = "STOP: positive control too weak; the pilot cannot detect large effects"
    elif passing:
        verdict = "G1 PASS: " + ", ".join(passing)
    elif skill_z:
        verdict = f"G1 FAIL: no skill with mean Z <= -{effect:.2f} and CI below 0"
    else:
        verdict = "controls OK; run stage C"
    out["verdict"] = verdict
    return out
