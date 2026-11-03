"""Export the harness rows of every task pool (configs/pools/*.json) to
data/instances/verified_pools.jsonl, so the pilot can run where HuggingFace is unreachable
(the harness and run_pilot.py accept this file via --dataset-file). Runs in GitHub Actions.

Each pool may name its harness dataset ("dataset"; default SWE-bench Verified). Rows of the
Verified dataset take precedence for tasks present in both, so existing pools keep their rows."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

DATASET = "SWE-bench/SWE-bench_Verified"  # swebench>=5 format (image, eval_script, log_parser)


def main() -> int:
    from datasets import load_dataset

    wanted: dict[str, set[str]] = defaultdict(set)
    for p in Path("configs/pools").glob("*.json"):
        pool = json.loads(p.read_text())
        if not isinstance(pool, dict) or not isinstance(pool.get("instances"), list):
            continue  # task-set files (e.g. e1_task_sets.json) are not pools
        wanted[pool.get("dataset", DATASET)] |= set(pool["instances"])
    rows: dict[str, dict] = {}
    for ds in sorted(wanted, key=lambda d: d != DATASET):  # Verified first
        split = "full" if "Live" in ds else "test"
        try:
            data = load_dataset(ds, split=split)
        except Exception:  # noqa: BLE001
            data = load_dataset(ds, split="test")
        for r in data:
            if r["instance_id"] in wanted[ds] and r["instance_id"] not in rows:
                row = dict(r)
                if "Live" in ds:  # prebuilt image of SWE-bench-Live (namespace starryzhang)
                    key = r["instance_id"].lower().replace("__", "_1776_")
                    row["image"] = f"starryzhang/sweb.eval.x86_64.{key}:latest"
                    row["image_name"] = "docker.io/" + row["image"]  # mini-swe-agent's key
                rows[r["instance_id"]] = row
    # the datasets change over time (SWE-bench-Live grows every month): record the exact revision
    revisions = {}
    try:
        from huggingface_hub import HfApi

        for ds in wanted:
            revisions[ds] = HfApi().dataset_info(ds).sha
    except Exception as exc:  # noqa: BLE001
        revisions["_error"] = repr(exc)
    Path("data/instances").mkdir(parents=True, exist_ok=True)
    Path("data/instances/revisions.json").write_text(json.dumps(revisions, indent=1) + "\n")
    ids = set().union(*wanted.values())
    out = Path("data/instances/verified_pools.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for iid in sorted(rows):
            fh.write(json.dumps(rows[iid], default=str) + "\n")
    print(f"exported {len(rows)}/{len(ids)} rows -> {out} ({out.stat().st_size // 1024} KiB)")
    return 0 if len(rows) == len(ids) else 1


if __name__ == "__main__":
    raise SystemExit(main())
