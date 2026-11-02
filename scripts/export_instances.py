"""Export the SWE-bench Verified rows of every task pool (configs/pools/*.json) to
data/instances/verified_pools.jsonl, so the pilot can run where HuggingFace is unreachable
(the harness and run_pilot.py accept this file via --dataset-file). Runs in GitHub Actions."""

from __future__ import annotations

import json
from pathlib import Path

DATASET = "SWE-bench/SWE-bench_Verified"  # swebench>=5 format (image, eval_script, log_parser)


def main() -> int:
    from datasets import load_dataset

    ids: set[str] = set()
    for p in Path("configs/pools").glob("*.json"):
        ids |= set(json.loads(p.read_text())["instances"])
    rows = [dict(r) for r in load_dataset(DATASET, split="test") if r["instance_id"] in ids]
    out = Path("data/instances/verified_pools.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for r in sorted(rows, key=lambda r: r["instance_id"]):
            fh.write(json.dumps(r, default=str) + "\n")
    print(f"exported {len(rows)}/{len(ids)} rows -> {out} ({out.stat().st_size // 1024} KiB)")
    return 0 if len(rows) == len(ids) else 1


if __name__ == "__main__":
    raise SystemExit(main())
