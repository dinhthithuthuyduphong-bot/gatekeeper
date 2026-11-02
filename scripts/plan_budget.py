"""Plan a fixed Vertex AI budget across the G1 pilot stages (docs/budget_200.md).

Cost per agent run is unknown until Stage A measures it, so the plan is computed for scenarios:
steps per run x share of input tokens served from Gemini's cache. Input tokens per run follow
the agent's growing context: sum_{i<=S} (P + h*i) with prompt P and history growth h per step.

Usage: python scripts/plan_budget.py [--budget 200] [--reserve 0.10] [--usd-per-run X]
Writes results/budget_plan.json.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from gatekeeper.pilot import estimate_cost_usd, load_model_specs

PROMPT_TOK, HIST_TOK, OUT_TOK = 3_000, 1_500, 300  # per step (assumptions, replaced by Stage A)
STEPS = (20, 30, 45)
CACHE = (0.0, 0.8)
SIGMA2 = {"SWE-Skills-Bench (0.04)": 0.04, "binary worst case (0.25)": 0.25}

STAGE_A_RUNS = 8  # 4 tasks x (none, positive control)
STAGE_B_ARMS = 3  # none, none-seed1 (noise), positive control
SKILLS_C = 4


def run_cost(spec, steps: int, cache: float) -> float:
    tin = sum(PROMPT_TOK + HIST_TOK * i for i in range(1, steps + 1))
    return estimate_cost_usd(spec, tin, OUT_TOK * steps, int(cache * tin))


def plan(budget: float, reserve: float, usd_per_run: float) -> dict:
    usable = budget * (1 - reserve)
    a = STAGE_A_RUNS * usd_per_run
    rest = max(usable - a, 0.0)
    b_budget, c_budget = 0.25 * rest, 0.75 * rest
    n_b = int(b_budget / (STAGE_B_ARMS * usd_per_run))
    # stage C: union of activated tasks gets the no-skill arm once; assume union ~= 0.8 * sum
    per_skill = int(c_budget / (usd_per_run * SKILLS_C * 1.8))
    per_skill = min(per_skill, 30)
    return {
        "usd_per_run": round(usd_per_run, 4),
        "stage_A": {"runs": STAGE_A_RUNS, "usd": round(a, 2)},
        "stage_B": {
            "tasks": n_b,
            "runs": n_b * STAGE_B_ARMS,
            "usd": round(n_b * STAGE_B_ARMS * usd_per_run, 2),
        },
        "stage_C": {
            "skills": SKILLS_C,
            "tasks_per_skill": per_skill,
            "runs": int(per_skill * SKILLS_C * 1.8),
            "usd": round(per_skill * SKILLS_C * 1.8 * usd_per_run, 2),
        },
        "ci_halfwidth_per_skill": {
            k: (round(1.96 * math.sqrt(v / per_skill), 3) if per_skill else None)
            for k, v in SIGMA2.items()
        },
        "total_runs_possible": int(usable / usd_per_run),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=float, default=200.0)
    ap.add_argument("--reserve", type=float, default=0.10)
    ap.add_argument("--usd-per-run", type=float, default=0.0, help="measured cost (Stage A)")
    a = ap.parse_args()
    specs = load_model_specs("configs/models/vertex_gemini.json")
    scenarios = []
    if a.usd_per_run:
        scenarios.append(
            {
                "model": "measured",
                "steps": None,
                "cache": None,
                **plan(a.budget, a.reserve, a.usd_per_run),
            }
        )
    else:
        for key in ("gemini-flash-lite", "gemini-flash", "gemini-pro"):
            for steps in STEPS:
                for cache in CACHE:
                    c = run_cost(specs[key], steps, cache)
                    scenarios.append(
                        {
                            "model": key,
                            "steps": steps,
                            "cache": cache,
                            **plan(a.budget, a.reserve, c),
                        }
                    )
    for s in scenarios:
        print(
            f"{s['model']:<18} steps={s['steps']!s:>4} cache={s['cache']!s:>4} "
            f"{s['usd_per_run']:6.3f}$/run "
            f"runs={s['total_runs_possible']:>5}  B tasks={s['stage_B']['tasks']:>3}  "
            f"C/skill={s['stage_C']['tasks_per_skill']:>3}  CI±={s['ci_halfwidth_per_skill']}"
        )
    out = {
        "budget": a.budget,
        "reserve": a.reserve,
        "assumptions": {
            "prompt_tokens": PROMPT_TOK,
            "history_tokens_per_step": HIST_TOK,
            "output_tokens_per_step": OUT_TOK,
            "prices_from": "configs/models/vertex_gemini.json",
        },
        "scenarios": scenarios,
    }
    Path("results").mkdir(exist_ok=True)
    Path("results/budget_plan.json").write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    main()
