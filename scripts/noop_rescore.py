"""Section 27m-a: score a NO-OP patch (adds an unused one-line file) once per task with our harness.

  python scripts/noop_rescore.py --rows <e1_rows.jsonl> <live rows.jsonl> ... \
      --live-python <livenv python>

Tasks: all 20 T4 tasks (SWE-bench-Live) and 20 E1 tasks (SWE-bench test split, A111m) drawn with
random.Random(27).sample from the sorted union of E1 task sets (execution note 27m-1). A no-op
patch leaves every FAIL_TO_PASS test failing, so the expected resolved rate is 0. Writes
results/harness_noop.json after every task (resumable).
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gold_rescore import failures  # noqa: E402
from run_pilot import image_name, prepull  # noqa: E402

from gatekeeper.harness import read_report, run_harness  # noqa: E402

OUT = Path("results/harness_noop.json")
NOOP_PATCH = (
    "diff --git a/gk_noop.py b/gk_noop.py\n"
    "new file mode 100644\n"
    "--- /dev/null\n"
    "+++ b/gk_noop.py\n"
    "@@ -0,0 +1 @@\n"
    "+# no-op\n"
)
N_E1 = 20  # section 27m: 0/20 gives a Wilson 95% upper bound of 0.161
SEED = 27


def e1_tasks() -> list[str]:
    u = set()
    for s in (41, 51, 61):
        d = json.loads(Path(f"results/pilot/g1-e1all-s{s}.json").read_text())
        for sk in ("null-guard", "type-guard", "exception-handling"):
            u |= {p["instance_id"] for p in d["skills"][sk]["pairs"]}
    return random.Random(SEED).sample(sorted(u), N_E1)


def targets() -> list[str]:
    t4 = json.loads(Path("results/pilot/t4-s41.json").read_text())["instances"]
    return list(t4) + e1_tasks()


def drop_image(name: str) -> None:
    """Remove the image under BOTH names: prepull tags the mirror copy with its docker.io name, so
    removing one name alone frees no layers and the disk fills up (A92m)."""
    mirror = "mirror.gcr.io/" + name.removeprefix("docker.io/")
    subprocess.run(["docker", "rmi", "-f", name, mirror], capture_output=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", nargs="+", type=Path, required=True)
    ap.add_argument("--live-python", required=True)
    # SWE-bench (E1: full test split; G1 pilot: Verified) is scored with swebench 5.0.2 in the agent
    # env, as E1 was (A90 below; A111m: E1 is not Verified)
    ap.add_argument("--verified-python", required=True)
    # section 28m step 1 negative control: first N tasks, with network, separate output
    ap.add_argument("--net", action="store_true")
    # GitHub Actions shards (note 26m-2): this shard takes items k, k+of, k+2*of, ...
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--of", type=int, default=1)
    ap.add_argument("--first", type=int, default=0)
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    rows, src = {}, {}
    for f in a.rows:
        for line in f.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                rows.setdefault(r["instance_id"], r)
                src.setdefault(r["instance_id"], f)
    out = json.loads(a.out.read_text()) if a.out.exists() else {}
    work = Path("runs/noop-rescore")
    work.mkdir(parents=True, exist_ok=True)
    for iid in targets()[: a.first or None][a.shard :: a.of]:
        if iid in out:
            continue
        if iid not in rows:
            out[iid] = {"error": "row not found"}
            continue
        row = rows[iid]
        live = (row.get("image") or "").startswith(
            "starryzhang/"
        )  # Live; Verified: swebench/ (A93m)
        failed = prepull([row])
        if failed:
            out[iid] = {"error": f"image pull failed: {failed}"}
            a.out.write_text(json.dumps(out, indent=1) + "\n")
            continue
        preds = work / f"{iid}.json"
        preds.write_text(
            json.dumps(
                {iid: {"model_name_or_path": "noop", "instance_id": iid, "model_patch": NOOP_PATCH}}
            )
        )
        rid = f"noop{'net' if a.net else ''}-{iid}-{time.strftime('%Y%m%dT%H%M%S')}"
        kw = (
            {"namespace": "starryzhang", "python": a.live_python}
            if live
            else {"python": a.verified_python}
        )
        try:
            run_harness(str(preds), [iid], rid, 1, dataset=str(src[iid]), net=a.net, **kw)
        except SystemExit as exc:
            print(f"harness error {rid}: {exc}", flush=True)
        out[iid] = {"dataset": src[iid].name, "run_id": rid, **failures(read_report(rid, "", iid))}
        a.out.write_text(json.dumps(out, indent=1) + "\n")
        print(f"[noop] {iid}: resolved={out[iid].get('resolved')}", flush=True)
        drop_image(image_name(row))
    print("[noop] done", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
