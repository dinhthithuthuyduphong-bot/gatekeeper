"""Design table for the Phase 3 decision: paired trials per cell for 80% power, as a function of
how many cells share the alpha budget and of the true effect size.

Fewer cells (coarser scopes, fewer skills tested) -> larger alpha per cell -> fewer trials.
Writes results/design_table.json.
"""

from __future__ import annotations

import json
from pathlib import Path

from gatekeeper.analysis import trials_needed

ALPHA_FAMILY = 0.05
CELL_SHARE = 0.7  # AlphaLedger default: 70% of alpha for (skill, scope) cells
CELLS = [10, 50, 100, 300, 1600]
EFFECTS = [-0.25, -0.15, -0.10]
THETAS = [0.05, 0.02]
POWER = 0.8
MAX_BUDGET = 3000


def main() -> None:
    rows = []
    for theta in THETAS:
        for n_cells in CELLS:
            a = ALPHA_FAMILY * CELL_SHARE / n_cells
            row = {"theta": theta, "cells": n_cells, "alpha_cell": a, "trials": {}}
            for eff in EFFECTS:
                n = trials_needed(
                    eff, a, theta=theta, power=POWER, max_budget=MAX_BUDGET, reps=300, seed=11
                )
                row["trials"][str(eff)] = n
                print(f"theta={theta} cells={n_cells:5d} alpha={a:.2e} STR={eff:+.2f} -> n80={n}")
            rows.append(row)
    out = {
        "alpha_family": ALPHA_FAMILY,
        "cell_share": CELL_SHARE,
        "power": POWER,
        "thetas": THETAS,
        "max_budget": MAX_BUDGET,
        "rows": rows,
    }
    Path("results").mkdir(exist_ok=True)
    Path("results/design_table.json").write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    main()
