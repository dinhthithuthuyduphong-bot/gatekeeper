"""Section 19 C (docs/preregistration_main.md; deviation D-M9: E1 only): sham-skill audit.
An LLM auditor sees a failed/passed pair of runs and decides whether a skill caused the failure.
  (i)   real:  skill candidate pairs (target run had the skill loaded);
  (ii)  sham:  A/A placebo pairs presented as if the target run had the skill loaded;
  (iii) plain: the same placebo pairs, no skill mentioned.
Writes results/sham_audit.json (no trajectory text). Paid: one auditor call per pair, hard cap.

  .venv/bin/python scripts/sham_audit.py build                    # prompts -> scratchpad, no calls
  <agent env>/python scripts/sham_audit.py call --model gemini-flash-lite --cap-usd 1.0 [--limit 3]
The build step needs the repo's environment (numpy, scipy); the call step needs only litellm.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

PROMPT = Path("configs/audit_prompt.txt")
MODELS = Path("configs/models/vertex_gemini.json")
ROWS = Path(
    "/tmp/claude-0/-home-user-gatekeeper/cfb16e31-7b52-5c1a-8071-d03b24bd210f/scratchpad/e1_rows.jsonl"
)
TAIL_MESSAGES, TAIL_CHARS, PATCH_CHARS = 30, 80_000, 8_000  # 20,000 tokens at ~4 chars per token
CATS = (
    "task_implementation_fault",
    "artifact_or_verifier_interface_fault",
    "environment_or_runtime_fault",
)


def skill_text(skill: str) -> str:
    return json.loads(Path(f"configs/skills/{skill}.json").read_text())["procedure"]["guidance"]


def collect() -> tuple[list[dict], list[dict]]:
    """Real skill candidate pairs and A/A placebo pairs of E1, with paths to their trajectories."""
    import analyze_g1_final as gf
    import replicate_attribution as ra

    where: dict = {}  # (iid, seed) -> part
    rec: dict = {}
    for f in sorted(glob.glob(ra.STAGE_FILES["e1"])):
        part = Path(f).stem
        s = ra.seed_of(part)
        for skill, v in json.loads(Path(f).read_text())["skills"].items():
            for p in v["pairs"]:
                i = p["instance_id"]
                where[(i, s)] = part
                rec.setdefault(skill, {}).setdefault(i, {})[s] = (
                    gf.resolved(p["loss_with"]),
                    gf.resolved(p["loss_without"]),
                )
    real, placebo, seen = [], [], set()
    for skill in sorted(rec):
        for i, v in sorted(rec[skill].items()):
            if not all(s in v for s in ra.SEEDS):
                continue
            for s in ra.SEEDS:
                if ra.functional(v[s][0], v[s][1]):
                    real.append(
                        {
                            "skill": skill,
                            "iid": i,
                            "target": (where[(i, s)], skill),
                            "ref": (where[(i, s)], "none"),
                        }
                    )
            for a, b in ra.PLACEBO:
                if ra.functional(v[a][1], v[b][1]) and (i, a, b) not in seen:
                    seen.add((i, a, b))
                    placebo.append(
                        {
                            "skill": skill,
                            "iid": i,
                            "target": (where[(i, a)], "none"),
                            "ref": (where[(i, b)], "none"),
                        }
                    )
    return real, placebo


def _traj(part: str, arm: str, iid: str) -> dict:
    return json.loads(Path(f"runs/{part}/{arm}/agent/{iid}/{iid}.traj.json").read_text())


def _patch(part: str, arm: str, iid: str) -> str:
    preds = json.loads(Path(f"runs/{part}/{arm}/agent/preds_scored.json").read_text())
    return (preds.get(iid, {}).get("model_patch") or "(empty patch)")[:PATCH_CHARS]


def _tail(traj: dict) -> str:
    out = []
    for m in traj.get("messages", [])[-TAIL_MESSAGES:]:
        c = m.get("content")
        if isinstance(c, list):
            c = " ".join(x.get("text", "") for x in c if isinstance(x, dict))
        out.append(f"[{m.get('role')}] {c}")
    return "\n".join(out)[-TAIL_CHARS:]


def build_prompt(pair: dict, condition: str, tasks: dict) -> str:
    """Pure given the files: the registered prompt for one pair and condition."""
    tpl = PROMPT.read_text()
    (tp, ta), (rp, rarm) = pair["target"], pair["ref"]
    iid = pair["iid"]
    if condition in ("real", "sham"):
        setup = (
            "The target run was executed with the SKILL below loaded into its prompt; "
            "the reference run had no skill."
        )
        cause, word = "the loaded skill", "skill"
        block = f"=== SKILL LOADED IN THE TARGET RUN ===\n{skill_text(pair['skill'])}\n\n"
    elif condition == "plain":
        setup = "Both runs used the same configuration."
        cause, word, block = "something specific to the target run's setup", "setup", ""
    else:
        raise ValueError(condition)
    return tpl.format(
        setup_sentence=setup,
        cause_phrase=cause,
        cause_word=word,
        skill_block=block,
        task=tasks[iid][:6000],
        target_patch=_patch(tp, ta, iid),
        reference_patch=_patch(rp, rarm, iid),
        target_tail=_tail(_traj(tp, ta, iid)),
    )


def parse(text: str) -> dict | None:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(d.get("attributed"), bool):
        return None
    return {
        "attributed": d["attributed"],
        "confidence": d.get("confidence"),
        "category": d.get("category"),
    }


JOBS = ROWS.parent / "sham_audit_jobs.jsonl"  # scratchpad: contains trajectory text, not committed


def build() -> None:
    rows = [json.loads(line) for line in ROWS.open()]
    tasks = {r["instance_id"]: r["problem_statement"] for r in rows}
    real, placebo = collect()
    jobs = [("real", p) for p in real] + [(c, p) for p in placebo for c in ("sham", "plain")]
    with JOBS.open("w") as f:
        for cond, p in jobs:
            f.write(
                json.dumps({"condition": cond, **p, "prompt": build_prompt(p, cond, tasks)}) + "\n"
            )
    print(f"{len(jobs)} jobs ({len(real)} real, {len(placebo)} placebo pairs) -> {JOBS}")


def call(model: str, cap_usd: float, limit: int | None, tag: str) -> None:
    import litellm  # agent environment

    spec = json.loads(MODELS.read_text())["models"][model]
    jobs = [json.loads(line) for line in JOBS.open()]
    if limit:
        jobs = jobs[:limit]
    spent, out = 0.0, []
    for j in jobs:
        prompt = j["prompt"]
        worst = (
            len(prompt) / 2 / 1e6 * spec["usd_per_mtok_in"] + 2000 / 1e6 * spec["usd_per_mtok_out"]
        )
        if spent + worst > cap_usd:
            print(f"[stop] cap: spent {spent:.4f} + worst {worst:.4f} > {cap_usd}")
            break
        r = litellm.completion(
            model=spec["litellm_name"],
            messages=[{"role": "user", "content": prompt}],
            **spec["kwargs"],
        )
        u = r.usage
        cost = (
            u.prompt_tokens * spec["usd_per_mtok_in"]
            + u.completion_tokens * spec["usd_per_mtok_out"]
        ) / 1e6
        spent += cost
        out.append(
            {k: j[k] for k in ("condition", "skill", "iid", "target", "ref")}
            | {
                "decision": parse(r.choices[0].message.content),
                "tokens_in": u.prompt_tokens,
                "tokens_out": u.completion_tokens,
                "usd": cost,
            }
        )
        print(j["condition"], j["skill"], j["iid"], out[-1]["decision"], f"{spent:.4f}", flush=True)
    res = {
        "model": model,
        "jobs": len(jobs),
        "done": len(out),
        "spent_usd": spent,
        "tokens_in": sum(x["tokens_in"] for x in out),
        "tokens_out": sum(x["tokens_out"] for x in out),
        "rows": out,
    }
    name = ("sham_audit_cost_probe" if limit else "sham_audit") + tag
    Path(f"results/{name}.json").write_text(json.dumps(res, indent=1) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["build", "call"])
    ap.add_argument("--model")
    ap.add_argument("--cap-usd", type=float)
    ap.add_argument("--limit", type=int, default=None, help="first N jobs only (cost measurement)")
    ap.add_argument(
        "--tag", default="", help="suffix of the result file, e.g. _flash (section 19 note 19-2)"
    )
    a = ap.parse_args()
    if a.step == "build":
        build()
    else:
        if not a.model or a.cap_usd is None:
            ap.error("call needs --model and --cap-usd")
        call(a.model, a.cap_usd, a.limit, a.tag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
