"""Section 26: score the GOLD patch of each audit target 3 times with the same harness (0 USD).

  python scripts/gold_rescore.py --rows <e1_rows.jsonl> <live rows.jsonl> ... \
      --live-python <livenv python>

Targets: results/harness_gold_targets.json. One instance at a time: pull its image, score the gold
patch REPS times (fresh run id each time, so the harness never reuses a report), remove the image.
Label: "broken" if the gold patch is not resolved in all REPS runs, "flaky" if in 1..REPS-1,
"ok" if resolved every time. Also records which tests failed. Writes results/harness_gold.json
after every instance (resumable).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_pilot import image_name, prepull  # noqa: E402

from gatekeeper.harness import read_report, run_harness  # noqa: E402

REPS = 3  # section 26: operational, separates deterministic (3/3) from intermittent (1-2/3)
OUT = Path("results/harness_gold.json")


def failures(rep: dict | None) -> dict:
    if rep is None:
        return {"report": False}
    ts = rep.get("tests_status") or {}
    return {
        "report": True,
        "resolved": bool(rep.get("resolved")),
        "f2p_fail": sorted((ts.get("FAIL_TO_PASS") or {}).get("failure") or []),
        "p2p_fail": sorted((ts.get("PASS_TO_PASS") or {}).get("failure") or []),
    }


def label(runs: list[dict]) -> str:
    k = sum(1 for r in runs if r.get("resolved"))
    return "ok" if k == len(runs) else ("broken" if k == 0 else "flaky")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", nargs="+", type=Path, required=True)
    ap.add_argument("--live-python", required=True)
    a = ap.parse_args()
    rows, src = {}, {}
    for f in a.rows:
        for line in f.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                rows.setdefault(r["instance_id"], r)
                src.setdefault(r["instance_id"], f)
    targets = json.loads(Path("results/harness_gold_targets.json").read_text())
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    work = Path("runs/gold-rescore")
    work.mkdir(parents=True, exist_ok=True)
    for iid in targets:
        if iid in out:
            continue
        if iid not in rows:
            out[iid] = {"error": "row not found"}
            continue
        row = rows[iid]
        live = bool(row.get("image"))  # SWE-bench-Live rows carry their image name
        failed = prepull([row])
        if failed:
            out[iid] = {"error": f"image pull failed: {failed}"}
            OUT.write_text(json.dumps(out, indent=1) + "\n")
            continue
        preds = work / f"{iid}.json"
        preds.write_text(
            json.dumps(
                {
                    iid: {
                        "model_name_or_path": "gold",
                        "instance_id": iid,
                        "model_patch": row["patch"],
                    }
                }
            )
        )
        runs = []
        for k in range(REPS):
            rid = f"gold-{iid}-{time.strftime('%Y%m%dT%H%M%S')}-r{k}"
            kw = {"namespace": "starryzhang", "python": a.live_python} if live else {}
            try:
                run_harness(str(preds), [iid], rid, 1, dataset=str(src[iid]), **kw)
            except SystemExit as exc:
                print(f"harness error {rid}: {exc}", flush=True)
            runs.append({"run_id": rid, **failures(read_report(rid, "gold", iid))})
        out[iid] = {"dataset": src[iid].name, "runs": runs, "label": label(runs)}
        OUT.write_text(json.dumps(out, indent=1) + "\n")
        print(f"[gold] {iid}: {out[iid]['label']}", flush=True)
        subprocess.run(["docker", "rmi", "-f", image_name(row)], capture_output=True)
    print("[gold] done", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
