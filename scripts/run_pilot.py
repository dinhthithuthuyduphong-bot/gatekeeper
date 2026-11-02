"""Paired-trial pilot: mini-swe-agent (Gemini on Vertex AI) x SWE-bench Verified x skills.

For every arm ("none" + each skill) the same instances are solved by the agent, the patches are
scored by the official harness, and per-instance losses give paired differences Z per skill.
Outputs results/pilot/<name>.json and a resumable trial log runs/<name>/trials.jsonl.

  # free dry run (no LLM): scripted model + oracle skill, expected Z = -0.667
  python scripts/run_pilot.py --name dryrun --model deterministic \
      --skills configs/skills/oracle-gold.json --instances psf__requests-1142,pallets__flask-5014

  # paid run (needs VERTEXAI_PROJECT, VERTEXAI_LOCATION, GOOGLE_APPLICATION_CREDENTIALS)
  python scripts/run_pilot.py --name r15-a --model gemini-flash --n 30 --budget-usd 40 \
      --skills configs/skills/guidance-reproduce-first.json

Budget guard: refuses to start when (#arms x #instances x per-instance cost_limit) exceeds
--budget-usd, and stops between arms once the measured cost reaches it.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

from gatekeeper.analysis import variance_components
from gatekeeper.eprocess import run_admission
from gatekeeper.harness import DATASET, loss_of, read_report, run_harness
from gatekeeper.pilot import (
    arm_config,
    arm_rows,
    deterministic_outputs,
    estimate_cost_usd,
    litellm_registry,
    load_model_specs,
    pair_losses,
    traj_usage,
)
from gatekeeper.runlog import ResumableLog, TrialRecord
from gatekeeper.skill import Skill

MODELS_FILE = Path("configs/models/vertex_gemini.json")


def pool_ids(pool: str) -> list[str] | None:
    """Usable task ids from results/pool_validation/<tag>/summary.json (or a configs/pools file)."""
    if not pool or not Path(pool).exists():
        return None
    d = json.loads(Path(pool).read_text())
    return list(d.get("usable") or d.get("instances") or [])


def load_instances(
    ids: list[str] | None, n: int, seed: int, allowed: list[str] | None = None
) -> list[dict]:
    from datasets import load_dataset

    rows = list(load_dataset(DATASET, split="test"))
    if allowed is not None:
        keep = set(allowed)
        rows = [r for r in rows if r["instance_id"] in keep]
        if len(rows) < n and not ids:
            raise SystemExit(f"pool has only {len(rows)} usable tasks, --n {n} requested")
    if ids:
        by_id = {r["instance_id"]: r for r in rows}
        missing = [i for i in ids if i not in by_id]
        if missing:
            raise SystemExit(f"unknown instance ids: {missing}")
        return [by_id[i] for i in ids]
    rng = random.Random(seed)
    return rng.sample(rows, n)


def activated(skill: Skill, rows: list[dict]) -> list[dict]:
    """Rows where the skill's input predicates hold on the issue text (no fingerprints here)."""
    from gatekeeper.scope import TargetContext, screen

    return [
        r
        for r in rows
        if screen(
            skill,
            TargetContext(
                name=r["repo"], fingerprints={}, issue_text=r.get("problem_statement", "")
            ),
        ).in_scope
    ]


def usage_summary(u: dict[str, dict], loss: dict[str, float]) -> dict:
    """Per-arm calibration numbers: cost and tokens per agent run, cache hit share, solve rate."""
    runs = [v for v in u.values() if v]
    n = len(runs)
    tin = sum(int(v.get("tokens_in", 0)) for v in runs)
    tc = sum(int(v.get("tokens_cached", 0)) for v in runs)
    return {
        "runs": n,
        "usd_per_run": sum(float(v.get("cost_usd", 0.0)) for v in runs) / n if n else None,
        "tokens_in_per_run": tin / n if n else None,
        "tokens_out_per_run": sum(int(v.get("tokens_out", 0)) for v in runs) / n if n else None,
        "cached_share": tc / tin if tin else None,
        "api_calls_per_run": sum(int(v.get("api_calls", 0)) for v in runs) / n if n else None,
        "solve_rate": sum(1 for x in loss.values() if x == 0.0) / len(loss) if loss else None,
    }


