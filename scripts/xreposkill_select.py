"""E2 (docs/preregistration_e2.md): XRepoSkill's own rule selection on the E2 tasks.

XRepoSkill (pinned commit, cloned locally; the repository has no LICENSE, so its rule TEXT is never
committed here) publishes its 36 general strategies (data/general_strategies_36.md). This script
1. checks the clone is at the pinned commit,
2. packs the 36 strategies in XRepoSkill's own skill layout
   (skills/repo_conventions/<bucket>/SKILL.md, bullets "- **title** (tag) — body", parsed by its
   retrieval.parse_skill_md), one bucket "general", body = the strategy's Trigger and Action,
3. runs XRepoSkill's RetrievalFlow unchanged (2 backbone calls per issue, top_n = 3, temperature 0,
   its default config) with our agent's backbone,
4. renders each issue's selected rules exactly as its rollout does (SKILL_FRAME + render_rules).

Writes (scratchpad, never committed): <out>/skills/, <out>/retrieval/<iid>.json,
<out>/guidance_by_instance.json. Writes (committed): results/e2_selection.json with the selected
rule ids per task, the commit and token usage only.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from gatekeeper.pilot import estimate_cost_usd, load_model_specs

PINNED = "26fd70345698108c0fdce2d8904293a38b9cd42f"
_STRATEGY = re.compile(
    r"^## (?P<n>\d+)\. (?P<title>.+?)\n+\*\*Trigger:\*\*\s*(?P<trigger>.+?)\n+"
    r"\*\*Action:\*\*\s*(?P<action>.+?)(?=\n## |\Z)",
    re.MULTILINE | re.DOTALL,
)


def parse_strategies(md: str) -> list[dict]:
    out = []
    for m in _STRATEGY.finditer(md):
        out.append(
            {
                "n": int(m.group("n")),
                "title": " ".join(m.group("title").split()),
                "body": "Trigger: "
                + " ".join(m.group("trigger").split())
                + " Action: "
                + " ".join(m.group("action").split()),
            }
        )
    return out


def pack(strategies: list[dict], skills_root: Path) -> None:
    d = skills_root / "repo_conventions" / "general"
    d.mkdir(parents=True, exist_ok=True)
    lines = [f"- **{s['title']}** (strategy {s['n']}) — {s['body']}" for s in strategies]
    (d / "SKILL.md").write_text("# general\n\n" + "\n".join(lines) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clone", required=True, type=Path)
    ap.add_argument("--rows", required=True, type=Path, help="exported task rows (jsonl)")
    ap.add_argument(
        "--ids",
        required=True,
        type=Path,
        nargs="+",
        help="pool summaries or pool files (several = validation blocks; results already in "
        "<out>/retrieval are re-read by XRepoSkill's resume, not re-requested, and their recorded "
        "token usage is kept, so spent_usd stays cumulative)",
    )
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--model", default="vertex_ai/gemini-3.1-flash-lite")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    spec = next(
        m
        for m in load_model_specs("configs/models/vertex_gemini.json").values()
        if m.litellm_name == a.model
    )
    head = subprocess.check_output(["git", "-C", str(a.clone), "rev-parse", "HEAD"], text=True)
    if head.strip() != PINNED:
        raise SystemExit(f"XRepoSkill clone at {head.strip()}, expected {PINNED}")
    sys.path.insert(0, str(a.clone / "src"))
    from xreposkill import retrieval  # noqa: PLC0415 (third-party code, pinned and reviewed)
    from xreposkill.config import load_config  # noqa: PLC0415
    from xreposkill.rollout import SKILL_FRAME  # noqa: PLC0415

    strategies = parse_strategies((a.clone / "data" / "general_strategies_36.md").read_text())
    if len(strategies) != 36:
        raise SystemExit(f"parsed {len(strategies)} strategies, expected 36")
    skills_root = a.out / "skills"
    pack(strategies, skills_root)
    cfg = load_config(a.clone / "configs" / "pipeline.yaml")["retrieval"]
    flow = retrieval.RetrievalFlow(
        skills_root=skills_root,
        model=a.model,
        top_n=cfg["top_n"],
        issue_max_chars=cfg["issue_max_chars"],
    )
    if len(flow.rules) != 36:
        raise SystemExit(f"XRepoSkill parsed {len(flow.rules)} rules, expected 36")
    ids: list[str] = []
    for f in a.ids:
        pool = json.loads(f.read_text())
        ids += [i for i in (pool.get("usable") or pool["instances"]) if i not in ids]
    rows = {}
    for line in a.rows.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            rows[r["instance_id"]] = r
    inst = [rows[i] for i in ids]
    # XRepoSkill records an API error and moves on, and its resume re-reads that file: a transient
    # error would silently mark an issue "no rule selected" (not activated) and bias the sample.
    # Errored results are re-run (their file is replaced); any error left stops the experiment.
    for attempt in range(4):
        res = retrieval.run_flow_batch(
            flow=flow, instances=inst, out_dir=a.out / "retrieval", workers=a.workers
        )
        errored = [r["instance_id"] for r in res if r["error"]]
        if not errored:
            break
        print(f"[retry {attempt + 1}] {len(errored)} errored selections", flush=True)
        for iid in errored:
            (a.out / "retrieval" / f"{iid}.json").unlink()
    else:
        raise SystemExit(f"selection errors remain for {errored}; not writing the task set")
    guidance, sel = {}, {}
    for r in sorted(res, key=lambda x: x["instance_id"]):
        rules = [flow.by_id[s["rule_id"]] for s in r["selected"]]
        sel[r["instance_id"]] = {
            "rule_ids": [s["rule_id"] for s in r["selected"]],
            "strategy_numbers": [int(x.tag.split()[-1]) for x in rules],
            "error": r["error"],
            "tokens_in": sum(u.get("in_tokens", 0) for u in r["usage"]),
            "tokens_out": sum(u.get("out_tokens", 0) for u in r["usage"]),
        }
        if rules:
            guidance[r["instance_id"]] = SKILL_FRAME.format(block=retrieval.render_rules(rules))
    (a.out / "guidance_by_instance.json").write_text(json.dumps(guidance, indent=1))
    summary = {
        "_comment": "XRepoSkill rule selection for E2 (rule ids only; the text is not "
        "redistributed: the repository has no LICENSE). docs/preregistration_e2.md",
        "xreposkill_commit": PINNED,
        "model": a.model,
        "top_n": cfg["top_n"],
        "n_tasks": len(sel),
        "n_activated": sum(1 for v in sel.values() if v["rule_ids"]),
        "n_errors": sum(1 for v in sel.values() if v["error"]),
        "tokens_in": sum(v["tokens_in"] for v in sel.values()),
        "tokens_out": sum(v["tokens_out"] for v in sel.values()),
        # part of E2's 45 USD (run_e2.sh subtracts it); priced from configs/models, no caching
        "spent_usd": round(
            estimate_cost_usd(
                spec,
                sum(v["tokens_in"] for v in sel.values()),
                sum(v["tokens_out"] for v in sel.values()),
            ),
            4,
        ),
        "per_task": sel,
    }
    Path("results/e2_selection.json").write_text(json.dumps(summary, indent=1) + "\n")
    print({k: v for k, v in summary.items() if k != "per_task"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
