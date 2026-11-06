"""Power of the cross-agent transfer correlation for SWE-Skills-Bench skills (A83). Free.

  python scripts/sskb_transfer_power.py --n-skills 66

Question: if we rerun n skills once (10 requirements, 1 seed, both arms) on our agent and
correlate our per-skill effect with SSKB's mean effect over its 4 configurations, what r do we
expect and what is the power of a test of r > 0?

Variance components (all in pp, per skill):
- transferable variance = mean pairwise covariance of skill effects across SSKB configurations
  (the part of a skill's effect that is shared by different agent-model pairs);
- SSKB side variance = variance across skills of the 4-config mean effect;
- our side variance = transferable variance + noise variance of a 10-requirement mean, the noise
  taken from our measured per-requirement differences (results/sskb_probe.json, section 22).
Expected r (100% transfer of the shared part) = cov / sqrt(var_sskb * var_ours).
Power uses the Fisher z approximation, z = atanh(r) * sqrt(n - 3) (Fisher 1921).
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import statistics as st
from collections import defaultdict
from pathlib import Path

from scipy.stats import norm

S = Path("/tmp/claude-0/-home-user-gatekeeper/cfb16e31-7b52-5c1a-8071-d03b24bd210f/scratchpad")
CELLS = S / "ext/sskb/results/final_results/ALL_combined_cells.csv"
PROBE = Path("results/sskb_probe.json")
N_REQ = 10  # requirements per skill in SSKB (one batch = one requirement)


def skill_effects(path: Path) -> dict[str, dict[str, float]]:
    d: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    with path.open() as f:
        for r in csv.DictReader(f):
            d[r["harness_model"]][r["skill"]].append(float(r["delta_pp"]))
    common = set.intersection(*(set(v) for v in d.values()))
    return {c: {s: st.mean(d[c][s]) for s in sorted(common)} for c in sorted(d)}


def probe_diffs(path: Path) -> list[float]:
    by: dict[tuple, dict[str, float]] = defaultdict(dict)
    for r in json.loads(path.read_text())["rows"]:
        by[(r["skill"], r["batch"], r["seed"])][r["arm"]] = r["pass_rate"]
    return [100 * (v["skill"] - v["none"]) for v in by.values() if len(v) == 2]


def power(r: float, n: int, alpha: float, sides: int) -> float:
    z = math.atanh(r) * math.sqrt(n - 3)
    return float(norm.sf(norm.isf(alpha / sides) - z))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-skills", type=int, required=True)
    ap.add_argument("--alpha", type=float, required=True)
    a = ap.parse_args()
    eff = skill_effects(CELLS)
    cfgs = list(eff)
    skills = list(eff[cfgs[0]])
    pairs = list(itertools.combinations(cfgs, 2))
    xs = {c: [eff[c][s] for s in skills] for c in cfgs}
    covs = [st.covariance(xs[p], xs[q]) for p, q in pairs]
    cors = [st.correlation(xs[p], xs[q]) for p, q in pairs]
    cov = st.mean(covs)
    var_sskb = st.variance([st.mean(eff[c][s] for c in cfgs) for s in skills])
    diffs = probe_diffs(PROBE)
    noise_sd = st.stdev(diffs) / math.sqrt(N_REQ)
    var_ours = cov + noise_sd**2
    r_exp = cov / math.sqrt(var_sskb * var_ours)
    out = {
        "n_configs": len(cfgs),
        "n_skills_common": len(skills),
        "cross_config_corr_min": min(cors),
        "cross_config_corr_max": max(cors),
        "transferable_cov_pp2": cov,
        "transferable_sd_pp": math.sqrt(cov),
        "sskb_mean_effect_var_pp2": var_sskb,
        "our_diff_sd_per_requirement_pp": st.stdev(diffs),
        "our_n_diffs": len(diffs),
        "our_noise_sd_10req_pp": noise_sd,
        "expected_r_full_transfer": r_exp,
        "n_skills": a.n_skills,
        "alpha": a.alpha,
        "power_one_sided": power(r_exp, a.n_skills, a.alpha, 1),
        "power_two_sided": power(r_exp, a.n_skills, a.alpha, 2),
    }
    Path("results/sskb_transfer_power.json").write_text(json.dumps(out, indent=1) + "\n")
    for k, v in out.items():
        print(f"{k}: {v:.4g}" if isinstance(v, float) else f"{k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
