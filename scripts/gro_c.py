"""Choose the bet cap c of the aGRAPA e-process by growth-rate optimality (GRO; Kelly 1956;
Grunwald, de Heide & Koolen, Safe Testing): the c maximising E[log E_n] under the alternative.
Validity (Ville) holds for every c in (0, 1); c only changes power, so trying several values on
SIMULATED data is legitimate. Inputs are measured/published: Z in {-1, 0, 1} with
P(Z=+1) = p_plus (0.04 / 0.08, pilot), STR in {-0.05, -0.109} (SWE-Skills-Bench), theta in {0,0.02}.
Candidates: Waudby-Smith & Ramdas' defaults (1/2, 3/4) and a grid around them.
Writes results/gro_c.json.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from gatekeeper.eprocess import BettingEProcess

CANDIDATES = [0.25, 0.5, 0.75, 0.9]
N = 600
REPS = 400


def growth(c: float, p_plus: float, str_true: float, theta: float, seed: int) -> float:
    rng = np.random.default_rng(seed)
    p_minus = p_plus - str_true
    logs = []
    for _ in range(REPS):
        z = rng.choice([1.0, -1.0, 0.0], size=N, p=[p_plus, p_minus, 1 - p_plus - p_minus])
        ep = BettingEProcess(theta=max(theta, 1e-9), alpha=0.05, c=c)
        for v in z:
            ep.update(float(v))
        logs.append(ep.log_e)
    return float(np.mean(logs)) / N


def main() -> int:
    out = []
    for pp in (0.04, 0.08):
        for st in (-0.05, -0.109):
            for th in (0.0, 0.02):
                row = {"p_plus": pp, "str": st, "theta": th, "growth_per_trial": {}}
                for c in CANDIDATES:
                    row["growth_per_trial"][str(c)] = growth(c, pp, st, th, seed=7)
                best = max(row["growth_per_trial"], key=row["growth_per_trial"].get)
                row["gro_c"] = float(best)
                out.append(row)
                print(
                    pp,
                    st,
                    th,
                    {k: round(v, 5) for k, v in row["growth_per_trial"].items()},
                    "best",
                    best,
                    flush=True,
                )
    Path("results/gro_c.json").write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