def image_digest(instance_id: str) -> str:
    name = "docker.io/swebench/sweb.eval.x86_64." + instance_id.replace("__", "_1776_").lower()
    try:
        out = subprocess.run(
            [
                "docker",
                "image",
                "inspect",
                "--format",
                "{{index .RepoDigests 0}}",
                name + ":latest",
            ],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
    except FileNotFoundError:
        out = ""
    return out.split("@", 1)[1] if "@sha256:" in out else "sha256:unknown"


def run_arm(arm: str, skill: Skill | None, rows: list[dict], args, out_dir: Path, model) -> Path:
    arm_dir = out_dir / arm
    ds_dir = arm_dir / "dataset"
    ds_dir.mkdir(parents=True, exist_ok=True)
    with (ds_dir / "data.jsonl").open("w", encoding="utf-8") as fh:
        for r in arm_rows(rows, skill):
            fh.write(json.dumps(r, default=str) + "\n")
    if model is None:  # deterministic dry run
        overlay = arm_config(
            skill, "deterministic", model_class="deterministic", outputs=deterministic_outputs()
        )
    else:
        overlay = arm_config(
            skill,
            model.litellm_name,
            model.kwargs,
            step_limit=args.step_limit,
            cost_limit=args.cost_limit,
        )
    (arm_dir / "overlay.yaml").write_text(yaml.safe_dump(overlay, sort_keys=False))
    from minisweagent.config import builtin_config_dir

    base = builtin_config_dir / "benchmarks" / "swebench.yaml"
    agent_dir = arm_dir / "agent"
    cmd = [
        "mini-extra",
        "swebench",
        "--subset",
        str(ds_dir),
        "--split",
        "train",
        "-o",
        str(agent_dir),
        "-w",
        str(args.workers),
        "-c",
        str(base),
        "-c",
        str(arm_dir / "overlay.yaml"),
    ]
    print("+", " ".join(cmd), flush=True)
    env = dict(os.environ)
    if model is None:
        env["MSWEA_COST_TRACKING"] = "ignore_errors"  # the scripted model has no price
    else:
        # register our prices so the per-instance cost_limit is enforced, and fail loudly rather
        # than silently counting 0 USD if a cost cannot be computed
        reg = out_dir / "litellm_registry.json"
        reg.write_text(json.dumps(litellm_registry(model), indent=2))
        env["LITELLM_MODEL_REGISTRY_PATH"] = str(reg.resolve())
        env["MSWEA_COST_TRACKING"] = "default"
    rc = subprocess.run(cmd, check=False, env=env).returncode
    if rc != 0:
        raise SystemExit(f"mini-swe-agent failed for arm {arm} (exit {rc})")
    return agent_dir


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument(
        "--model", required=True, help="'deterministic' or a key of " + str(MODELS_FILE)
    )
    ap.add_argument("--skills", required=True, help="comma-separated skill JSON files")
    ap.add_argument("--instances", default="")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument(
        "--no-activation",
        dest="activation",
        action="store_false",
        help="run every skill on every task (ignore issue_regex activation predicates)",
    )
    ap.add_argument(
        "--pool",
        default="",
        help="sample only from validated tasks (results/pool_validation/<tag>/summary.json)",
    )
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--step-limit", type=int, default=60)
    ap.add_argument("--cost-limit", type=float, default=1.0, help="USD per instance per arm")
    ap.add_argument("--budget-usd", type=float, default=0.0)
    ap.add_argument("--theta", type=float, default=0.05)
    ap.add_argument("--alpha", type=float, default=0.05)
    a = ap.parse_args()

    skills = [Skill.load(p) for p in a.skills.split(",") if p]
    model = None if a.model == "deterministic" else load_model_specs(MODELS_FILE)[a.model]
    if model is not None:
        for v in ("VERTEXAI_PROJECT", "VERTEXAI_LOCATION"):
            if not os.environ.get(v):
                raise SystemExit(f"{v} is not set (Vertex AI); see docs/vertex_setup.md")
    ids = [i for i in a.instances.split(",") if i] or None
    rows = load_instances(ids, a.n, a.seed, pool_ids(a.pool))
    arms: list[tuple[str, Skill | None]] = [("none", None)] + [(s.id, s) for s in skills]
    # P_s = tasks where the skill's activation predicates I(x) hold (corrections.md §1.2):
    # a skill arm only runs on its activated tasks; the no-skill arm runs on their union.
    arm_rows_map = {sid: activated(sk, rows) for sid, sk in arms if sk is not None}
    union = {r["instance_id"] for rs in arm_rows_map.values() for r in rs}
    arm_rows_map["none"] = [r for r in rows if r["instance_id"] in union] if a.activation else rows
    if not a.activation:
        arm_rows_map = {sid: rows for sid, _ in arms}
    for sid, rs in arm_rows_map.items():
        print(f"arm {sid}: {len(rs)} tasks", flush=True)
    arms = [(sid, sk) for sid, sk in arms if arm_rows_map[sid]]
    worst = sum(len(arm_rows_map[sid]) for sid, _ in arms) * (a.cost_limit if model else 0.0)
    if model is not None and worst > a.budget_usd:
        raise SystemExit(
            f"worst-case cost {worst:.2f} USD > --budget-usd {a.budget_usd:.2f}; "
            "lower --n / --cost-limit or raise the budget"
        )

    out_dir = Path("runs") / a.name
    out_dir.mkdir(parents=True, exist_ok=True)
    log = ResumableLog(out_dir / "trials.jsonl")
    losses: dict[str, dict[str, float]] = {}
    usage: dict[str, dict[str, dict]] = {}
    spent = 0.0
    for arm, skill in arms:
        rows_arm = arm_rows_map[arm]
        agent_dir = run_arm(arm, skill, rows_arm, a, out_dir, model)
        run_harness(
            str(agent_dir / "preds.json"),
            [r["instance_id"] for r in rows_arm],
            f"{a.name}-{arm}",
            a.workers,
        )
        losses[arm], usage[arm] = {}, {}
        for r in rows_arm:
            iid = r["instance_id"]
            losses[arm][iid], _ = loss_of(read_report(f"{a.name}-{arm}", "", iid))
            traj = agent_dir / iid / f"{iid}.traj.json"
            u = traj_usage(json.loads(traj.read_text())) if traj.exists() else {}
            usage[arm][iid] = u
            if model is not None and u and not u.get("cost_usd"):
                u["cost_usd"] = estimate_cost_usd(
                    model, int(u["tokens_in"]), int(u["tokens_out"]), int(u.get("tokens_cached", 0))
                )
            spent += float(u.get("cost_usd", 0.0)) if model else 0.0
        if model is not None and spent >= a.budget_usd:
            print(f"budget reached after arm {arm}: {spent:.2f} USD", flush=True)
            break

    today = date.today().isoformat()
    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "name": a.name,
        "model": a.model if model is None else model.litellm_name,
        "dataset": DATASET,
        "instances": [r["instance_id"] for r in rows],
        "theta": a.theta,
        "alpha": a.alpha,
        "spent_usd": round(spent, 4),
        "usage": {arm: usage_summary(usage[arm], losses[arm]) for arm in losses},
        "skills": {},
    }
    for arm, _skill in arms[1:]:
        if arm not in losses:
            continue
        pairs = pair_losses(losses["none"], losses[arm])
        for iid, lw, lo in pairs:
            u_w, u_o = usage[arm].get(iid, {}), usage["none"].get(iid, {})
            r = next(x for x in rows if x["instance_id"] == iid)
            log.append(
                TrialRecord(
                    key=f"{a.name}/{arm}/{iid}/{a.seed}",
                    system="pilot",
                    cell=f"{arm}@verified",
                    task_id=iid,
                    seed=a.seed,
                    loss_with=lw,
                    loss_without=lo,
                    model_id=summary["model"],
                    model_access_date=today,
                    image_digest=image_digest(iid),
                    repo_commit=r.get("base_commit", "unknown"),
                    tokens_in=int(u_w.get("tokens_in", 0)) + int(u_o.get("tokens_in", 0)),
                    tokens_out=int(u_w.get("tokens_out", 0)) + int(u_o.get("tokens_out", 0)),
                    cost_usd=float(u_w.get("cost_usd", 0.0)) + float(u_o.get("cost_usd", 0.0)),
                )
            )
        z = [lw - lo for _, lw, lo in pairs]
        dec = run_admission(z, a.theta, a.alpha, budget=len(z))
        summary["skills"][arm] = {
            "pairs": [
                {"instance_id": i, "loss_with": lw, "loss_without": lo} for i, lw, lo in pairs
            ],
            "mean_Z": sum(z) / len(z) if z else None,
            "variance_components": variance_components(pairs) if len(pairs) >= 3 else None,
            "eprocess": {"admitted": dec.admitted, "n": dec.n_trials, "log_e": dec.log_e},
        }
        print(
            f"[{arm}] n={len(z)} mean Z={summary['skills'][arm]['mean_Z']} admitted={dec.admitted}"
        )
    Path("results/pilot").mkdir(parents=True, exist_ok=True)
    out = Path("results/pilot") / f"{a.name}.json"
    out.write_text(json.dumps(summary, indent=2) + "\n")
    print("wrote", out, "spent", summary["spent_usd"], "USD")
    return 0


if __name__ == "__main__":
    sys.exit(main())
