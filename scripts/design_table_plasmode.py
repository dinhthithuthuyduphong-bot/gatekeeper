"""Plasmode design table (TODO Phase 3): trials per cell for the anytime-valid e-process, with every
input measured or published, replacing the hand-picked scenario of scripts/design_table.py.

- Per-trial Z in {-1, 0, 1} (SWE-bench resolved). The discordance level p_plus = P(Z = +1) is
  MEASURED: 0.04 (stage C, both arms seed 1) and 0.08 (confirmation, mean of P(+1), P(-1)).
- True effects STR from the PUBLISHED SWE-Skills-Bench distribution: p25 magnitude 0.02, the 15%
  tail 0.05, p05 0.109 (results/sskb_analysis.json).
- alpha per cell = alpha_family / K with equal weights (Bonferroni, no prior ranking); K = number
  of (skill, scope) hypotheses; alpha_family = 0.025: the admission claim ("the skill helps") is
  ONE-sided, and ICH E9's one-sided level is 0.025 (= two-sided 0.05). (Was 0.05 with a wrong
  "two-sided convention" label: audit A41.)
- Power 80% (Cohen 1988 convention, reported as such); theta in {0, 0.02, 0.05}.
Plasmode simulation: Franklin et al. 2014. Writes results/design_table_plasmode.json.
"""

from __future__ import annotations

import json
from pathlib import Path

from gatekeeper.analysis import trials_needed

ALPHA_FAMILY = 0.025
P_PLUS = [0.04, 0.08]
EFFECTS = [-0.02, -0.05, -0.109]
THETAS = [0.0, 0.02, 0.05]
CELLS = [1, 3, 10, 30, 100]
POWER = 0.8
MAX_BUDGET = 4000


def main() -> int:
    rows = []
    for pp in P_PLUS:
        for th in THETAS:
            for k in CELLS:
                a = ALPHA_FAMILY / k
                row = {"p_plus": pp, "theta": th, "cells": k, "alpha_cell": a, "trials": {}}
                for eff in EFFECTS:
                    if eff > -th or pp - eff > 1:  # effect not beyond theta: never admissible
                        row["trials"][str(eff)] = None
                        continue
                    n = trials_needed(
                        eff,
                        a,
                        theta=th,  # theta = 0 is a valid null (audit A42)
                        power=POWER,
                        p_plus=pp,
                        max_budget=MAX_BUDGET,
                        reps=300,
                        seed=11,
                    )
                    row["trials"][str(eff)] = n
                rows.append(row)
                print(f"p+={pp} theta={th} K={k:3d} -> {row['trials']}", flush=True)
    out = {
        "inputs": {
            "alpha_family": ALPHA_FAMILY,
            "p_plus_measured": P_PLUS,
            "effects_published": EFFECTS,
            "thetas": THETAS,
            "power": POWER,
            "max_budget": MAX_BUDGET,
        },
        "rows": rows,
    }
    Path("results/design_table_plasmode.json").write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
