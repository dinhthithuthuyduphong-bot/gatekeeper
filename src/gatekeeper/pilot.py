"""Paired-trial pilot on SWE-bench Verified with mini-swe-agent (TODO.md Phase 2-3, R15).

Pure-Python helpers (no Docker, no LLM) used by scripts/run_pilot.py:

* arm datasets: one local JSONL per arm ("none" or a skill id). A skill acts through
  - procedure["guidance"]: procedural text appended to the issue (prompt-level skill), and/or
  - procedure["startup"]: shell edit program run in the task container before the agent starts
    (mini-swe-agent `run.env_startup_command`, Jinja-rendered with the instance fields).
* arm configs: mini-swe-agent config overlays (model, limits, startup command).
* pairing: per-instance losses of the two arms -> paired differences Z.
* model registry: Gemini on Vertex AI via LiteLLM (`vertex_ai/<model-id>`), with a price table
  used for our own budget guard (prices change: keep configs/models/vertex_gemini.json current).
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gatekeeper.skill import Skill

__all__ = [
    "NOOP_FILE_COMMAND",
    "ModelSpec",
    "arm_config",
    "arm_rows",
    "deterministic_outputs",
    "estimate_cost_usd",
    "load_model_specs",
    "pair_losses",
    "traj_usage",
]

# Same idea as scripts/harness_smoke.py: an empty patch is skipped by the harness, so every arm
# adds one unrelated file; the harness then really evaluates the "no change" arm.
NOOP_FILE_COMMAND = "cd /testbed && echo noop > .gatekeeper_noop"
SUBMIT_COMMAND = (
    "cd /testbed && git add -A && git diff --cached > /tmp/gk_patch.txt && "
    "echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat /tmp/gk_patch.txt"
)


@dataclass(frozen=True)
class ModelSpec:
    key: str  # short name used in configs, e.g. "gemini-pro"
    litellm_name: str  # e.g. "vertex_ai/gemini-3.1-pro"
    usd_per_mtok_in: float
    usd_per_mtok_out: float
    kwargs: Mapping[str, Any]


def load_model_specs(path: str | Path) -> dict[str, ModelSpec]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    out = {}
    for key, m in raw["models"].items():
        if not m["litellm_name"].startswith("vertex_ai/"):
            raise ValueError(f"{key}: Gemini must be called through Vertex AI ('vertex_ai/...')")
        out[key] = ModelSpec(
            key=key,
            litellm_name=m["litellm_name"],
            usd_per_mtok_in=float(m["usd_per_mtok_in"]),
            usd_per_mtok_out=float(m["usd_per_mtok_out"]),
            kwargs=dict(m.get("kwargs", {})),
        )
    return out


def estimate_cost_usd(spec: ModelSpec, tokens_in: int, tokens_out: int) -> float:
    return (tokens_in * spec.usd_per_mtok_in + tokens_out * spec.usd_per_mtok_out) / 1e6


def arm_rows(rows: Iterable[Mapping[str, Any]], skill: Skill | None) -> list[dict]:
    """Rows of the arm dataset: identical tasks, the skill's guidance appended to the issue."""
    out = []
    guidance = (skill.procedure.get("guidance") or "").strip() if skill else ""
    for r in rows:
        row = dict(r)
        if guidance:
            row["problem_statement"] = (
                f'{r["problem_statement"]}\n\n<skill id="{skill.id}">\n{guidance}\n</skill>'
            )
        out.append(row)
    return out


def arm_config(
    skill: Skill | None,
    model_name: str,
    model_kwargs: Mapping[str, Any] | None = None,
    model_class: str | None = None,
    step_limit: int = 60,
    cost_limit: float = 1.0,
    outputs: list[dict] | None = None,
) -> dict:
    """mini-swe-agent config overlay for one arm (merged on top of benchmarks/swebench.yaml)."""
    startup = [NOOP_FILE_COMMAND]
    if skill and skill.procedure.get("startup"):
        startup.append(str(skill.procedure["startup"]))
    model: dict[str, Any] = {"model_name": model_name, "model_kwargs": dict(model_kwargs or {})}
    if model_class:
        model["model_class"] = model_class
    if outputs is not None:
        model["outputs"] = outputs
    return {
        "agent": {"step_limit": step_limit, "cost_limit": cost_limit},
        "run": {"env_startup_command": " && ".join(startup)},
        "model": model,
    }


def deterministic_outputs() -> list[dict]:
    """Scripted 'model' for the free dry run: stage whatever the startup edit program changed
    and submit it. Lets CI exercise mini-swe-agent + Docker + harness without any LLM call."""
    return [
        {
            "role": "assistant",
            "content": "THOUGHT: submit the current changes.",
            "extra": {"actions": [{"command": SUBMIT_COMMAND}], "cost": 0.0},
        }
    ]


def traj_usage(traj: Mapping[str, Any]) -> dict[str, float]:
    """Best-effort token / cost / call counts from a mini-swe-agent trajectory file."""
    tin = tout = 0
    cost = 0.0
    calls = 0
    for m in traj.get("messages", []):
        if m.get("role") != "assistant":
            continue
        calls += 1
        extra = m.get("extra") or {}
        cost += float(extra.get("cost") or 0.0)
        usage = (extra.get("response") or {}).get("usage") or extra.get("usage") or {}
        tin += int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
        tout += int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
    info = traj.get("info") or {}
    stats = info.get("model_stats") or {}
    if stats:
        cost = float(stats.get("instance_cost", cost))
        calls = int(stats.get("api_calls", calls))
    return {"tokens_in": tin, "tokens_out": tout, "cost_usd": cost, "api_calls": calls}


def pair_losses(
    none_losses: Mapping[str, float], skill_losses: Mapping[str, float]
) -> list[tuple[str, float, float]]:
    """(instance_id, loss_with, loss_without) for instances evaluated in both arms."""
    common = sorted(set(none_losses) & set(skill_losses))
    return [(i, float(skill_losses[i]), float(none_losses[i])) for i in common]
