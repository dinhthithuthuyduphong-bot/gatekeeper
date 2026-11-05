"""T4 decision (docs/preregistration_main.md section 14, D-M6): Gatekeeper, K = 1, alpha 0.025,
on the T4 pairs in the fixed task order. Prints ADMIT/CONTINUE and writes results/t4_decision.json.

  python scripts/t4_check.py --name t4-s41 --pool t4_pool.json
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import analyze_g1_final as gf  # noqa: E402

from gatekeeper.eprocess import run_admission  # noqa: E402

ALPHA = 0.025  # section 14 T4: K = 1, one-sided (ICH E9)
SKILL = "control-oracle-patch"


def trials(name: str, order: list[str]) -> list[float]:
    z: dict[str, float] = {}
    for f in sorted(glob.glob(f"results/pilot/{name}-p[0-9][0-9].json")):
        pairs = json.loads(Path(f).read_text())["skills"].get(SKILL, {}).get("pairs", [])
        z.update(gf.z_resolved(pairs))
    return [z[i] for i in order if i in z]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--pool", type=Path, required=True)
    a = ap.parse_args()
    order = json.loads(a.pool.read_text())["instances"]
    z = trials(a.name, order)
    r = run_admission(z, 0.0, ALPHA, budget=len(z))
    out = {
        "n_trials": len(z),
        "admitted": r.admitted,
        "admitted_at": r.n_trials if r.admitted else None,
        "log_e": r.log_e,
        "mean_resolved_gain": -sum(z) / len(z) if z else None,
    }
    Path("results/t4_decision.json").write_text(json.dumps(out, indent=1) + "\n")
    print(("ADMIT " if r.admitted else "CONTINUE ") + json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
