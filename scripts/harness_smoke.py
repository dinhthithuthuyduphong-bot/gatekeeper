"""End-to-end paired trial through the official SWE-bench harness, without any LLM (free).

For each task: run the gold patch ("perfect skill") and an empty patch ("no skill") through
`swebench.harness.run_evaluation`, turn the per-test outcomes into the normalised loss
(gatekeeper.loss) and the paired difference Z = loss_with - loss_without.

Expected: gold resolves every task (loss 0); the empty patch fixes no FAIL_TO_PASS test and
breaks nothing (F = 1, R = 0, loss = 1/(1 + w) = 0.667 for w = 0.5), so Z = -0.667.
This validates TODO.md Phase 0 'SWE-bench harness ... 5/5 pass' and the loss pipeline.

Usage (needs Docker): python scripts/harness_smoke.py [--ids a,b,c] [--workers 2]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from gatekeeper.loss import functional_loss

# swebench>=5 needs the SWE-bench org copy (it carries image, eval_script, log_parser)
DATASET = "SWE-bench/SWE-bench_Verified"
DEFAULT_IDS = [
    "psf__requests-1142",
    "psf__requests-2931",
    "pallets__flask-5014",
    "pydata__xarray-3677",
    "pylint-dev__pylint-6386",
]


def run_harness(preds: str, ids: list[str], run_id: str, workers: int) -> None:
    cmd = [
        sys.executable,
        "-m",
        "swebench.harness.run_evaluation",
        "--dataset_name",
        DATASET,
        "--split",
        "test",
        "--predictions_path",
        preds,
        "--instance_ids",
        *ids,
        "--max_workers",
        str(workers),
        "--run_id",
        run_id,
        "--timeout",
        "1800",
    ]
    print("+", " ".join(cmd), flush=True)
    rc = subprocess.run(cmd, check=False).returncode
    if rc != 0:
        raise SystemExit(f"swebench harness exited with code {rc} for run {run_id}")


def read_report(run_id: str, model: str, iid: str) -> dict | None:
    p = Path("logs/run_evaluation") / run_id / model / iid / "report.json"
    if not p.exists():  # layout differs across harness versions: search the run directory
        hits = sorted((Path("logs/run_evaluation") / run_id).glob(f"**/{iid}/report.json"))
        if not hits:
            return None
        p = hits[0]
    return json.loads(p.read_text())[iid]


def loss_of(rep: dict | None, w: float = 0.5) -> tuple[float, dict]:
    """No report (e.g. empty patch skipped by the harness) = nothing fixed, nothing broken."""
    if rep is None:
        return functional_loss(1.0, 0.0, w), {"resolved": False, "note": "no report"}
    ts = rep.get("tests_status", {})
    f2p, p2p = ts.get("FAIL_TO_PASS", {}), ts.get("PASS_TO_PASS", {})
    n_f = len(f2p.get("success", [])) + len(f2p.get("failure", []))
    n_p = len(p2p.get("success", [])) + len(p2p.get("failure", []))
    F = len(f2p.get("failure", [])) / n_f if n_f else 1.0
    R = len(p2p.get("failure", [])) / n_p if n_p else 0.0
    return functional_loss(F, R, w), {
        "resolved": bool(rep.get("resolved")),
        "F": F,
        "R": R,
        "n_fail_to_pass": n_f,
        "n_pass_to_pass": n_p,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", default=",".join(DEFAULT_IDS))
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    ids = [i for i in a.ids.split(",") if i]

    empty = Path("preds_empty.jsonl")
    empty.write_text(
        "".join(
            json.dumps({"instance_id": i, "model_name_or_path": "empty", "model_patch": ""}) + "\n"
            for i in ids
        )
    )
    run_harness("gold", ids, "smoke-gold", a.workers)
    run_harness(str(empty), ids, "smoke-empty", a.workers)

    rows = []
    for i in ids:
        lw, dw = loss_of(read_report("smoke-gold", "gold", i))
        lo, do = loss_of(read_report("smoke-empty", "empty", i))
        rows.append(
            {
                "instance_id": i,
                "loss_with": lw,
                "loss_without": lo,
                "Z": lw - lo,
                "gold": dw,
                "empty": do,
            }
        )
        print(f"{i:<28} gold={lw:.3f} empty={lo:.3f} Z={lw - lo:+.3f} resolved={dw['resolved']}")
    out = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dataset": DATASET,
        "rows": rows,
        "gold_resolved": sum(r["gold"]["resolved"] for r in rows),
        "n": len(rows),
    }
    Path("results").mkdir(exist_ok=True)
    Path("results/harness_smoke.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in ("gold_resolved", "n")}))
    return 0 if out["gold_resolved"] == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
