"""Positive-control skill `pc-oracle-files` (docs/preregistration_main_draft.md section 8): for each
task, the paths of the files the GOLD patch modifies, taken from the task row's `patch` field
(the code patch; the test patch is a separate field and is not used), as in SWE-bench's "Oracle"
retrieval setting (Jimenez et al. 2024). The text below is registered verbatim.

  python scripts/build_pc_guidance.py --rows e2_rows.jsonl --out runs/pc/guidance_by_instance.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

TEMPLATE = "The fix for this issue modifies the following file(s):\n{files}\n"
_DIFF = re.compile(r"^diff --git a/(\S+) b/(\S+)$", re.MULTILINE)


def files_of(patch: str) -> list[str]:
    seen: list[str] = []
    for a, b in _DIFF.findall(patch or ""):
        path = b if b != "/dev/null" else a
        if path not in seen:
            seen.append(path)
    return seen


def guidance(patch: str) -> str:
    files = files_of(patch)
    if not files:
        raise ValueError("gold patch names no file")
    return TEMPLATE.format(files="\n".join(f"- {f}" for f in files))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    out = {}
    for line in a.rows.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            out[r["instance_id"]] = guidance(r["patch"])
    a.out.parent.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(out, indent=1, sort_keys=True)
    a.out.write_text(blob)
    print(f"wrote {a.out} ({len(out)} tasks, sha256 {hashlib.sha256(blob.encode()).hexdigest()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
