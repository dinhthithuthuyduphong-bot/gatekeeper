"""Section 37, stage 0: can SWE-smith's grading run without a Docker daemon, with the same grades?

K0a  environment: is there a Docker daemon; does udocker unpack and run the task image.
K0b  equivalence: every non-empty stored patch of the given result files is graded once by
     SWE-smith's own run_evaluation through scripts/udocker_shim.py and compared with the grade
     on record (obtained under Docker); for the first --controls tasks, also the gold patch (must
     resolve) and no patch at all (must not resolve).
Appends one JSON line per grading to --out (an interrupted run resumes); prints a summary.

  python kaggle/scripts/k0_stage0.py --rows swesmith_pallets__jinja.jsonl \
      --results f1_probe.json f1_skill_probe.json --controls 20 --out k0b_jinja.jsonl
Run from a scratch directory (SWE-smith writes logs under ./logs/run_evaluation).
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))  # udocker_shim (kaggle/scripts)
sys.path.insert(1, str(_HERE.parents[1] / "scripts"))  # f0_scorer_check (repository scripts)


def probe() -> dict:
    def sh(cmd: str) -> tuple[int, str]:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return r.returncode, (r.stdout + r.stderr).strip()[-300:]

    du = shutil.disk_usage(".")
    return {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "docker_binary": shutil.which("docker"),
        "docker_daemon": sh("docker info")[0] == 0,
        "udocker_cmd": " ".join(__import__("udocker_shim").UDOCKER[:1]),
        "disk_free_gb": round(du.free / 2**30, 1),
        "cpus": __import__("os").cpu_count(),
        "udocker_execmode": __import__("os").environ.get("UDOCKER_EXECMODE", "default (P1)"),
    }


def grade(inst: dict, patch: str, is_gold: bool) -> dict:
    from swesmith.harness.eval import run_evaluation

    pred = {"instance_id": inst["instance_id"], "model_patch": patch, "model_name_or_path": "k0"}
    t = time.time()
    try:
        r = run_evaluation(
            pred, dict(inst), run_id=f"k0_{uuid.uuid4().hex[:8]}", f2p_only=False, is_gold=is_gold
        )
        out = {"resolved": bool(r["resolved"]), "status": r["status"]}
    except Exception as e:  # noqa: BLE001 - infrastructure, recorded and never counted as a grade
        out = {"resolved": None, "status": f"error: {type(e).__name__}: {str(e)[:160]}"}
    return {**out, "seconds": round(time.time() - t, 1)}


def summarise(out: Path) -> dict:
    rows = [json.loads(x) for x in out.read_text().splitlines() if x.strip()]
    done = [r for r in rows if r["status"] == "completed"]
    pat = [r for r in done if r["kind"] == "patch"]
    gold = [r for r in done if r["kind"] == "gold"]
    noop = [r for r in done if r["kind"] == "noop"]
    dis = [r for r in pat if r["resolved"] != r["recorded"]]
    return {
        "gradings": len(rows),
        "not_completed": len(rows) - len(done),
        "patches": len(pat),
        "patches_agree": len(pat) - len(dis),
        "disagreements": [(r["file"], r["instance_id"], r["recorded"], r["resolved"]) for r in dis],
        "recorded_resolved": sum(r["recorded"] for r in pat),
        "gold": len(gold),
        "gold_resolved": sum(r["resolved"] for r in gold),
        "noop": len(noop),
        "noop_resolved": sum(r["resolved"] for r in noop),
        "median_seconds": sorted(r["seconds"] for r in done)[len(done) // 2] if done else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True, type=Path)
    ap.add_argument("--results", nargs="+", required=True, type=Path)
    ap.add_argument("--controls", required=True, type=int)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--summary-only", action="store_true")
    a = ap.parse_args()
    if a.summary_only:
        print(json.dumps(summarise(a.out), indent=1))
        return 0
    print(json.dumps({"K0a": probe()}, indent=1), flush=True)
    import udocker_shim
    from f0_scorer_check import assume_public

    udocker_shim.install()
    rows = {}
    for x in a.rows.read_text().splitlines():
        if x.strip():
            r = json.loads(x)
            rows[r["instance_id"]] = r
    seen = set()
    if a.out.exists():
        for x in a.out.read_text().splitlines():
            if x.strip():
                d = json.loads(x)
                if d["status"] == "completed":  # an infrastructure error is retried (A105)
                    seen.add((d["kind"], d["file"], d["instance_id"]))
    jobs = []
    for f in a.results:
        for run in json.loads(f.read_text())["runs"]:
            p = run.get("patch") or ""
            if p.strip() and "S" in run and "infra_error" not in run:
                jobs.append(
                    ("patch", f.name, run["instance_id"], p, bool(run["S"].get("resolved")))
                )
    first = sorted(rows.values(), key=lambda r: r.get("_gskill_order", 0))
    for inst in [r for r in first if r.get("_gskill_split") == "test"][: a.controls]:
        jobs.append(("gold", "-", inst["instance_id"], inst["patch"], True))
        jobs.append(("noop", "-", inst["instance_id"], "", False))
    for kind, fname, iid, patch, recorded in jobs:
        if (kind, fname, iid) in seen:
            continue
        inst = rows[iid]
        assume_public(inst)
        g = grade(inst, patch, is_gold=(kind == "gold"))
        rec = {"kind": kind, "file": fname, "instance_id": iid, "recorded": recorded, **g}
        with a.out.open("a") as fh:
            fh.write(json.dumps(rec) + "\n")
        print(kind, fname, iid[-24:], recorded, g, flush=True)
    print(json.dumps({"K0b": summarise(a.out)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
