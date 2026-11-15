"""Section 39 (kaggle/preregistration_s39.md): rebuild the 102 sham-audit prompts of section 19 C.

The prompts were built by scripts/sham_audit.py into a scratchpad that no longer exists. This
rebuilds them from the archived raw runs (branch raw-archive) with the same, unchanged
build_prompt, for exactly the 102 (condition, skill, iid, target, ref) rows of
results/sham_audit.json, in the same order. Task texts come from each archived part's own
dataset file (the rows the agent was run on).

  python kaggle/scripts/b39_build.py --archives <dir of g1-e1-*.tar.gz> \
      --out <scratchpad>/b39_prompts.jsonl.gz

The output contains trajectory text, so (as in section 19 C) it is not committed; it is uploaded to
Kaggle as a private dataset. Archives are read with tarfile only; nothing is extracted to disk.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import sham_audit as sa  # noqa: E402


class Parts:
    def __init__(self, folder: Path):
        self.folder, self.open = folder, {}

    def _tf(self, part: str) -> tarfile.TarFile:
        if part not in self.open:
            self.open[part] = tarfile.open(self.folder / f"{part}.tar.gz")
        return self.open[part]

    def read(self, part: str, rel: str) -> str:
        return self._tf(part).extractfile(f"runs/{part}/{rel}").read().decode("utf-8")

    def task(self, part: str, arm: str, iid: str) -> str:
        for line in self.read(part, f"{arm}/dataset/data.jsonl").splitlines():
            if line.strip():
                r = json.loads(line)
                if r["instance_id"] == iid:
                    return r["problem_statement"]
        raise KeyError((part, arm, iid))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archives", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    parts = Parts(a.archives)
    sa._traj = lambda part, arm, iid: json.loads(
        parts.read(part, f"{arm}/agent/{iid}/{iid}.traj.json")
    )

    def patch(part: str, arm: str, iid: str) -> str:
        preds = json.loads(parts.read(part, f"{arm}/agent/preds_scored.json"))
        return (preds.get(iid, {}).get("model_patch") or "(empty patch)")[: sa.PATCH_CHARS]

    sa._patch = patch
    rows = json.loads((ROOT / "results" / "sham_audit.json").read_text())["rows"]
    out = []
    for k, r in enumerate(rows):
        pair = {"skill": r["skill"], "iid": r["iid"], "target": r["target"], "ref": r["ref"]}
        tp, ta = r["target"]
        tasks = {r["iid"]: parts.task(tp, ta, r["iid"])}
        prompt = sa.build_prompt(pair, r["condition"], tasks)
        out.append(
            {
                "job": k,
                "condition": r["condition"],
                **pair,
                "gemini_flash_lite_tokens_in": int(r["tokens_in"]),
                "chars": len(prompt),
                "sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "prompt": prompt,
            }
        )
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(a.out, "wt", encoding="utf-8") as fh:
        for r in out:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    ratio = sorted(r["chars"] / r["gemini_flash_lite_tokens_in"] for r in out)
    print(
        json.dumps(
            {
                "jobs": len(out),
                "chars_per_recorded_token_min_median_max": [ratio[0], ratio[50], ratio[-1]],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
