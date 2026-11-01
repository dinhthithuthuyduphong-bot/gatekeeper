"""Write data/splits/split_v0.json from data/benchmarks/*.csv (TODO.md Phase 4).

Usage: python scripts/make_split.py [--bench data/benchmarks] [--out data/splits/split_v0.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from gatekeeper.splits import load_tasks, make_split


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", default="data/benchmarks")
    ap.add_argument("--out", default="data/splits/split_v0.json")
    a = ap.parse_args()
    tasks = load_tasks(a.bench)
    if not tasks:
        print(f"no CSV files in {a.bench}; run the 'Data snapshots' workflow first")
        return 1
    split = make_split(tasks, thresholds=(30, 50, 100, 219, 500, 752))
    body = json.dumps(split, indent=2, ensure_ascii=False, sort_keys=True)
    split_hash = hashlib.sha256(body.encode()).hexdigest()[:16]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps({"sha256_16": split_hash, **split}, indent=2, ensure_ascii=False) + "\n"
    )
    print(
        f"train repos={len(split['train_repos'])} tasks={split['n_train_tasks']} | "
        f"test repos={len(split['test_repos'])} tasks={split['n_test_tasks']} | "
        f"removed for overlap={split['repos_removed_from_test_for_overlap']}"
    )
    print("scopes with >= n distinct tasks:", split["scopes_with_at_least"])
    print("hash", split_hash)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
