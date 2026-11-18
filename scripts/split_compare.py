"""Plan section 11, step 0.1: compare two exports of gskill's split, task by task (0 USD).

Same split = the same instance IDs, each with the same label (train/val/test) and the same
position (`_gskill_order`). Exit 1 on any difference.

  python scripts/split_compare.py --old <dir> --new <dir> --files <name> ... --out split_check.json
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path


def load(p: Path) -> dict[str, tuple[str, int]]:
    raw = p.read_bytes()
    if p.name.endswith(".gz"):
        raw = gzip.decompress(raw)
    rows = [json.loads(x) for x in raw.decode("utf-8").splitlines() if x.strip()]
    return {r["instance_id"]: (r["_gskill_split"], r["_gskill_order"]) for r in rows}


def compare(old: dict, new: dict) -> dict:
    only_old = sorted(set(old) - set(new))
    only_new = sorted(set(new) - set(old))
    moved = sorted(i for i in set(old) & set(new) if old[i] != new[i])
    return {
        "n_old": len(old),
        "n_new": len(new),
        "only_old": only_old[:20],
        "only_new": only_new[:20],
        "label_or_order_changed": moved[:20],
        "identical": not only_old and not only_new and not moved,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True, type=Path)
    ap.add_argument("--new", required=True, type=Path)
    ap.add_argument("--files", required=True, nargs="+")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    res = {f: compare(load(a.old / f), load(a.new / f)) for f in a.files}
    a.out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))
    return 0 if all(r["identical"] for r in res.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
