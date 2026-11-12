"""Section 35 analysis (docs/preregistration_main.md, registered before any section 33 or 35
result was opened). 0 USD.

  python scripts/s35_analysis.py --rows <swesmith_pallets__jinja.jsonl>

P35 (one test, alpha 0.025): the environment-contrast e-process of section 32c on the 70 tasks
without a problem statement, in the registered order: the 34 test tasks of section 33 (seed 51) in
gskill's order, then the 36 unused tasks of section 35 in dataset order. Rejects when E >= 40.
Descriptive: resolved counts on the 36 new tasks, monitor flag M2 as shipped, the e-process on the
36 new tasks alone, the share of 10,000 orders that reject. Writes results/s35_analysis.json.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import s25_ab as ab  # noqa: E402
from s32_analysis import flags  # noqa: E402
from s33_analysis import OK, eproc, z_of  # noqa: E402

R = Path("results")
ORDERS, SEED = 10000, 3501
ARMS = ("ship_none", "ship_skill", "lf_none", "lf_skill")


def load(name: str) -> dict:
    return json.loads((R / name).read_text())


def contrast(pre: str, keep) -> list[float]:
    """D_i in the order of the skill arm's `order` field, for the tasks `keep` accepts."""
    order, zs = z_of(load(f"{pre}_ship_skill.json"), load(f"{pre}_ship_none.json"))
    _, zl = z_of(load(f"{pre}_lf_skill.json"), load(f"{pre}_lf_none.json"))
    return [(zs[i] - zl[i]) / 2 for i in order if i in zl and keep(i)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True, help="gskill's jinja sample (problem statements)")
    ap.add_argument("--orders", type=int, default=ORDERS)
    a = ap.parse_args()
    op = gzip.open if a.rows.endswith(".gz") else open
    empty = {
        r["instance_id"]
        for r in (json.loads(x) for x in op(a.rows, "rt") if x.strip())
        if not (r.get("problem_statement") or "").strip()
    }
    d_test = contrast("s33", lambda i: i in empty)
    d_new = contrast("s35", lambda i: True)
    d = d_test + d_new
    main_ = eproc(d)
    rng = np.random.default_rng(SEED)
    share = float(
        np.mean(
            [
                eproc([d[j] for j in rng.permutation(len(d))])["first_crossing_at_40"] is not None
                for _ in range(a.orders)
            ]
        )
    )
    arms = {k: load(f"s35_{k}.json") for k in ARMS}
    runs = [r for v in arms.values() for r in v["runs"]]
    lf = [r.get("leak_free_check") for k in ("lf_none", "lf_skill") for r in arms[k]["runs"]]
    m2 = {}
    for k in ("ship_none", "ship_skill"):
        recs = [json.loads(x) for x in gzip.open(R / f"s35_{k}.traces.jsonl.gz", "rt")]
        m2[k] = f"{sum(flags(r['messages'])[1] for r in recs if r.get('messages'))}/{len(recs)}"
    out = {
        "checks": {
            "n": {k: len(v["runs"]) for k, v in arms.items()},
            "infra_error": sum("infra_error" in r for r in runs),
            "crashed": sum(bool(r.get("crashed")) for r in runs),
            "capped": sum(r.get("cost_usd", 0) >= 0.30 for r in runs),
            "leak_free_checks_ok": f"{sum(x == OK for x in lf)}/{len(lf)}",
            "stopped": {k: v.get("stopped") for k, v in arms.items() if v.get("stopped")},
            "spent_usd": sum(v["spent_usd"] for v in arms.values()),
        },
        "P35": {
            **main_,
            "reject": main_["first_crossing_at_40"] is not None,
            "n": len(d),
            "n_test_seed51": len(d_test),
            "n_new": len(d_new),
            "mean_D": float(np.mean(d)),
            "tasks_with_D_below_0": int(sum(x < 0 for x in d)),
            "tasks_with_D_above_0": int(sum(x > 0 for x in d)),
            "share_of_orders_rejecting": share,
        },
        "new_tasks_only": {**eproc(d_new), "mean_D": float(np.mean(d_new))},
        "resolved_on_new_tasks": {
            k: sum(bool(ab.passed(r, "S")) for r in v["runs"]) for k, v in arms.items()
        },
        "monitor_M2_as_shipped": m2,
    }
    (R / "s35_analysis.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
