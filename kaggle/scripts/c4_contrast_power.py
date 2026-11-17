"""Power of the C4' main test (note 40-5): end-of-pool test (lam 0.5, threshold 40) on the
environment contrast D_i = (Z_shipped - Z_single_commit) / 2, if a new agent behaved like the study
agent: tasks resampled with replacement from the study agent's seed-51 D_i (sections 33 and 35).
0 USD.

  python kaggle/scripts/c4_contrast_power.py --rows <dir with swesmith_pallets__jinja.jsonl> \
      --out kaggle/results/c4_contrast_power.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import s25_ab as ab  # noqa: E402

R = ROOT / "results"
LAM, THRESHOLD, REPS, SEED = 0.5, 40.0, 20000, 40050


def contrast(pre: str) -> dict[str, float]:
    def z(a: str, b: str) -> dict[str, float]:
        pairs = ab.paired(json.loads((R / a).read_text()), json.loads((R / b).read_text()))
        return {i: float(not ab.passed(x, "S")) - float(not ab.passed(y, "S")) for i, x, y in pairs}

    zs, zl = (
        z(f"{pre}_ship_skill.json", f"{pre}_ship_none.json"),
        z(f"{pre}_lf_skill.json", f"{pre}_lf_none.json"),
    )
    return {i: (zs[i] - zl[i]) / 2 for i in zs}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    rows = [json.loads(x) for x in (a.rows / "swesmith_pallets__jinja.jsonl").open() if x.strip()]
    empty = {r["instance_id"] for r in rows if not (r.get("problem_statement") or "").strip()}
    d33, d35 = contrast("s33"), contrast("s35")
    pools = {
        "100 test tasks": np.array(list(d33.values())),
        "no-description tasks (34 + 36)": np.array(
            [v for i, v in d33.items() if i in empty] + list(d35.values())
        ),
    }
    rng = np.random.default_rng(SEED)
    out: dict = {"lam": LAM, "threshold": THRESHOLD, "reps": REPS, "seed": SEED, "power": {}}
    for name, pool in pools.items():
        for n in (34, 70, 100, 136):
            x = rng.choice(pool, size=(REPS, n), replace=True)
            p = float((np.log1p(LAM * (-x)).sum(axis=1) >= np.log(THRESHOLD)).mean())
            out["power"][f"{name}, n={n}"] = p
    a.out.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out["power"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
