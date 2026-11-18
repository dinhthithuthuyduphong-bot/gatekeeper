"""X1' gate (docs/plan_vs_review.md, sections 9-10): did a gskill learning run use the same
train/val/test split as the exported rows on `data-snapshots`? 0 USD, no model call.

gskill (gepa@8c7b697, train_optimize_anything.py::load_and_split_data) loads the unpinned
Hugging Face dataset SWE-bench/SWE-smith, keeps the first matching rows, then shuffles with
--seed. A changed dataset would change the split even with the same seed. Every task ID that a
learning run's logs mention must be in the snapshot's train or val split; an ID in test, or not
in the snapshot, means the split differs.

  python scripts/split_identity.py --rows <swesmith_<repo>.jsonl[.gz]> \
      --archives <learn_run.tar.gz> ... --out results/split_identity.json
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import tarfile
from collections import Counter
from pathlib import Path

ID = re.compile(rb"[a-z0-9_-]+__[a-z0-9_-]+\.[0-9a-f]{8}\.[a-z_]+__[a-z0-9]{8}")
LOGS = re.compile(r"(training|run_log|terminal)\.(log|txt)$|run_log\.json$")


def split_of(rows_file: Path) -> dict[str, str]:
    raw = rows_file.read_bytes()
    if rows_file.name.endswith(".gz"):
        raw = gzip.decompress(raw)
    return {
        r["instance_id"]: r["_gskill_split"]
        for r in map(json.loads, raw.decode("utf-8").splitlines())
        if r
    }


def ids_in_logs(archive: Path) -> set[str]:
    out: set[str] = set()
    with tarfile.open(archive) as tf:
        for m in tf:
            if m.isfile() and LOGS.search(m.name):
                out |= {x.decode() for x in ID.findall(tf.extractfile(m).read())}
    return out


def check(split: dict[str, str], ids: set[str]) -> dict:
    where = Counter(split.get(i, "not_in_snapshot") for i in ids)
    return {
        "ids_in_logs": len(ids),
        "by_split": dict(where),
        "same_split": bool(ids) and where["test"] == 0 and where["not_in_snapshot"] == 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True, type=Path)
    ap.add_argument("--archives", required=True, nargs="+", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    split = split_of(a.rows)
    res = {"rows": a.rows.name, "runs": {p.name: check(split, ids_in_logs(p)) for p in a.archives}}
    a.out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))
    return 0 if all(r["same_split"] for r in res["runs"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
