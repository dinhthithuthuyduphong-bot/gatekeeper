"""Task pool for experiment E2 (docs/preregistration_e2.md): SWE-bench-Live (Python) tasks from
repositories that XRepoSkill did NOT learn from (all 12 SWE-bench repositories are excluded:
XRepoSkill's skills were distilled from SWE-bench Verified trajectories), in a RANDOM order fixed
by SEED. The pool is validated in that order and the first N usable tasks are used (simple random
sampling without replacement). Runs in GitHub Actions (needs HuggingFace).
Writes data/e2_pool.json (copy to configs/pools/e2.json to validate it).
"""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path

DATASET = "SWE-bench-Live/SWE-bench-Live"  # Python, swebench-compatible (NeurIPS version)
SPLIT = "full"  # all tasks; the lite/verified splits are frozen subsets
SEED = "2027-e2"
N_VALIDATE = 120  # validated in random order; N used is fixed in the pre-registration


def main() -> int:
    from datasets import load_dataset

    csv.field_size_limit(2**31 - 1)
    with Path("data/benchmarks/swe-bench.csv").open(encoding="utf-8") as fh:
        swebench_repos = {r["repo"] for r in csv.DictReader(fh)}
    try:
        rows = list(load_dataset(DATASET, split=SPLIT))
    except Exception:  # noqa: BLE001 - fall back to the test split name
        rows = list(load_dataset(DATASET, split="test"))
    keep = sorted(r["instance_id"] for r in rows if r["repo"] not in swebench_repos)
    random.Random(SEED).shuffle(keep)
    repos = sorted({r["repo"] for r in rows if r["repo"] not in swebench_repos})
    out = {
        "_comment": __doc__.split("\n\n")[0],
        "dataset": DATASET,
        "split": SPLIT,
        "seed": SEED,
        "excluded_repos": sorted(swebench_repos),
        "n_candidates": len(keep),
        "n_repos": len(repos),
        "random_order": keep,
        "instances": sorted(keep[:N_VALIDATE]),
        "fields": sorted(rows[0].keys()) if rows else [],
    }
    Path("data").mkdir(exist_ok=True)
    Path("data/e2_pool.json").write_text(json.dumps(out, indent=1) + "\n")
    print(len(keep), "candidates from", len(repos), "repos; validating", len(out["instances"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
