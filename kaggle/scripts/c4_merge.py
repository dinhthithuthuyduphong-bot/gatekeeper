"""Section 40, C4: join the chunk files of one arm into the result file that scripts/s25_ab.py
(branch trial, unchanged) reads, and the traces into one file.

  python kaggle/scripts/c4_merge.py --dir kaggle/results/c4 --tag haiku --out kaggle/results/c4
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

ARMS = ("none", "skill", "lf_none", "lf_skill")


def merge(folder: Path, tag: str, arm: str) -> tuple[dict, list[str]]:
    files = sorted(folder.glob(f"{tag}_{arm}_c[0-9][0-9].json"))
    runs, traces, head = [], [], None
    for f in files:
        d = json.loads(f.read_text())
        head = head or {k: v for k, v in d.items() if k not in ("runs", "n_tasks", "spent_usd")}
        runs += d["runs"]
        t = f.with_suffix(".traces.jsonl.gz")
        if t.exists():
            traces += [x for x in gzip.open(t, "rt") if x.strip()]
    ids = [r["instance_id"] for r in runs]
    if len(ids) != len(set(ids)):
        raise SystemExit(f"{tag} {arm}: a task appears in two chunks")
    runs.sort(key=lambda r: r["order"])
    return {**(head or {}), "n_tasks": len(runs), "chunks": len(files), "runs": runs}, traces


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, type=Path)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    for arm in ARMS:
        d, traces = merge(a.dir, a.tag, arm)
        (a.out / f"{a.tag}_{arm}.json").write_text(json.dumps(d, indent=1) + "\n")
        with gzip.open(a.out / f"{a.tag}_{arm}.traces.jsonl.gz", "wt") as fh:
            fh.writelines(traces)
        print(a.tag, arm, d["n_tasks"], "tasks,", d["chunks"], "chunks,", len(traces), "traces")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
