"""Variance components measured in the pilot (TODO Phase 3), on the SWE-bench resolved scale.

- sigma_S^2 (run-to-run, per arm): half the variance of the A/A difference in B3
  (two identical no-skill runs per task: Var(D) = 2 sigma_S^2).
- Within-task variance of Z across seeds and between-task variance of the true task effect from
  the confirmation runs (3 seeds x 32 tasks), by the method of moments (one-way random-effects
  ANOVA; the DerSimonian-Laird family, Veroniki et al. 2016): Var(mean_i) = tau^2 + s_w^2 / m.
Writes results/pilot_variance.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import analyze_g1_final as gf  # noqa: E402


def unresolved(loss: float) -> float:
    return float(not gf.resolved(loss))


def main() -> int:
    b3 = json.loads(Path("results/pilot/g1-b3.json").read_text())
    aa = np.array(
        [
            unresolved(p["loss_with"]) - unresolved(p["loss_without"])
            for p in b3["skills"]["control-none-seed1"]["pairs"]
        ]
    )
    runs = [json.loads(Path(f"results/pilot/g1-c-s{s}.json").read_text()) for s in (11, 21, 31)]
    ids = sorted(p["instance_id"] for p in runs[0]["skills"]["validation-error"]["pairs"])
    z = np.array(
        [
            [
                unresolved(p["loss_with"]) - unresolved(p["loss_without"])
                for p in sorted(
                    r["skills"]["validation-error"]["pairs"], key=lambda q: q["instance_id"]
                )
            ]
            for r in runs
        ]
    )
    m = z.shape[0]
    s_w2 = float(z.var(axis=0, ddof=1).mean())
    tau2 = max(0.0, float(z.mean(axis=0).var(ddof=1) - s_w2 / m))
    out = {
        "scale": "SWE-bench resolved (unresolved indicator)",
        "sigma_S2_per_arm_B3_AA": float(aa.var(ddof=1) / 2),
        "B3_AA_n_tasks": int(aa.size),
        "confirmation": {
            "skill": "validation-error",
            "n_tasks": len(ids),
            "n_seeds": m,
            "within_task_var_Z": s_w2,
            "between_task_var_true_effect_MoM": tau2,
            "var_task_mean_for_m_seeds": {k: tau2 + s_w2 / k for k in (1, 3, 5, 10)},
        },
    }
    Path("results/pilot_variance.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
