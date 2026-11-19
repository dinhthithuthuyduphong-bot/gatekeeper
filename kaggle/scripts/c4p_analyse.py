"""C4' analysis (kaggle/preregistration_s40.md, note 40-5; sensitivity of note 40-10). 0 USD.

  python kaggle/scripts/c4p_analyse.py --dir <unzipped c4p_results> --tag haiku \
      --nodesc-test kaggle/data/c4p_nodesc_test34.txt --test-chunks 10 \
      --lam 0.5 --theta 0 --threshold 120 --out kaggle/results/c4p/haiku_analysis.json

Main test of one agent (note 40-5, items 1-3): on the tasks without an issue description (the
34 test tasks of section 34 plus every task of the extra chunks, i.e. the 36 tasks of section
35), D_i = (Z_shipped - Z_single)/2 with Z = fails(skill) - fails(none) and fails = not
resolved by S; null sum E[D_i | C] >= 0; end-of-pool test, reject when E >= threshold (the
family threshold 3/alpha = 120 for three agents). A task with a crashed run in any arm is
dropped from every arm (note 40-13). Sensitivity (note 40-10, post hoc): the same
with every task dropped where any arm's run downloaded the released package.
"""

from __future__ import annotations

import argparse
import glob
import gzip
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from gatekeeper.eprocess import end_of_pool_log_e  # noqa: E402

ARMS = ("none", "skill", "lf_none", "lf_skill")
# fixed in note 40-10 before any C4' gain was computed
DOWNLOAD = re.compile(
    r"pip\s+download|pip\s+install\s+[^\n]*jinja2?\s*==|pypi\.org|files\.pythonhosted"
)


def load(d: Path, tag: str) -> tuple[dict, dict]:
    runs, chunk = {a: {} for a in ARMS}, {}
    for f in glob.glob(f"{d}/{tag}_*_c[0-9][0-9].json"):
        m = re.match(rf".*/{tag}_(.+)_c(\d+)\.json$", f)
        arm, k = m.group(1), int(m.group(2))
        for r in json.load(open(f))["runs"]:
            runs[arm][r["instance_id"]] = r
            chunk[r["instance_id"]] = k
    return runs, chunk


def downloads(d: Path, tag: str) -> set[str]:
    hit = set()
    for f in glob.glob(f"{d}/{tag}_*_c[0-9][0-9].traces.jsonl.gz"):
        for line in gzip.open(f, "rt"):
            t = json.loads(line)
            text = " ".join(
                str(m.get("content", ""))
                for m in (t.get("messages") or [])
                if m.get("role") == "assistant"
            )
            if DOWNLOAD.search(text):
                hit.add(t["instance_id"])
    return hit


def fails(r: dict) -> int:
    return int(not (r.get("S") or {}).get("resolved"))


def contrast(runs: dict, ids: list[str], lam: float, theta: float, threshold: float) -> dict:
    ds, solved = [], {a: 0 for a in ARMS}
    for i in ids:
        z = fails(runs["skill"][i]) - fails(runs["none"][i])
        zl = fails(runs["lf_skill"][i]) - fails(runs["lf_none"][i])
        ds.append((z - zl) / 2)
        for a in ARMS:
            solved[a] += 1 - fails(runs[a][i])
    e = math.exp(end_of_pool_log_e(ds, lam, theta))
    n = len(ds)
    mean = sum(ds) / n
    sd = (sum((x - mean) ** 2 for x in ds) / (n - 1)) ** 0.5
    return {
        "n": n,
        "solved": solved,
        "mean_D": mean,
        "ci95_D": [mean - 1.96 * sd / n**0.5, mean + 1.96 * sd / n**0.5],
        "neg_pos": [sum(x < 0 for x in ds), sum(x > 0 for x in ds)],
        "E": e,
        "reject": e >= threshold,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--nodesc-test", type=Path, required=True)
    ap.add_argument("--test-chunks", type=int, required=True)
    ap.add_argument("--lam", type=float, required=True)
    ap.add_argument("--theta", type=float, required=True)
    ap.add_argument("--threshold", type=float, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    runs, chunk = load(a.dir, a.tag)
    complete = set.intersection(*(set(v) for v in runs.values()))
    # note 40-13: a task whose run crashed in any arm (kept after a second crash) is dropped
    # from every arm of this agent
    crashed = {i for v in runs.values() for i, r in v.items() if r.get("crashed")}
    complete -= crashed
    nodesc = set(a.nodesc_test.read_text().split()) | {
        i for i, k in chunk.items() if k >= a.test_chunks
    }
    ids = sorted(nodesc & complete)
    dl = downloads(a.dir, a.tag)
    res = {
        "tag": a.tag,
        "tasks_complete_all_arms": len(complete),
        "pool_missing": sorted(nodesc - complete),
        "dropped_crashed": sorted(crashed),
        "main": contrast(runs, ids, a.lam, a.theta, a.threshold),
        "sensitivity_without_downloads": contrast(
            runs, [i for i in ids if i not in dl], a.lam, a.theta, a.threshold
        ),
        "download_tasks_in_pool": sorted(dl & set(ids)),
        "all_tasks_solved": {a_: sum(1 - fails(r) for r in runs[a_].values()) for a_ in ARMS},
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k != "download_tasks_in_pool"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
