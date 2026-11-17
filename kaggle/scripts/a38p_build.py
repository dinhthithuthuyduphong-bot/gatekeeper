"""Section 38, note 38-10 (A'): paired prompts for the reference model (0 USD).

For each of the 6 saved calls of cell leak/ablated, the renamed prompt is the same prompt with every
match of RENAME (case-insensitive: "Bug Patch", "bug patch", "bug-patch", "bug_patch") replaced by
the neutral message of section 43 ("Merge branch 'stable'", configs/c10.json). Nothing else
changes; the check below rebuilds the original from the renamed prompt and the recorded positions.

  python kaggle/scripts/a38p_build.py --prompts kaggle/data/a38_prompts.jsonl.gz \
      --out kaggle/data/a38p_prompts.jsonl.gz
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RENAME = re.compile(r"bug[ _-]?patch", re.IGNORECASE)


def rename(prompt: str, neutral: str) -> tuple[str, list[tuple[int, str]]]:
    """Return the renamed prompt and (position, original text) of every replacement."""
    hits = [(m.start(), m.group(0)) for m in RENAME.finditer(prompt)]
    return RENAME.sub(neutral, prompt), hits


def restore(renamed: str, hits: list[tuple[int, str]], neutral: str) -> str:
    out, src, shift = [], 0, 0
    for pos, text in hits:
        at = pos + shift
        out.append(renamed[src:at])
        assert renamed[at : at + len(neutral)] == neutral
        out.append(text)
        src = at + len(neutral)
        shift += len(neutral) - len(text)
    out.append(renamed[src:])
    return "".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    neutral = json.loads((ROOT / "configs" / "c10.json").read_text())["neutral_message"]
    assert not RENAME.search(neutral)
    rows = [json.loads(x) for x in gzip.open(a.prompts, "rt")]
    out = []
    for p in rows:
        if (p["condition"], p["variant"]) != ("leak", "ablated"):
            continue
        new, hits = rename(p["prompt"], neutral)
        assert hits and not RENAME.search(new) and neutral not in p["prompt"]
        assert restore(new, hits, neutral) == p["prompt"]
        out.append(
            {
                "pid": p["pid"].replace("-ablated", "-renamed"),
                "pair_of": p["sha256"],
                "condition": "leak",
                "variant": "renamed",
                "replacements": len(hits),
                "replaced_forms": sorted({t for _, t in hits}),
                "prompt_chars": len(new),
                "sha256": hashlib.sha256(new.encode()).hexdigest(),
                "prompt": new,
            }
        )
    assert len(out) == 6
    data = "".join(json.dumps(r) + "\n" for r in out).encode()
    with gzip.GzipFile(a.out, "wb", mtime=0) as fh:  # deterministic bytes
        fh.write(data)
    print(json.dumps([{k: r[k] for k in ("pid", "replacements", "replaced_forms")} for r in out]))
    print("sha256 gz", hashlib.sha256(a.out.read_bytes()).hexdigest())
    print("sha256 jsonl", hashlib.sha256(data).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
