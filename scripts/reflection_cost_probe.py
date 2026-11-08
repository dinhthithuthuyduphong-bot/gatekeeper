"""Section 25 step 2, cost probe (cap 1 USD): what does one gskill reflection call cost?

Faithful to gskill at gepa@8c7b697:
  1. gskill's fitness function (create_swe_fitness_fn) runs the agent with empty skills on the
     first n training tasks (gskill split, _gskill_order) -> (score, side_info) per task;
  2. the reflective dataset is built as OptimizeAnythingAdapter.make_reflective_dataset does
     ("scores" renamed to "Scores (Higher is Better)", *_specific_info merged or dropped);
  3. gskill's LoggingProposer is called once with the reflection model, with gskill's own LM
     settings (no extra kwargs: gskill passes none).
Costs are summed per model from LiteLLM's response_cost. Prints operational fields only.
"""

from __future__ import annotations

import argparse
import gzip
import json
import threading
from collections import defaultdict
from pathlib import Path

_cost: dict[str, float] = defaultdict(float)
_tok: dict[str, list[int]] = defaultdict(lambda: [0, 0])
_lock = threading.Lock()


def _track(kwargs, response, start, end):
    m = kwargs.get("model", "?")
    u = getattr(response, "usage", None)
    with _lock:
        _cost[m] += float(kwargs.get("response_cost") or 0.0)
        if u is not None:
            _tok[m][0] += int(getattr(u, "prompt_tokens", 0) or 0)
            _tok[m][1] += int(getattr(u, "completion_tokens", 0) or 0)


def reflective_item(side_info: dict, component: str) -> dict:
    """OptimizeAnythingAdapter.make_reflective_dataset for one example (gepa@8c7b697)."""
    out: dict = {}
    for k, v in side_info.items():
        if k == "scores":
            out["Scores (Higher is Better)"] = v
        elif not k.endswith("_specific_info"):
            out[k] = v
        elif k == f"{component}_specific_info":
            out.update(v)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    for k in (
        "--rows",
        "--model",
        "--reflection-model",
        "--registry",
        "--out",
        "--run-dir",
        "--gskill-yaml",
    ):
        ap.add_argument(k, required=True)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--cap", type=float, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--cost-limit", type=float, required=True)
    a = ap.parse_args()
    if a.seed == 0:
        raise SystemExit("seed 0 means 'no seed' on Vertex (A14)")

    import litellm
    from f1_probe import make_config
    from gskill.swe_fitness_fn import create_swe_fitness_fn
    from gskill.train_optimize_anything import LoggingProposer

    litellm.register_model(json.loads(Path(a.registry).read_text()))
    litellm.success_callback = [_track]
    raw = Path(a.rows).read_bytes()
    text = (gzip.decompress(raw) if a.rows.endswith(".gz") else raw).decode("utf-8")
    rows = [json.loads(x) for x in text.splitlines() if x.strip()]
    train = sorted(
        (r for r in rows if r["_gskill_split"] == "train"), key=lambda r: r["_gskill_order"]
    )

    # same agent config as F1 (registered): gskill's mini.yaml with cost_limit and model_kwargs set
    kwargs = {"seed": a.seed, "drop_params": True, "parallel_tool_calls": True}
    cfg = make_config(
        Path(a.gskill_yaml), Path(a.out).with_suffix(".mini.yaml"), a.cost_limit, kwargs
    )
    fitness = create_swe_fitness_fn(model_name=a.model, n_workers=1, config_path=str(cfg))
    items, scores = [], []
    for task in train[: a.n]:
        if sum(_cost.values()) + a.cost_limit > a.cap:
            raise SystemExit("cap reached before the reflection call")
        score, side_info = fitness({"skills": ""}, task)
        scores.append(score)
        items.append(reflective_item(side_info, "skills"))
        print(f"rollout {len(items)} cost so far {sum(_cost.values()):.4f}", flush=True)
    agent_cost = sum(_cost.values())

    Path(a.run_dir).mkdir(parents=True, exist_ok=True)
    prop = LoggingProposer(Path(a.run_dir), a.reflection_model)
    prompt_chars = len(prop.format_prompt("", json.dumps(items, indent=2, default=str)))
    if agent_cost > a.cap:
        raise SystemExit("cap reached before the reflection call")
    new = prop({"skills": ""}, {"skills": items}, ["skills"])
    out = {
        "model": a.model,
        "reflection_model": a.reflection_model,
        "n_rollouts": len(items),
        "lenient_scores": scores,
        "agent_cost_usd": agent_cost,
        "reflection_cost_usd": sum(_cost.values()) - agent_cost,
        "per_model_cost_usd": dict(_cost),
        "per_model_tokens_in_out": {k: v for k, v in _tok.items()},
        "reflection_prompt_chars": prompt_chars,
        "new_skills_chars": len(new.get("skills", "")),
    }
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
    print(
        json.dumps(
            {
                k: out[k]
                for k in ("agent_cost_usd", "reflection_cost_usd", "reflection_prompt_chars")
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
