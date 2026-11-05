"""Harm-at-matched-coverage curves (docs/preregistration_main.md section 16). 0 USD.
Writes results/harm_coverage.json.

  python scripts/harm_coverage.py --xrepo <XRepoSkill clone at 26fd703> --reps 1000
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import gates  # noqa: E402
import lifecycle_plasmode as lp  # noqa: E402
import plasmode_real as pr  # noqa: E402

from gatekeeper.analysis import harm_at_coverage  # noqa: E402
from gatekeeper.eprocess import BettingEProcess  # noqa: E402

SEED = 20271110
N, LOOK = 200, 10
GK_ALPHAS = [1e-12, 1e-10, 1e-8, 1e-6, 1e-4, 3e-4, 1e-3, 3e-3, 0.01, 0.03, 0.1, 0.3]
BX2_C = [0.0, 0.5, 1.0, 1.5, 1.959964, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 7.0]
PLUG_T = [0.0, 0.02, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5, 0.6]
TARGETS = [0.5, 0.7, 0.8]


def log_e_path(z: list[float]) -> list[float]:
    """log E_t of the Gatekeeper e-process (alpha only sets the crossing flag, not the path)."""
    ep = BettingEProcess(theta=0.0, alpha=0.5)
    out = []
    for v in z:
        ep.update(v)
        out.append(ep.log_e)
    return out


def bx2_stat(pairs, score) -> tuple[float, float] | None:
    strata = [score.Stratum(s, a=int(w), n1=1, c=int(o), n0=1) for w, o, s in pairs]
    return score.mh_risk_difference(strata)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xrepo", type=Path, required=True)
    ap.add_argument("--reps", type=int, required=True)
    a = ap.parse_args()
    score = gates.load_xreposkill_score(a.xrepo)
    tasks = pr.no_skill_runs()
    base = float(np.mean([np.mean(t) for t in tasks]))
    rng = np.random.default_rng(SEED)
    deltas = pr.DELTAS
    bad = [c for c, d in enumerate(deltas) if d <= 0]
    good = [c for c, d in enumerate(deltas) if d > 0]
    looks = list(range(LOOK, N + 1, LOOK))
    # counts[rule][mode][threshold index] = (#admitted bad, #admitted good)
    keys = {"gatekeeper": GK_ALPHAS, "b_x2": BX2_C, "plug_in": PLUG_T, "e_bh": GK_ALPHAS}
    cnt = {r: {m: np.zeros((len(v), 2)) for m in ("once", "monitored")} for r, v in keys.items()}
    for _ in range(a.reps):
        cells = [pr.make_cell(rng, tasks, N, d, base, None) for d in deltas]
        finals = []
        for c, (z, prs) in enumerate(cells):
            col = 0 if c in bad else 1 if c in good else None
            le = log_e_path(z)
            finals.append(math.exp(le[-1]))
            mx = max(le)
            st_once = bx2_stat(prs, score)
            st_look = [bx2_stat(prs[:t], score) for t in looks]
            zbar_once = float(np.mean(z))
            zbar_look = [float(np.mean(z[:t])) for t in looks]
            for i, al in enumerate(GK_ALPHAS):
                cnt["gatekeeper"]["once"][i, col] += le[-1] >= math.log(1 / al)
                cnt["gatekeeper"]["monitored"][i, col] += mx >= math.log(1 / al)
            for i, cc in enumerate(BX2_C):
                ok = lambda s, cc=cc: s is not None and s[1] > 0 and s[0] - cc * s[1] > 0  # noqa: E731
                cnt["b_x2"]["once"][i, col] += ok(st_once)
                cnt["b_x2"]["monitored"][i, col] += any(ok(s) for s in st_look)
            for i, tt in enumerate(PLUG_T):
                cnt["plug_in"]["once"][i, col] += zbar_once < -tt
                cnt["plug_in"]["monitored"][i, col] += any(m < -tt for m in zbar_look)
        for i, al in enumerate(GK_ALPHAS):
            rej = lp.e_bh(finals, al)
            for c in range(len(deltas)):
                if rej[c]:
                    cnt["e_bh"]["once"][i, 0 if c in bad else 1] += 1
    out = {"reps": a.reps, "n": N, "curves": {}, "harm_at_coverage": {}}
    for r, v in keys.items():
        for m in ("once", "monitored"):
            if r == "e_bh" and m == "monitored":
                continue
            curve = [
                (
                    float(th),
                    cnt[r][m][i, 1] / (a.reps * len(good)),
                    cnt[r][m][i, 0] / (a.reps * len(bad)),
                )
                for i, th in enumerate(v)
            ]
            out["curves"][f"{r}/{m}"] = curve
            covs = [c[1] for c in curve]
            out["harm_at_coverage"][f"{r}/{m}"] = {
                str(t): (harm_at_coverage(curve, t) if min(covs) <= t <= max(covs) else None)
                for t in TARGETS
            }
    Path("results/harm_coverage.json").write_text(json.dumps(out, indent=1) + "\n")
    for k, v in out["harm_at_coverage"].items():
        print(k, v)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
