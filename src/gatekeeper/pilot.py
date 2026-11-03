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
    "litellm_registry",
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
    usd_per_mtok_cached: float | None = None  # cached input tokens (None = billed as input)


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
            usd_per_mtok_cached=(
                float(m["usd_per_mtok_cached"])
                if m.get("usd_per_mtok_cached") is not None
                else None
            ),
        )
    return out


def estimate_cost_usd(
    spec: ModelSpec, tokens_in: int, tokens_out: int, tokens_cached: int = 0
) -> float:
    """tokens_in includes cached tokens; cached ones are billed at the cached rate if known."""
    cached_rate = (
        spec.usd_per_mtok_cached if spec.usd_per_mtok_cached is not None else spec.usd_per_mtok_in
    )
    fresh = max(tokens_in - tokens_cached, 0)
    return (
        fresh * spec.usd_per_mtok_in
        + tokens_cached * cached_rate
        + tokens_out * spec.usd_per_mtok_out
    ) / 1e6


def litellm_registry(spec: ModelSpec) -> dict[str, dict[str, Any]]:
    """Price entry for litellm.register_model, so mini-swe-agent's per-instance cost_limit works
    even when LiteLLM's bundled table lacks the model (otherwise cost = 0: the limit is inert)."""
    entry: dict[str, Any] = {
        "input_cost_per_token": spec.usd_per_mtok_in / 1e6,
        "output_cost_per_token": spec.usd_per_mtok_out / 1e6,
        "litellm_provider": "vertex_ai",
        "mode": "chat",
        "supports_function_calling": True,
        "max_input_tokens": 1_048_576,
    }
    if spec.usd_per_mtok_cached is not None:
        entry["cache_read_input_token_cost"] = spec.usd_per_mtok_cached / 1e6
    return {spec.litellm_name: entry}


def _test_list(v: Any) -> list[str]:
    if isinstance(v, str):
        import ast

        try:
            v = json.loads(v)
        except ValueError:
            v = ast.literal_eval(v) if v.strip().startswith("[") else [v]
    return [str(x) for x in (v or [])]


def _truncate(s: str, n: int) -> str:
    return s if len(s) <= n else s[:n] + "\n... (truncated)"


def fill_template(template: str, row: Mapping[str, Any], max_items: int = 5) -> str:
    """Fill {files}, {functions}, {tests}, {test_patch} from the gold patch and FAIL_TO_PASS.
    Only for controls: these placeholders leak the answer's location (never an evaluated skill)."""
    from gatekeeper.patches import parse_patch

    pp = parse_patch(row.get("patch") or "")
    fns = sorted(f.split("::", 1)[1] + " (" + f.split("::", 1)[0] + ")" for f in pp.functions)
    tests = _test_list(row.get("FAIL_TO_PASS"))
    vals = {
        "{files}": ", ".join(pp.files) or "(unknown)",
        "{functions}": ", ".join(fns[:max_items]) or "(not identifiable from the patch)",
        "{tests}": "\n".join("- " + x for x in tests[:max_items]) or "(none listed)",
        "{test_patch}": _truncate(row.get("test_patch") or "", 4000) or "(no test patch)",
    }
    for k, v in vals.items():
        template = template.replace(k, v)
    return template


def arm_rows(rows: Iterable[Mapping[str, Any]], skill: Skill | None) -> list[dict]:
    """Rows of the arm dataset: identical tasks plus the skill's guidance.

    procedure keys: "guidance" (same text for every task), "guidance_template" (filled per task),
    "guidance_by_instance_file" (JSON {instance_id: text}, e.g. rules selected per issue by a
    third-party system; tasks without an entry get no guidance), "position": "append" (default,
    after the issue) or "prepend" (above the issue, as XRepoSkill injects its rules), "wrap": false
    to insert the text verbatim (a third-party system's own framing) instead of in <skill> tags."""
    out = []
    proc = skill.procedure if skill else {}
    guidance = (proc.get("guidance") or "").strip()
    template = (proc.get("guidance_template") or "").strip()
    by_inst: dict[str, str] = {}
    if proc.get("guidance_by_instance_file"):
        by_inst = json.loads(Path(proc["guidance_by_instance_file"]).read_text())
    prepend = proc.get("position", "append") == "prepend"
    wrap = proc.get("wrap", True)
    for r in rows:
        row = dict(r)
        g = guidance
        if template:  # per-instance guidance, e.g. the positive control leaking the gold patch
            g = fill_template(template, r)
        if by_inst:
            g = (by_inst.get(r["instance_id"]) or "").strip()
        if g:
            block = f'<skill id="{skill.id}">\n{g}\n</skill>' if wrap else g
            row["problem_statement"] = (
                f"{block}\n\n{r['problem_statement']}"
                if prepend
                else f"{r['problem_statement']}\n\n{block}"
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
    kwargs = dict(model_kwargs or {})
    if skill and skill.procedure.get("model_kwargs"):  # e.g. a different seed for a noise control
        kwargs.update(skill.procedure["model_kwargs"])
    if skill and skill.procedure.get("seed_offset"):  # noise control relative to the run's seed
        kwargs["seed"] = int(kwargs.get("seed", 0)) + int(skill.procedure["seed_offset"])
    if "seed" in kwargs and int(kwargs["seed"]) == 0:
        # Vertex AI drops seed=0 (proto3 default) -> unseeded sampling, while seed>=1 is
        # deterministic: arms would differ in HOW they sample, not only in the skill (stage B bug).
        raise ValueError("seed 0 means 'unset' on Vertex AI; use seeds >= 1")
    model: dict[str, Any] = {"model_name": model_name, "model_kwargs": kwargs}
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
    tin = tout = tcached = 0
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
        details = usage.get("prompt_tokens_details") or {}
        tcached += int(details.get("cached_tokens") or usage.get("cache_read_input_tokens") or 0)
    info = traj.get("info") or {}
    stats = info.get("model_stats") or {}
    if stats:
        cost = float(stats.get("instance_cost", cost))
        calls = int(stats.get("api_calls", calls))
    return {
        "tokens_in": tin,
        "tokens_out": tout,
        "tokens_cached": tcached,
        "cost_usd": cost,
        "api_calls": calls,
    }


def pair_losses(
    none_losses: Mapping[str, float], skill_losses: Mapping[str, float]
) -> list[tuple[str, float, float]]:
    """(instance_id, loss_with, loss_without) for instances evaluated in both arms."""
    common = sorted(set(none_losses) & set(skill_losses))
    return [(i, float(skill_losses[i]), float(none_losses[i])) for i in common]
