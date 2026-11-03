"""Uncertainty of the plasmode power that comes from its INPUT: the per-task no-skill solve rates
q were measured on only 32 G1 tasks. Bootstrap the 32 tasks (60 resamples), simulate each design
300 times per resample with the same functions as scripts/verify_methods.py, and report the median
and the 5%-95% range of power. Writes results/power_input_uncertainty.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import verify_methods as vm  # noqa: E402

B, R = 60, 300  # operational: MCSE of one power value <= 0.03 (sqrt(0.25/300)); see method_check


def main() -> int:
    q = vm.measured_q()
    rng = np.random.default_rng(7)
    e2 = json.loads(Path("configs/pools/e2_selected.json").read_text())["instances"]
    s1 = json.loads(Path("configs/pools/e1_task_sets.json").read_text())
    sx = json.loads(Path("configs/pools/e1x_task_sets.json").read_text())
    cases = {
        "E2 n=121": (121, vm.clusters_of(e2), vm.ALPHA),
        "E1 n=53": (53, vm.clusters_of(s1["null-guard"] + sx["null-guard"]), vm.ALPHA / 3),
    }
    out: dict = {
        "q": {
            "n": int(q.size),
            "mean": float(q.mean()),
            "share_q1": float((q == 1).mean()),
            "share_q0": float((q == 0).mean()),
        }
    }
    for name, (n, sizes, lev) in cases.items():
        for d in (0.109, 0.20):
            pw = []
            for _ in range(B):
                qb = rng.choice(q, size=q.size, replace=True)
                hit = sum(
                    vm.decide(vm.simulate(rng, qb, n, sizes, d)[0], lev)["primary"]
                    for _ in range(R)
                )
                pw.append(hit / R)
            pw = np.array(pw)
            out[f"{name} delta={d}"] = {
                "median": float(np.median(pw)),
                "q05": float(np.quantile(pw, 0.05)),
                "q95": float(np.quantile(pw, 0.95)),
            }
            print(name, d, out[f"{name} delta={d}"], flush=True)
    Path("results/power_input_uncertainty.json").write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
