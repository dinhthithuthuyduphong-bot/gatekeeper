"""Validate the pilot task pool with the official harness, no LLM (TODO.md Phase 4 'Kiem tra moi
task chay duoc bang harness chinh thuc (gold pass, khong flaky)').

For the shard's tasks: gold patch twice (flakiness: the two runs must agree) and the no-op patch
once (the no-skill arm must evaluate with F = 1, R = 0).
Writes results/pool_validation/<tag>/shard<k>.json.

  python scripts/validate_pool.py --shard 0 --shards 4
  python scripts/validate_pool.py --merge          # combine shard files
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gatekeeper.harness import NOOP_PATCH, loss_of, read_report, run_harness

OUT = Path("results/pool_validation")
TAG = "default"


def out_dir() -> Path:
    return OUT / TAG


def shard_ids(shard: int, shards: int) -> list[str]:
    ids = json.loads(Path(f"configs/pools/{TAG}.json").read_text())["instances"]
    return ids[shard::shards]


def validate(shard: int, shards: int, workers: int) -> dict:
    ids = shard_ids(shard, shards)
    noop = Path(f"preds_noop_{shard}.jsonl")
    noop.write_text(
        "".join(
            json.dumps({"instance_id": i, "model_name_or_path": "noop", "model_patch": NOOP_PATCH})
            + "\n"
            for i in ids
        )
    )
    tag = f"{TAG}{shard}"
    run_harness("gold", ids, f"{tag}-gold-a", workers)
    run_harness("gold", ids, f"{tag}-gold-b", workers)
    run_harness(str(noop), ids, f"{tag}-noop", workers)
    res = {}
    for i in ids:
        la, ia = loss_of(read_report(f"{tag}-gold-a", "gold", i))
        lb, ib = loss_of(read_report(f"{tag}-gold-b", "gold", i))
        ln, in_ = loss_of(read_report(f"{tag}-noop", "noop", i))
        ok_gold = ia.get("resolved") and ib.get("resolved")
        stable = la == lb and ia.get("R") == ib.get("R")
        ok_noop = in_.get("note") != "no report" and in_.get("F") == 1.0 and in_.get("R") == 0.0
        res[i] = {
            "gold_a": ia,
            "gold_b": ib,
            "noop": in_,
            "usable": bool(ok_gold and stable and ok_noop),
            "reason": ""
            if ok_gold and stable and ok_noop
            else ";".join(
                x
                for x, bad in (
                    ("gold not resolved", not ok_gold),
                    ("unstable", not stable),
                    ("noop arm not clean", not ok_noop),
                )
                if bad
            ),
        }
        print(f"{i:<40} usable={res[i]['usable']} {res[i]['reason']}")
    out_dir().mkdir(parents=True, exist_ok=True)
    (out_dir() / f"shard{shard}.json").write_text(json.dumps(res, indent=2) + "\n")
    return res


def merge() -> dict:
    allres: dict = {}
    for f in sorted(out_dir().glob("shard*.json")):
        allres.update(json.loads(f.read_text()))
    usable = sorted(i for i, v in allres.items() if v["usable"])
    summary = {
        "n_checked": len(allres),
        "n_usable": len(usable),
        "usable": usable,
        "rejected": {i: v["reason"] for i, v in allres.items() if not v["usable"]},
    }
    (out_dir() / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: summary[k] for k in ("n_checked", "n_usable")}), summary["rejected"])
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--shards", type=int, default=1)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--tag", default="default", help="pool name: configs/pools/<tag>.json")
    a = ap.parse_args()
    global TAG
    TAG = a.tag
    if a.merge:
        merge()
    else:
        validate(a.shard, a.shards, a.workers)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
