"""Section 25: export SWE-smith rows of one repository with gskill's own train/val/test split.

Runs where HuggingFace is reachable (Data snapshots workflow). Reproduces
`gepa.gskill.train_optimize_anything.load_and_split_data` at gepa@8c7b697 exactly: iterate
`load_dataset("SWE-bench/SWE-smith", split="train")` in order, keep rows whose `repo` contains
`swesmith/<repo>`, stop at train+val+test rows, `random.seed(seed); random.shuffle(rows)`, then
slice train | val | test. Refuses to write if the dataset card licence is not in PERMISSIVE.

Usage: python scripts/export_swesmith.py --repo pallets__jinja --train 200 --val 50 --test 100 \
           --seed 42 --out data/instances/swesmith_pallets__jinja.jsonl
"""

from __future__ import annotations

import argparse
import gzip
import json
import random
from pathlib import Path

PERMISSIVE = {"mit", "apache-2.0", "cc-by-4.0", "bsd-3-clause", "bsd-2-clause"}
HF_ID = "SWE-bench/SWE-smith"


def gskill_split(rows: list[dict], train: int, val: int, test: int, seed: int) -> list[dict]:
    """Same arithmetic as load_and_split_data (including the proportional scale-down)."""
    rows = list(rows)
    random.seed(seed)
    random.shuffle(rows)
    total = train + val + test
    if len(rows) < total:
        ratio = len(rows) / total
        train, val = int(train * ratio), int(val * ratio)
        test = len(rows) - train - val
    out = []
    for i, r in enumerate(rows):
        split = "train" if i < train else "val" if i < train + val else "test"
        if i >= train + val + test:
            break
        out.append({**r, "_gskill_split": split, "_gskill_order": i})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--train", type=int, required=True)
    ap.add_argument("--val", type=int, required=True)
    ap.add_argument("--test", type=int, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--extra-empty",
        type=int,
        help="section 35: also export the first N rows AFTER gskill's sample whose problem "
        "statement is empty (split 'extra'), to --extra-out",
    )
    ap.add_argument("--extra-out")
    a = ap.parse_args()

    from datasets import load_dataset
    from huggingface_hub import DatasetCard

    lic = (DatasetCard.load(HF_ID).data.to_dict().get("license") or "").lower()
    if lic not in PERMISSIVE:
        raise SystemExit(f"dataset licence {lic!r} not in {sorted(PERMISSIVE)}: not exporting")

    ds = load_dataset(HF_ID, split="train")
    pattern = a.repo if "/" in a.repo else f"swesmith/{a.repo}"
    need = a.train + a.val + a.test
    rows, extra, matched = [], [], 0
    for item in ds:
        if pattern in item.get("repo", ""):
            matched += 1
            if len(rows) < need:
                rows.append(dict(item))
            elif a.extra_empty and not (item.get("problem_statement") or "").strip():
                # dataset order; rows gskill never reads (it stops at `need` rows)
                extra.append(
                    {**dict(item), "_gskill_split": "extra", "_gskill_order": 100000 + matched}
                )
            if len(rows) >= need and len(extra) >= (a.extra_empty or 0):
                break
    out = gskill_split(rows, a.train, a.val, a.test, a.seed)
    p = Path(a.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    # .gz output: GitHub rejects files over 100 MB (pygments rows: 102 MB uncompressed, A91)
    opener = gzip.open if p.suffix == ".gz" else open
    with opener(p, "wt", encoding="utf-8") as fh:
        for r in out:
            fh.write(json.dumps(r, default=str) + "\n")
    if a.extra_empty:
        if len(extra) < a.extra_empty or not a.extra_out:
            raise SystemExit(f"only {len(extra)} extra rows without a problem statement")
        sample_ids = {r["instance_id"] for r in out}
        assert not sample_ids & {r["instance_id"] for r in extra}
        with open(a.extra_out, "w", encoding="utf-8") as fh:
            for r in extra:
                fh.write(json.dumps(r, default=str) + "\n")
        print(f"extra rows: {len(extra)} -> {a.extra_out}")
    meta = {
        "hf_id": HF_ID,
        "fingerprint": getattr(ds, "_fingerprint", None),
        "license": lic,
        "repo_pattern": pattern,
        "n_rows": len(out),
        "splits": {s: sum(r["_gskill_split"] == s for r in out) for s in ("train", "val", "test")},
        "seed": a.seed,
        "reproduces": "gepa@8c7b697 gskill/train_optimize_anything.py::load_and_split_data",
    }
    meta_path = Path(str(p).removesuffix(".gz").removesuffix(".jsonl") + ".meta.json")
    meta_path.write_text(json.dumps(meta, indent=1) + "\n")
    print(json.dumps(meta))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
