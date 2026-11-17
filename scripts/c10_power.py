"""Power and size of the C10 main test before registration (docs/preregistration_main.md section 43;
0 USD).

  python scripts/c10_power.py --rows <dir with swesmith_pallets__jinja.jsonl> \
      --out results/c10_power.json

Main test: end-of-pool test (lam 0.5, theta 0, reject when E >= 40) on
D_i = (Z_i^A - Z_i^C) / 2, Z = 1[skill fails] - 1[no skill fails], over the no-description tasks.
Scenarios (tasks resampled with replacement from the study agent's seed-51 runs, sections 33/35):
  leak   : C behaves like the single-commit environment (D_i = observed (Z_ship - Z_single)/2)
  half   : C keeps half of the gain (each observed D_i = -0.5 is set to 0 with probability 1/2)
  null   : C behaves like A (A and C drawn independently from the same pooled solve rates)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s25_ab as ab  # noqa: E402

R = Path(__file__).resolve().parents[1] / "results"
LAM, THRESHOLD, REPS, SEED = 0.5, 40.0, 20000, 4301


def zmap(a: str, b: str) -> dict[str, float]:
    pairs = ab.paired(json.loads((R / a).read_text()), json.loads((R / b).read_text()))
    return {i: float(not ab.passed(x, "S")) - float(not ab.passed(y, "S")) for i, x, y in pairs}


def solved(f: str, ids: set[str]) -> list[int]:
    return [
        int(ab.passed(r, "S"))
        for r in json.loads((R / f).read_text())["runs"]
        if r["instance_id"] in ids
    ]


def reject(d: np.ndarray) -> float:
    return float((np.log1p(LAM * (-d)).sum(axis=1) >= np.log(THRESHOLD)).mean())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    rows = [json.loads(x) for x in (a.rows / "swesmith_pallets__jinja.jsonl").open() if x.strip()]
    empty = {r["instance_id"] for r in rows if not (r.get("problem_statement") or "").strip()}
    pools = {}
    for pre, keep in (("s33", empty), ("s35", None)):
        zs, zl = (
            zmap(f"{pre}_ship_skill.json", f"{pre}_ship_none.json"),
            zmap(f"{pre}_lf_skill.json", f"{pre}_lf_none.json"),
        )
        pools[pre] = np.array([(zs[i] - zl[i]) / 2 for i in zs if keep is None or i in keep])
    pools["all70"] = np.concatenate([pools["s33"], pools["s35"]])
    ids35 = {r["instance_id"] for r in json.loads((R / "s35_ship_skill.json").read_text())["runs"]}
    ids = (
        empty
        & {r["instance_id"] for r in json.loads((R / "s33_ship_skill.json").read_text())["runs"]}
    ) | ids35
    p_skill = np.mean(solved("s33_ship_skill.json", ids) + solved("s35_ship_skill.json", ids))
    p_none = np.mean(solved("s33_ship_none.json", ids) + solved("s35_ship_none.json", ids))
    rng = np.random.default_rng(SEED)
    out: dict = {
        "lam": LAM,
        "threshold": THRESHOLD,
        "reps": REPS,
        "seed": SEED,
        "observed": {
            k: {
                "n": int(v.size),
                "n_negative": int((v < 0).sum()),
                "n_positive": int((v > 0).sum()),
            }
            for k, v in pools.items()
        },
        "pooled_solve_rate_shipped": {"skill": float(p_skill), "none": float(p_none)},
        "rejection_rate": {},
    }
    for n, src in ((34, pools["s33"]), (70, pools["all70"])):
        x = rng.choice(src, size=(REPS, n), replace=True)
        out["rejection_rate"][f"leak, n={n}"] = reject(x)
        h = np.where((x < 0) & (rng.random(x.shape) < 0.5), 0.0, x)
        out["rejection_rate"][f"half, n={n}"] = reject(h)

        def z(shape):
            return (rng.random(shape) >= p_skill).astype(float) - (rng.random(shape) >= p_none)

        out["rejection_rate"][f"null, n={n}"] = reject((z((REPS, n)) - z((REPS, n))) / 2)
    a.out.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
