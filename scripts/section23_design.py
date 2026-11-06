"""Design numbers for section 23 (docs/preregistration_main.md), computed BEFORE any paid run. Free.

  python scripts/section23_design.py

(a) Probe on a second model (gemini-flash), skills viper-configuration and asyncio-patterns,
    k batches each (k is set by the 2 USD cap, unknown before the run). Rule of section 22:
    go on if G = (D_viper - D_asyncio) / 2 >= 0.10. For k = 3..10, P(go) when the effect is as
    published (k batch differences drawn with replacement from SSKB's 40 public differences of the
    skill: 4 configurations x 10 batches) and when there is no effect (same draws, random signs).
(b) Screen-then-confirm on gemini-flash-lite (data splitting, Cox 1975). Screen: 5 skills x 10
    batches x seed 41; select the skill with the largest |D|. Confirm: fresh seeds 51 and 61 on the
    selected skill; 10 batch-level differences (mean of 2 seeds); exact one-sided sign-flip test in
    the screened direction over all 2^10 sign patterns, identity included (Hemerik & Goeman 2018),
    alpha 0.05. True effects delta_i ~ N(0, tau^2), tau in {3, 5, 7} pp: 7 pp is the upper bound
    sqrt(49.7) (variance of per-configuration skill effects in SSKB, which includes their noise;
    results/sskb_transfer_power.json lists the components). Screening noise sd 9.35 pp (section 22,
    20 differences, 10-batch mean). Batch-level confirmation noise sd between 29.6/sqrt(2) (all
    noise between seeds) and 29.6 (all noise between requirements).
Writes results/section23_design.json.
"""

from __future__ import annotations

import csv
import itertools
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

SRC = Path("data/external/swe-skills-bench/ALL_combined_cells.csv")
N_SIM = 20_000
SEED = 2023
SD_REQ = 29.565  # pp, section 22 per-requirement difference sd (results/sskb_transfer_power.json)
SCREEN_SD = SD_REQ / np.sqrt(10)


def public_diffs(skill: str) -> np.ndarray:
    d = defaultdict(list)
    with SRC.open() as f:
        for r in csv.DictReader(f):
            d[r["skill"]].append(float(r["delta_pp"]) / 100)
    return np.array(d[skill])


def part_a(rng: np.random.Generator) -> dict:
    v, a = public_diffs("viper-configuration"), public_diffs("asyncio-patterns")
    assert v.size == 40 and a.size == 40
    out = {}
    for k in range(3, 11):
        dv = rng.choice(v, size=(N_SIM, k)).mean(1)
        da = rng.choice(a, size=(N_SIM, k)).mean(1)
        g_pub = (dv - da) / 2
        sv = rng.choice((-1, 1), size=(N_SIM, k)) * rng.choice(v, size=(N_SIM, k))
        sa = rng.choice((-1, 1), size=(N_SIM, k)) * rng.choice(a, size=(N_SIM, k))
        g_null = (sv.mean(1) - sa.mean(1)) / 2
        out[str(k)] = {
            "p_go_published": float((g_pub >= 0.10).mean()),
            "p_go_null": float((g_null >= 0.10).mean()),
        }
    return out


SIGNS = np.array(list(itertools.product((-1.0, 1.0), repeat=10)))  # 1024 x 10, includes identity


def exact_p_one_sided(x: np.ndarray) -> np.ndarray:
    """x: n_sim x 10 differences oriented so that the alternative is mean > 0."""
    out = np.empty(x.shape[0])
    for i in range(0, x.shape[0], 1000):  # chunks keep memory small
        c = x[i : i + 1000]
        perm = (np.abs(c)[:, None, :] * SIGNS[None, :, :]).mean(2)  # chunk x 1024
        out[i : i + 1000] = (perm >= c.mean(1)[:, None] - 1e-12).mean(1)
    return out


def part_b(rng: np.random.Generator) -> dict:
    out = {}
    for tau in (3.0, 5.0, 7.0):
        for label, sd_b in (("seed_noise", SD_REQ / np.sqrt(2)), ("requirement_noise", SD_REQ)):
            delta = rng.normal(0, tau, size=(N_SIM, 5))
            screen = delta + rng.normal(0, SCREEN_SD, size=(N_SIM, 5))
            pick = np.abs(screen).argmax(1)
            d_sel = delta[np.arange(N_SIM), pick]
            sign = np.sign(screen[np.arange(N_SIM), pick])
            conf = d_sel[:, None] + rng.normal(0, sd_b, size=(N_SIM, 10))
            p = exact_p_one_sided(conf * sign[:, None])
            out[f"tau{tau:g}_{label}"] = {
                "p_confirm": float((p <= 0.05).mean()),
                "p_confirm_true_direction": float(((p <= 0.05) & (sign * d_sel > 0)).mean()),
            }
    # level check: no effect at all
    conf = rng.normal(0, SD_REQ, size=(N_SIM, 10))
    out["null_level"] = float((exact_p_one_sided(conf) <= 0.05).mean())
    return out


def part_c_dm11(rng: np.random.Generator) -> dict:
    """D-M11 (gemini-flash, 7 USD): screen 5 skills x 6 batches x 1 seed; confirm the selected
    skill on 10 batches x 1 fresh seed (batch-level noise sd 29.6 pp). Noise of Flash-Lite is used
    because Flash has not been measured. Also P(go) of the section 22 rule at k = 2 (Pro, 3 USD)."""
    out = {}
    for tau in (3.0, 5.0, 7.0):
        delta = rng.normal(0, tau, size=(N_SIM, 5))
        screen = delta + rng.normal(0, SD_REQ / np.sqrt(6), size=(N_SIM, 5))
        pick = np.abs(screen).argmax(1)
        d_sel = delta[np.arange(N_SIM), pick]
        sign = np.sign(screen[np.arange(N_SIM), pick])
        conf = d_sel[:, None] + rng.normal(0, SD_REQ, size=(N_SIM, 10))
        p = exact_p_one_sided(conf * sign[:, None])
        out[f"tau{tau:g}"] = float(((p <= 0.05) & (sign * d_sel > 0)).mean())
    v, a = public_diffs("viper-configuration"), public_diffs("asyncio-patterns")
    g_pub = (rng.choice(v, size=(N_SIM, 2)).mean(1) - rng.choice(a, size=(N_SIM, 2)).mean(1)) / 2
    sv = rng.choice((-1, 1), size=(N_SIM, 2)) * rng.choice(v, size=(N_SIM, 2))
    sa = rng.choice((-1, 1), size=(N_SIM, 2)) * rng.choice(a, size=(N_SIM, 2))
    out["a_k2"] = {
        "p_go_published": float(((g_pub) >= 0.10).mean()),
        "p_go_null": float(((sv.mean(1) - sa.mean(1)) / 2 >= 0.10).mean()),
    }
    return out


def main() -> int:
    rng = np.random.default_rng(SEED)
    res = {
        "a_flash_probe": part_a(rng),
        "b_screen_confirm": part_b(rng),
        "c_dm11": part_c_dm11(rng),
        "n_sim": N_SIM,
    }
    Path("results/section23_design.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
