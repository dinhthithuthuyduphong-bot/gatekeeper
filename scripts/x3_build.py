#!/usr/bin/env python3
"""Section 49 (X3'): build the blind labelling bundle of the 104 traces (0 USD, no model call).

The traces are every run of the study agent with the original skill, in the shipped environment,
on a task without a description, in the three cohorts of the paper's "What the agent saw":
s27_trace34 + s27_trace34b (seed 41), s33_ship_skill restricted to tasks without a description
(seed 51), s35_ship_skill (seed 51, 36 new tasks). Runs that crashed or carry an infra error are
skipped, as in scripts/history_audit.py.

The bundle shows, per trace code: the messages in order, the agent's final patch, the benchmark's
bug patch and the FAIL_TO_PASS test names. It hides the cohort, seed, task id, scores and every
detector label. The key (code -> stem, instance id) is written separately.

  python scripts/x3_build.py --traces <dir with <stem>.json and <stem>.traces.jsonl.gz> \
      --rows <dir with swesmith_pallets__jinja.jsonl and extra36.jsonl> --seed 4901 \
      --bundle <out>/traces.json --key results/x3_codes.json
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import random
from pathlib import Path

STEMS = ["s27_trace34", "s27_trace34b", "s33_ship_skill", "s35_ship_skill"]
ROW_FILES = ["swesmith_pallets__jinja.jsonl", "extra36.jsonl"]


def load_rows(rows_dir: Path) -> dict[str, dict]:
    out = {}
    for name in ROW_FILES:
        for line in (rows_dir / name).read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                out[r["instance_id"]] = r
    return out


def f2p_names(row: dict) -> list[str]:
    f2p = row.get("FAIL_TO_PASS") or []
    if isinstance(f2p, str):
        f2p = json.loads(f2p) if f2p.startswith("[") else [f2p]
    return list(f2p)


def collect(traces_dir: Path, rows: dict[str, dict]) -> list[dict]:
    items = []
    for stem in STEMS:
        res = {
            r["instance_id"]: r
            for r in json.loads((traces_dir / f"{stem}.json").read_text())["runs"]
        }
        for line in gzip.open(traces_dir / f"{stem}.traces.jsonl.gz", "rt"):
            tr = json.loads(line)
            iid, msgs = tr["instance_id"], tr.get("messages")
            r, row = res.get(iid), rows.get(iid)
            if not msgs or r is None or row is None or "infra_error" in r or r.get("crashed"):
                continue
            if (row.get("problem_statement") or "").strip():
                continue  # the stratum is tasks without a description
            items.append(
                {
                    "stem": stem,
                    "instance_id": iid,
                    "messages": [
                        {"role": m.get("role"), "content": str(m.get("content", ""))} for m in msgs
                    ],
                    "agent_patch": r.get("patch") or "",
                    "bug_patch": row["patch"],
                    "f2p": f2p_names(row),
                }
            )
    return items


def blind(items: list[dict], seed: int) -> tuple[list[dict], dict[str, dict]]:
    order = list(range(len(items)))
    random.Random(seed).shuffle(order)
    bundle, key = [], {}
    for k, i in enumerate(order, start=1):
        code = f"T{k:03d}"
        it = items[i]
        key[code] = {"stem": it["stem"], "instance_id": it["instance_id"]}
        bundle.append(
            {
                "code": code,
                "messages": it["messages"],
                "agent_patch": it["agent_patch"],
                "bug_patch": it["bug_patch"],
                "f2p": it["f2p"],
            }
        )
    return bundle, key


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--traces", type=Path, required=True)
    ap.add_argument("--rows", type=Path, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--bundle", type=Path, required=True)
    ap.add_argument("--key", type=Path, required=True)
    a = ap.parse_args()
    items = collect(a.traces, load_rows(a.rows))
    bundle, key = blind(items, a.seed)
    text = json.dumps(bundle, ensure_ascii=False)
    a.bundle.write_text(text)
    a.key.write_text(
        json.dumps(
            {
                "seed": a.seed,
                "n": len(key),
                "bundle_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "codes": key,
            },
            indent=1,
        )
        + "\n"
    )
    print(
        len(key), "traces;", sum(1 for v in key.values() if v["stem"].startswith("s27")), "seed 41"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
