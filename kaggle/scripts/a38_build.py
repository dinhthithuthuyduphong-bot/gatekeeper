"""Section 38 (kaggle/preregistration_s38.md): the prompts sent to other skill writers (0 USD).

Reads the three saved gskill learning runs and writes kaggle/data/a38_prompts.jsonl.gz, one row per
(call, variant), with the prompt gskill sent to its reflection model, byte for byte, except that in
the "ablated" variant every line of the parent skill that matches the registered rule of section 29
(scripts/make_ablation.py: RULE) is removed from the parent-skill block of the prompt.

  python kaggle/scripts/a38_build.py --jinja <s25_learn_run.tar.gz> \
      --bleve <s25bleve_learn_run.tar.gz> --clean results/s30_learn_run.tar.gz \
      --out kaggle/data/a38_prompts.jsonl.gz

Archives of runs are untrusted data: read with tarfile only, nothing is extracted or executed.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from make_ablation import RULE, ablate  # noqa: E402

# Section 36b's leak marker, copied from scripts/s36_analysis.py (branch main): a trajectory "shows
# the leak" when an observation returned to the agent contains the injected commit's subject.
M2 = "Bug Patch"
SKILL_BLOCK = "## Current Skills\nThe agent currently has these learned skills:\n```\n{}\n```"


def split_trace(t: str) -> tuple[str, list[str]]:
    """Copied from scripts/s36_analysis.py (main): agent commands and the observations."""
    parts = re.split(r"^\[(SYSTEM|USER|ASSISTANT)\]\s*$", t, flags=re.M)
    blocks = list(zip(parts[1::2], parts[2::2], strict=True))
    cmd = "\n".join(b for r, b in blocks if r == "ASSISTANT")
    users = [b for r, b in blocks if r == "USER"]
    return cmd, users[1:]


def shows_leak(call: dict) -> list[bool]:
    out = []
    for e in call["evaluation_data"]:
        _, obs = split_trace(e["Generated Outputs"].get("Agent Trace", ""))
        out.append(any(M2 in o for o in obs))
    return out


def calls_of(archive: Path) -> list[dict]:
    with tarfile.open(archive) as tf:
        names = [n for n in tf.getnames() if re.search(r"proposer_calls/call_\d+\.json$", n)]
        names.sort(key=lambda n: int(re.search(r"call_(\d+)\.json$", n).group(1)))
        return [json.loads(tf.extractfile(n).read().decode("utf-8")) for n in names]


def ablated_prompt(call: dict) -> tuple[str, list[int]]:
    cur = call["current_skills"]
    if not cur:  # gskill's format_prompt writes "(No skills learned yet)": nothing to remove
        if "```\n(No skills learned yet)\n```" not in call["full_prompt"]:
            raise SystemExit(f"call {call['call_num']}: empty parent but no placeholder")
        return call["full_prompt"], []
    block = SKILL_BLOCK.format(cur)
    fp = call["full_prompt"]
    if fp.count(block) != 1:
        raise SystemExit(
            f"call {call['call_num']}: parent-skill block found {fp.count(block)} times"
        )
    new, drop = ablate(cur)
    return fp.replace(block, SKILL_BLOCK.format(new.rstrip("\n"))), drop


def rows(run: str, archive: Path, leaky_env: bool) -> list[dict]:
    out = []
    for c in calls_of(archive):
        if c["type"] != "batch" or not c.get("success"):
            raise SystemExit(f"{run} call {c['call_num']}: not a successful batch call")
        leak = shows_leak(c)
        if any(leak):
            cond = "leak"
        elif leaky_env:
            cond = "noleak_leaky_env"
        else:
            cond = "clean"
        variants = {"ablated": ablated_prompt(c)}
        if cond == "leak":
            variants["original"] = (c["full_prompt"], [])
        for var, (prompt, drop) in variants.items():
            out.append(
                {
                    "pid": f"{run}-c{c['call_num']:02d}-{var}",
                    "run": run,
                    "call": c["call_num"],
                    "condition": cond,
                    "variant": var,
                    "trajectories_showing_leak": sum(leak),
                    "parent_lines_removed": drop,
                    "parent_has_history_line": bool(RULE.search(c["current_skills"])),
                    "original_child_has_history_line": bool(RULE.search(c["new_skills"])),
                    "prompt_chars": len(prompt),
                    "sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                    "prompt": prompt,
                }
            )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jinja", required=True, type=Path)
    ap.add_argument("--bleve", required=True, type=Path)
    ap.add_argument("--clean", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    out = (
        rows("jinja", a.jinja, True) + rows("bleve", a.bleve, True) + rows("clean", a.clean, False)
    )
    if any(r["parent_has_history_line"] for r in out if r["condition"] == "clean"):
        raise SystemExit("a clean-run parent has a history line; the design assumes none")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(a.out, "wt", encoding="utf-8") as fh:
        for r in out:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = {}
    for r in out:
        k = f"{r['condition']}/{r['variant']}"
        summary[k] = summary.get(k, 0) + 1
    uniq = len({r["sha256"] for r in out})
    print(json.dumps({"rows": len(out), "unique_prompts": uniq, "by_cell": summary}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
