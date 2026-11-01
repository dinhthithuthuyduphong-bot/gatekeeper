"""End-to-end paired trial through the official SWE-bench harness, without any LLM (free).

For each task: run the gold patch ("perfect skill") and a no-op patch ("no skill") through
`swebench.harness.run_evaluation`, turn the per-test outcomes into the normalised loss
(gatekeeper.loss) and the paired difference Z = loss_with - loss_without.

Expected: gold resolves every task (loss 0); the no-op patch fixes no FAIL_TO_PASS test and
breaks nothing (F = 1, R = 0, loss = 1/(1 + w) = 0.667 for w = 0.5), so Z = -0.667. Unlike an
empty patch (which the harness skips), the no-op patch is evaluated: F and R are measured.
This validates TODO.md Phase 0 'SWE-bench harness ... 5/5 pass' and the loss pipeline.

Usage (needs Docker): python scripts/harness_smoke.py [--ids a,b,c] [--workers 2]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from gatekeeper.harness import DATASET, NOOP_PATCH, loss_of, read_report, run_harness

__all__ = ["DATASET", "NOOP_PATCH", "loss_of", "read_report", "run_harness"]

DEFAULT_IDS = [
    "psf__requests-1142",
    "psf__requests-2931",
    "pallets__flask-5014",
    "pydata__xarray-3677",
    "pylint-dev__pylint-6386",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", default=",".join(DEFAULT_IDS))
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    ids = [i for i in a.ids.split(",") if i]

    noop = Path("preds_noop.jsonl")
    noop.write_text(
        "".join(
            json.dumps({"instance_id": i, "model_name_or_path": "noop", "model_patch": NOOP_PATCH})
            + "\n"
            for i in ids
        )
    )
    run_harness("gold", ids, "smoke-gold", a.workers)
    run_harness(str(noop), ids, "smoke-noop", a.workers)

    rows = []
    for i in ids:
        lw, dw = loss_of(read_report("smoke-gold", "gold", i))
        lo, do = loss_of(read_report("smoke-noop", "noop", i))
        rows.append(
            {
                "instance_id": i,
                "loss_with": lw,
                "loss_without": lo,
                "Z": lw - lo,
                "gold": dw,
                "noop": do,
            }
        )
        print(f"{i:<28} gold={lw:.3f} noop={lo:.3f} Z={lw - lo:+.3f} resolved={dw['resolved']}")
    out = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dataset": DATASET,
        "rows": rows,
        "no_skill_arm_measured": all(r["noop"].get("note") != "no report" for r in rows),
        "gold_resolved": sum(r["gold"]["resolved"] for r in rows),
        "n": len(rows),
    }
    Path("results").mkdir(exist_ok=True)
    Path("results/harness_smoke.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in ("gold_resolved", "n")}))
    return 0 if out["gold_resolved"] == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
