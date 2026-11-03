"""Rebuild the E2 guidance file from the RECORDED rule selection (no LLM call), so E2 can run on
another machine (GitHub Actions) with exactly the same prompts (audit A55).

  python scripts/build_e2_guidance.py --clone <XRepoSkill clone> --out guidance_by_instance.json \
      [--expect-sha256 <hash of the file used locally>]

Inputs: results/e2_selection.json (rule ids per task, committed) and XRepoSkill at the pinned
commit (its rule text is not redistributed: the repository has no LICENSE, so the text is rebuilt
locally from the clone). Output text is rendered exactly as scripts/xreposkill_select.py does
(SKILL_FRAME + retrieval.render_rules). With --expect-sha256 the script stops if the rebuilt file
differs from the reference one."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from xreposkill_select import PINNED, pack, parse_strategies  # noqa: E402


def build(clone: Path, selection: dict) -> str:
    import subprocess

    head = subprocess.check_output(["git", "-C", str(clone), "rev-parse", "HEAD"], text=True)
    if head.strip() != PINNED or selection["xreposkill_commit"] != PINNED:
        raise SystemExit(f"XRepoSkill commit mismatch: clone {head.strip()}, expected {PINNED}")
    sys.path.insert(0, str(clone / "src"))
    from xreposkill import retrieval  # noqa: PLC0415
    from xreposkill.rollout import SKILL_FRAME  # noqa: PLC0415

    strategies = parse_strategies((clone / "data" / "general_strategies_36.md").read_text())
    with tempfile.TemporaryDirectory() as tmp:
        pack(strategies, Path(tmp))
        by_id = {r.rule_id: r for r in retrieval.load_rules(Path(tmp))}
    if len(by_id) != 36:
        raise SystemExit(f"parsed {len(by_id)} rules, expected 36")
    guidance = {}
    for iid, v in sorted(selection["per_task"].items()):
        rules = [by_id[r] for r in v["rule_ids"]]
        if rules:
            guidance[iid] = SKILL_FRAME.format(block=retrieval.render_rules(rules))
    return json.dumps(guidance, indent=1)  # same serialisation as xreposkill_select.py


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clone", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--expect-sha256", default="")
    a = ap.parse_args()
    selection = json.loads(Path("results/e2_selection.json").read_text())
    text = build(a.clone, selection)
    sha = hashlib.sha256(text.encode()).hexdigest()
    if a.expect_sha256 and sha != a.expect_sha256:
        raise SystemExit(f"rebuilt guidance {sha} != expected {a.expect_sha256}")
    a.out.write_text(text)
    print(f"wrote {a.out} ({len(json.loads(text))} tasks, sha256 {sha})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
