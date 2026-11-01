"""External pilot on real paired data: SWE-Skills-Bench (TODO.md Phase 3, no LLM cost).

Input: data/external/swe-skills-bench/ALL_combined_cells.csv (MIT, see SOURCE.md).
Loss = 1 - pass_rate/100; Z = loss(with skill) - loss(without).

1. Variance components  -> real sigma_T^2, sigma_S^2 and the pairing saving (Prop. 9 corrected).
2. Effect sizes         -> distribution of per-(config, skill) STR, corrected for sampling noise.
3. Context dependence   -> does a skill's effect under one agent x model predict its effect under
                           another? Compared with split-half reliability inside one configuration.
4. Minimum trials       -> even a perfect skill (Z = -1 every time) needs n_min trials to admit.
5. Split-half admission -> plug-in "mean <= -theta" on 5 requirements, scored on the other 5;
                           and the anytime-valid e-process on the same 5 trials.

Writes results/sskb_analysis.json.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np

from gatekeeper.analysis import variance_components
from gatekeeper.eprocess import BettingEProcess, run_admission

SRC = Path("data/external/swe-skills-bench/ALL_combined_cells.csv")
THETAS = (0.02, 0.05)
ALPHAS = {"single cell (0.05)": 0.05, "98 skills x 1 scope": 0.05 * 0.7 / 98}


def load() -> list[dict]:
    rows = []
    with SRC.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            lw = 1 - float(r["one_pass_rate"]) / 100
            lo = 1 - float(r["none_pass_rate"]) / 100
            rows.append(
                {
                    "cfg": r["harness_model"],
                    "skill": r["skill"],
                    "batch": int(r["requirement_batch"].replace("batch", "")),
                    "lw": lw,
                    "lo": lo,
                    "z": lw - lo,
                }
            )
    return rows


def corr(a, b) -> float:
    a, b = np.asarray(a), np.asarray(b)
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def main() -> None:
    rows = load()
    cfgs = sorted({r["cfg"] for r in rows})
    skills = sorted({r["skill"] for r in rows})
    out: dict = {"source": str(SRC), "n_rows": len(rows), "configs": cfgs, "n_skills": len(skills)}

    # 1. variance components ---------------------------------------------------------------
    vc_all = variance_components(
        [(f"{r['cfg']}|{r['skill']}|{r['batch']}", r["lw"], r["lo"]) for r in rows]
    )
    out["variance_components"] = {
        "all": vc_all,
        "per_config": {
            c: variance_components(
                [(f"{r['skill']}|{r['batch']}", r["lw"], r["lo"]) for r in rows if r["cfg"] == c]
            )
            for c in cfgs
        },
    }
    z_all = np.array([r["z"] for r in rows])
    out["paired_differences"] = {
        "mean": float(z_all.mean()),
        "frac_exactly_zero": float((z_all == 0).mean()),
        "frac_abs_ge_0.05": float((np.abs(z_all) >= 0.05).mean()),
    }

    # 2. effect sizes per (config, skill) ----------------------------------------------------
    cell: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in rows:
        cell[(r["cfg"], r["skill"])].append(r["z"])
    means = np.array([np.mean(v) for v in cell.values()])
    within = np.array([np.var(v, ddof=1) / len(v) for v in cell.values()])
    var_between = max(float(means.var(ddof=1) - within.mean()), 0.0)
    out["effect_sizes"] = {
        "n_cells": len(means),
        "quantiles": dict(
            zip(
                ["min", "p05", "p25", "p50", "p75", "p95", "max"],
                np.quantile(means, [0, 0.05, 0.25, 0.5, 0.75, 0.95, 1]).round(4).tolist(),
                strict=True,
            )
        ),
        "observed_sd_of_cell_means": float(means.std(ddof=1)),
        "noise_sd_of_cell_means": float(np.sqrt(within.mean())),
        "estimated_true_sd": float(np.sqrt(var_between)),
        "share_true_variance": float(var_between / means.var(ddof=1)) if means.var() > 0 else 0.0,
        "frac_le_minus": {str(t): float((means <= -t).mean()) for t in (0.02, 0.05, 0.10)},
        "frac_gt_plus": {str(t): float((means > t).mean()) for t in (0.0, 0.02, 0.05, 0.10)},
    }

    # 3. context dependence ------------------------------------------------------------------
    by_cfg = {c: np.array([np.mean(cell[(c, s)]) for s in skills]) for c in cfgs}
    cross = {f"{a} vs {b}": corr(by_cfg[a], by_cfg[b]) for a, b in combinations(cfgs, 2)}
    split = {}
    for c in cfgs:
        odd = [
            np.mean([r["z"] for r in rows if r["cfg"] == c and r["skill"] == s and r["batch"] % 2])
            for s in skills
        ]
        even = [
            np.mean(
                [r["z"] for r in rows if r["cfg"] == c and r["skill"] == s and not r["batch"] % 2]
            )
            for s in skills
        ]
        rho = corr(odd, even)
        split[c] = {
            "split_half_r": rho,
            "spearman_brown_r": 2 * rho / (1 + rho) if rho > -1 else rho,
        }
    flips = 0
    for i in range(len(skills)):
        vals = [by_cfg[c][i] for c in cfgs]
        if min(vals) <= -0.05 and max(vals) >= 0.05:
            flips += 1
    out["context_dependence"] = {
        "cross_config_r": cross,
        "mean_cross_config_r": float(np.nanmean(list(cross.values()))),
        "within_config_reliability": split,
        "mean_within_config_reliability": float(
            np.nanmean([v["spearman_brown_r"] for v in split.values()])
        ),
        "skills_helpful_in_one_config_harmful_in_another": flips,
        "skills_helpful_in_one_config_harmful_in_another_frac": flips / len(skills),
    }

    # 4. minimum trials for a perfect skill ---------------------------------------------------
    nmin = {}
    for th in THETAS:
        for name, a in ALPHAS.items():
            ep = BettingEProcess(theta=th, alpha=a)
            n = 0
            while not ep.crossed and n < 10_000:
                ep.update(-1.0)
                n += 1
            nmin[f"theta={th}, {name}"] = n
    out["min_trials_perfect_skill"] = nmin

    # 5. split-half admission -----------------------------------------------------------------
    adm_res = {}
    for th in THETAS:
        for name, a in ALPHAS.items():
            stats = {"plugin": [0, 0, 0, 0], "eprocess": [0, 0, 0, 0], "B2": [0, 0, 0, 0]}
            n_harm = n_ben = n_neu = 0
            for (c, s), _ in cell.items():
                adm = [
                    r["z"] for r in rows if r["cfg"] == c and r["skill"] == s and r["batch"] <= 5
                ]
                held = [
                    r["z"] for r in rows if r["cfg"] == c and r["skill"] == s and r["batch"] > 5
                ]
                h = float(np.mean(held))
                label = "harmful" if h > 0 else ("beneficial" if h <= -th else "neutral")
                n_harm += label == "harmful"
                n_ben += label == "beneficial"
                n_neu += label == "neutral"
                decisions = {
                    "plugin": float(np.mean(adm)) <= -th,
                    "eprocess": run_admission(adm, th, a, budget=len(adm)).admitted,
                    "B2": True,
                }
                for k, d in decisions.items():
                    if d:
                        stats[k][0] += 1
                        stats[k][1] += label == "harmful"
                        stats[k][2] += label == "beneficial"
                        stats[k][3] += label == "neutral"
            adm_res[f"theta={th}, {name}"] = {
                "labels": {"harmful": n_harm, "beneficial": n_ben, "neutral": n_neu},
                **{
                    k: {
                        "admitted": v[0],
                        "harmful_acceptance": v[1] / max(n_harm, 1),
                        "clean_reuse_coverage": v[2] / max(n_ben, 1),
                    }
                    for k, v in stats.items()
                },
            }
    out["split_half_admission"] = adm_res

    Path("results").mkdir(exist_ok=True)
    Path("results/sskb_analysis.json").write_text(json.dumps(out, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: out[k]
                for k in ("paired_differences", "context_dependence", "min_trials_perfect_skill")
            },
            indent=2,
        )
    )
    print("pairing saving (all):", round(vc_all["unpaired_over_paired"], 2))
    print("effect sizes:", json.dumps(out["effect_sizes"], indent=1))
    for k, v in adm_res.items():
        print(k, json.dumps(v))


if __name__ == "__main__":
    main()
