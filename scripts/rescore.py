"""P26 (docs/potential_issues.md section 4): is SWE-smith's scorer stable on our own patches?

Re-scores every non-empty patch of the given result files with SWE-smith's grading
(f0_scorer_check.score_strict), `--repeats` more times, and compares with the recorded S. No model
call (0 USD). Appends one JSON line per (file, task, repeat) to `--out`, so an interrupted run
resumes where it stopped.

  PYTHONPATH=scripts python scripts/rescore.py --rows swesmith_pallets__jinja.jsonl \
      --results results/f1_probe.json results/f1_skill_probe.json --repeats 2 \
      --out results/rescore_jinja.jsonl
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path


def load_rows(path: str) -> dict[str, dict]:
    raw = Path(path).read_bytes()
    text = (gzip.decompress(raw) if path.endswith(".gz") else raw).decode("utf-8")
    rows = [json.loads(x) for x in text.splitlines() if x.strip()]
    return {r["instance_id"]: r for r in rows}


def done_keys(out: Path) -> set[tuple[str, str, int]]:
    if not out.exists():
        return set()
    keys = set()
    for line in out.read_text().splitlines():
        if line.strip():
            d = json.loads(line)
            if d.get("status") == "completed":  # an infrastructure error is retried (A105)
                keys.add((d["file"], d["instance_id"], d["repeat"]))
    return keys


def summarise(out: Path) -> dict:
    """Per file: patches re-scored, how many repeats disagree with the recorded S."""
    by: dict[str, dict] = {}
    for line in out.read_text().splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        f = by.setdefault(d["file"], {"tasks": {}, "infra": 0})
        if d.get("status") != "completed":
            f["infra"] += 1
            continue
        f["tasks"].setdefault(d["instance_id"], {"orig": d["orig"], "new": []})["new"].append(
            d["resolved"]
        )
    res = {}
    for name, f in by.items():
        t = f["tasks"]
        flips = [i for i, v in t.items() if any(x != v["orig"] for x in v["new"])]
        res[name] = {
            "patches": len(t),
            "repeats_scored": sum(len(v["new"]) for v in t.values()),
            "tasks_with_any_flip": len(flips),
            "flipped_tasks": sorted(flips),
            "orig_resolved": sum(v["orig"] for v in t.values()),
            "infra_not_completed": f["infra"],
        }
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True)
    ap.add_argument("--results", nargs="+", required=True)
    ap.add_argument("--repeats", type=int, required=True)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--summary-only", action="store_true")
    a = ap.parse_args()
    if not a.summary_only:
        from f0_scorer_check import assume_public, score_strict

        rows = load_rows(a.rows)
        done = done_keys(a.out)
        for rf in a.results:
            name = Path(rf).name
            for run in json.loads(Path(rf).read_text())["runs"]:
                patch = run.get("patch") or ""
                if not patch.strip() or "S" not in run:
                    continue
                inst = rows[run["instance_id"]]
                assume_public(inst)
                for k in range(a.repeats):
                    if (name, run["instance_id"], k) in done:
                        continue
                    try:
                        s = score_strict(inst, patch)
                    except Exception as e:  # noqa: BLE001 - infrastructure, recorded
                        s = {"resolved": None, "status": f"error: {type(e).__name__}"}
                    rec = {
                        "file": name,
                        "instance_id": run["instance_id"],
                        "repeat": k,
                        "orig": bool(run["S"].get("resolved")),
                        **s,
                    }
                    with a.out.open("a") as fh:
                        fh.write(json.dumps(rec) + "\n")
                    print(f"{name} {run['instance_id'][:40]} r{k} {s}", flush=True)
    print(json.dumps(summarise(a.out), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
