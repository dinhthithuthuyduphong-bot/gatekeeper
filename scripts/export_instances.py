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
                rows[r["instance_id"]] = dict(r)
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
