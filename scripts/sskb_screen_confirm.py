"""Screen-then-confirm on SWE-Skills-Bench (external, published data; no LLM cost).

Same design as G1 (docs/g1_verdict.md), applied to 392 (agent config, skill) cells:
a naive screen admits a cell if its mean Z on requirements 1-5 is in the helpful direction
(and, separately, <= -theta); the admitted cells are then scored on the HELD-OUT requirements 6-10
(data splitting, Cox 1975). If screening picked real effects, held-out effects of admitted cells
are negative; if the screen mostly picks noise, they regress to the overall mean.

Exploratory: the data were inspected before (results/sskb_analysis.json), so this is not
pre-registered. Inference on held-out cell means: paired t (Student 1908) and a sign-flip
permutation test by Monte Carlo with the identity included (exact, Hemerik & Goeman 2018).
Writes results/sskb_screen_confirm.json.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

SRC = Path("data/external/swe-skills-bench/ALL_combined_cells.csv")
THETAS = (
    0.0,
    0.02,
    0.05,
)  # 0 = "helpful direction" (the G1 selection rule); 0.02/0.05 = paper grid
N_MC = 100_000
SEED = 2027


def sign_flip_mc(x: np.ndarray, rng: np.random.Generator) -> float:
    """One-sided p for mean < 0; identity included so the test is exact (Hemerik & Goeman)."""
    obs = x.mean()
    flips = rng.choice((-1.0, 1.0), size=(N_MC, x.size)) * np.abs(x)
    return float((1 + np.sum(flips.mean(axis=1) <= obs)) / (N_MC + 1))


def ci95(x: np.ndarray) -> list[float]:
    """Student-t 95% interval for the mean of held-out cell effects."""
    half = stats.t.ppf(0.975, x.size - 1) * x.std(ddof=1) / np.sqrt(x.size)
    return [float(x.mean() - half), float(x.mean() + half)]


def main() -> int:
    cells: dict[tuple[str, str], dict[int, float]] = defaultdict(dict)
    with SRC.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            b = int(r["requirement_batch"].replace("batch", ""))
            # loss = 1 - pass_rate/100; Z = loss(with) - loss(without) = (none - one)/100
            z = (float(r["none_pass_rate"]) - float(r["one_pass_rate"])) / 100.0
            cells[(r["harness_model"], r["skill"])][b] = z
    rng = np.random.default_rng(SEED)
    out: dict = {"source": str(SRC), "n_cells": len(cells), "screens": {}}
    for th in THETAS:
        for screen_half, held_half in (((1, 5), (6, 10)), ((6, 10), (1, 5))):
            sa = []
            for zs in cells.values():
                a = [zs[b] for b in range(screen_half[0], screen_half[1] + 1) if b in zs]
                h = [zs[b] for b in range(held_half[0], held_half[1] + 1) if b in zs]
                if not (a and h):
                    continue
                # theta = 0: helpful direction (mean < 0); theta > 0: plug-in rule mean <= -theta
                admit = np.mean(a) < 0 if th == 0 else np.mean(a) <= -th
                if admit:
                    sa.append((np.mean(a), np.mean(h)))
            key = f"theta={th}, screen on {screen_half}, held-out {held_half}"
            if not sa:
                out["screens"][key] = {"admitted": 0}
                continue
            scr = np.array([s for s, _ in sa])
            held = np.array([h for _, h in sa])
            t = stats.ttest_1samp(held, 0.0, alternative="less")
            out["screens"][key] = {
                "admitted": len(sa),
                "screen_mean": float(scr.mean()),
                "heldout_mean": float(held.mean()),
                "heldout_ci95": ci95(held),
                "heldout_t_p_one_sided": float(t.pvalue),
                "heldout_signflip_p_one_sided": sign_flip_mc(held, rng),
                "shrinkage_heldout_over_screen": float(held.mean() / scr.mean()),
            }
    allz = np.array([z for zs in cells.values() for z in zs.values()])
    out["overall_mean_Z"] = float(allz.mean())
    Path("results/sskb_screen_confirm.json").write_text(json.dumps(out, indent=1) + "\n")
    for k, v in out["screens"].items():
        if v.get("admitted"):
            lo, hi = v["heldout_ci95"]
            print(
                f"{k}: admitted {v['admitted']:3d}  screen {v['screen_mean']:+.3f} -> held-out "
                f"{v['heldout_mean']:+.3f} CI [{lo:+.3f}, {hi:+.3f}] "
                f"p_t {v['heldout_t_p_one_sided']:.3f} "
                f"p_flip {v['heldout_signflip_p_one_sided']:.3f}"
            )
    print("overall mean Z", round(out["overall_mean_Z"], 4))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
