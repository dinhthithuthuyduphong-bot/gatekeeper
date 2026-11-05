"""Per-run tokens and wall time from agent trajectories (docs/preregistration_main.md section 18,
execution note 18-1). 0 USD. Writes results/run_metrics_<stage>.json.

  python scripts/run_metrics.py --stage e1      # trajectories under runs/ (E1 is still on disk)
  python scripts/run_metrics.py --stage e2      # trajectories from the raw-archive branch

Tokens = sum of prompt_tokens + completion_tokens over every `usage` dict in the trajectory.
Time = last message timestamp minus first message timestamp (trials.jsonl has wall_seconds = 0).
"""

from __future__ import annotations

import argparse
import glob
import io
import json
import subprocess
import tarfile
from pathlib import Path

STAGES = {"e1": "results/pilot/g1-e1-s*-p[0-9][0-9].json", "e2": "results/e2/g2-e2-s*-k*-p*.json"}


def _walk_usage(o, acc: list[int]) -> None:
    if isinstance(o, dict):
        u = o.get("usage")
        if isinstance(u, dict) and "prompt_tokens" in u:
            acc[0] += int(u.get("prompt_tokens") or 0)
            acc[1] += int(u.get("completion_tokens") or 0)
        for v in o.values():
            _walk_usage(v, acc)
    elif isinstance(o, list):
        for v in o:
            _walk_usage(v, acc)


def metrics(traj: dict) -> dict:
    """Pure: tokens and wall time of one trajectory."""
    acc = [0, 0]
    _walk_usage(traj, acc)
    ts = []
    for m in traj.get("messages", []):
        t = (m.get("extra") or {}).get("timestamp")
        if t is not None:
            ts.append(float(t))
    return {
        "tokens_in": acc[0],
        "tokens_out": acc[1],
        "tokens": acc[0] + acc[1],
        "seconds": (max(ts) - min(ts)) if len(ts) >= 2 else None,
        "n_timestamps": len(ts),
    }


def _parts(stage: str) -> list[str]:
    return sorted(Path(f).stem for f in glob.glob(STAGES[stage]))


def _from_disk(part: str) -> dict[str, dict]:
    out = {}
    for f in glob.glob(f"runs/{part}/*/agent/*/*.traj.json"):
        arm = Path(f).parts[2]
        iid = Path(f).parent.name
        out[f"{arm}/{iid}"] = metrics(json.loads(Path(f).read_text()))
    return out


def _from_archive(part: str) -> dict[str, dict]:
    shard = part.rsplit("-p", 1)[0]
    raw = subprocess.run(
        ["git", "show", f"origin/raw-archive:archive/{shard}/{part}.tar.gz"],
        capture_output=True,
        check=True,
    ).stdout
    out = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tf:
        for m in tf.getmembers():
            p = Path(m.name)
            if not m.isfile() or not m.name.endswith(".traj.json"):
                continue
            # runs/<part>/<arm>/agent/<iid>/<iid>.traj.json
            arm, iid = p.parts[2], p.parent.name
            out[f"{arm}/{iid}"] = metrics(json.loads(tf.extractfile(m).read()))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=sorted(STAGES), required=True)
    a = ap.parse_args()
    reader = _from_disk if a.stage == "e1" else _from_archive
    res = {}
    for part in _parts(a.stage):
        res[part] = reader(part)
    n = sum(len(v) for v in res.values())
    no_time = sum(1 for v in res.values() for x in v.values() if x["seconds"] is None)
    out = {
        "stage": a.stage,
        "n_parts": len(res),
        "n_runs": n,
        "runs_without_time": no_time,
        "runs": res,
    }
    Path(f"results/run_metrics_{a.stage}.json").write_text(json.dumps(out, indent=0) + "\n")
    print(f"{a.stage}: {len(res)} parts, {n} runs, {no_time} without timestamps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
