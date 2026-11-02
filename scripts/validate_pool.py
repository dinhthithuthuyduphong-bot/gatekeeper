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
import time
from pathlib import Path

from gatekeeper.harness import NOOP_PATCH, loss_of, read_report, run_harness

OUT = Path("results/pool_validation")
TAG = "default"


def out_dir() -> Path:
    return OUT / TAG


def shard_ids(shard: int, shards: int) -> list[str]:
    ids = json.loads(Path(f"configs/pools/{TAG}.json").read_text())["instances"]
    return ids[shard::shards]


RETRIES = 2
RETRY_WAIT_S = 90


def _preds(name: str, ids: list[str]) -> str:
    p = Path(f"preds_{name}.jsonl")
    p.write_text(
        "".join(
            json.dumps({"instance_id": i, "model_name_or_path": "noop", "model_patch": NOOP_PATCH})
            + "\n"
            for i in ids
        )
    )
    return str(p)


def _run_with_retries(
    arm: str, ids: list[str], run_id: str, workers: int
) -> dict[str, dict | None]:
    """Run one arm; tasks without a report (image pull / eval infrastructure errors) are retried
    under a fresh run id instead of being mistaken for real failures."""
    reports: dict[str, dict | None] = {}
    todo = list(ids)
    for attempt in range(RETRIES + 1):
        rid = run_id if attempt == 0 else f"{run_id}-r{attempt}"
        preds = "gold" if arm == "gold" else _preds(rid, todo)
        try:
            run_harness(preds, todo, rid, workers)
        except SystemExit as exc:  # harness crash: keep going, missing reports are retried
            print(f"harness error in {rid}: {exc}", flush=True)
        model = "gold" if arm == "gold" else "noop"
        for i in todo:
            reports[i] = read_report(rid, model, i)
        todo = [i for i in todo if reports[i] is None]
        if not todo:
            break
        if attempt < RETRIES:
            print(
                f"{len(todo)} tasks without report in {rid}; retrying in {RETRY_WAIT_S}s",
                flush=True,
            )
            time.sleep(RETRY_WAIT_S)
    return reports


def classify(ra: dict | None, rb: dict | None, rn: dict | None) -> dict:
    if ra is None or rb is None or rn is None:
        return {"usable": False, "infra_error": True, "reason": "infra: no report after retries"}
    la, ia = loss_of(ra)
    lb, ib = loss_of(rb)
    _, in_ = loss_of(rn)
    ok_gold = ia.get("resolved") and ib.get("resolved")
    stable = la == lb and ia.get("R") == ib.get("R")
    ok_noop = in_.get("F") == 1.0 and in_.get("R") == 0.0
    bad = [
        x
        for x, b in (
            ("gold not resolved", not ok_gold),
            ("unstable", not stable),
            ("noop arm not clean", not ok_noop),
        )
        if b
    ]
    return {
        "gold_a": ia,
        "gold_b": ib,
        "noop": in_,
        "usable": not bad,
        "infra_error": False,
        "reason": ";".join(bad),
    }


def validate(shard: int, shards: int, workers: int) -> dict:
    ids = shard_ids(shard, shards)
    tag = f"{TAG}{shard}"
    ga = _run_with_retries("gold", ids, f"{tag}-gold-a", workers)
    gb = _run_with_retries("gold", ids, f"{tag}-gold-b", workers)
    nn = _run_with_retries("noop", ids, f"{tag}-noop", workers)
    res = {}
    for i in ids:
        res[i] = classify(ga[i], gb[i], nn[i])
        print(f"{i:<40} usable={res[i]['usable']} {res[i]['reason']}")
    out_dir().mkdir(parents=True, exist_ok=True)
    (out_dir() / f"shard{shard}.json").write_text(json.dumps(res, indent=2) + "\n")
    return res


def merge() -> dict:
    allres: dict = {}
    for f in sorted(out_dir().glob("shard*.json")):
        allres.update(json.loads(f.read_text()))
    usable = sorted(i for i, v in allres.items() if v["usable"])
    expected = (
        json.loads(Path(f"configs/pools/{TAG}.json").read_text())["instances"]
        if (Path(f"configs/pools/{TAG}.json").exists())
        else list(allres)
    )
    summary = {
        "n_expected": len(expected),
        "n_checked": len(allres),
        "n_usable": len(usable),
        "usable": usable,
        "rejected": {
            i: v["reason"]
            for i, v in allres.items()
            if not v["usable"] and not v.get("infra_error")
        },
        "infra_error": sorted(i for i, v in allres.items() if v.get("infra_error")),
        "missing": sorted(set(expected) - set(allres)),
    }
    (out_dir() / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: summary[k] for k in ("n_expected", "n_checked", "n_usable")}), summary)
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
