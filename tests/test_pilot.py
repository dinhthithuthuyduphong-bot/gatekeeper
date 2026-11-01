import json

import pytest

from gatekeeper.pilot import (
    NOOP_FILE_COMMAND,
    SUBMIT_COMMAND,
    arm_config,
    arm_rows,
    deterministic_outputs,
    estimate_cost_usd,
    load_model_specs,
    pair_losses,
    traj_usage,
)
from gatekeeper.skill import Skill

ROWS = [{"instance_id": "a__b-1", "problem_statement": "Bug X", "patch": "diff"}]


def test_model_config_is_vertex_gemini():
    specs = load_model_specs("configs/models/vertex_gemini.json")
    assert set(specs) == {"gemini-pro", "gemini-flash"}
    assert all(s.litellm_name.startswith("vertex_ai/gemini") for s in specs.values())
    assert (
        estimate_cost_usd(specs["gemini-pro"], 1_000_000, 0) == specs["gemini-pro"].usd_per_mtok_in
    )


def test_non_vertex_model_is_rejected(tmp_path):
    p = tmp_path / "m.json"
    p.write_text(
        json.dumps(
            {
                "models": {
                    "x": {"litellm_name": "openai/gpt", "usd_per_mtok_in": 1, "usd_per_mtok_out": 1}
                }
            }
        )
    )
    with pytest.raises(ValueError):
        load_model_specs(p)


def test_arm_rows_add_guidance_only_for_skill():
    sk = Skill.load("configs/skills/guidance-reproduce-first.json")
    assert arm_rows(ROWS, None)[0]["problem_statement"] == "Bug X"
    ps = arm_rows(ROWS, sk)[0]["problem_statement"]
    assert ps.startswith("Bug X") and '<skill id="guidance-reproduce-first">' in ps
    assert ROWS[0]["problem_statement"] == "Bug X"  # input not mutated


def test_arm_config_startup_and_model():
    oracle = Skill.load("configs/skills/oracle-gold.json")
    c = arm_config(
        oracle, "vertex_ai/gemini-x", {"temperature": 0.0}, step_limit=10, cost_limit=0.5
    )
    start = c["run"]["env_startup_command"]
    assert start.startswith(NOOP_FILE_COMMAND) and "{{ patch }}" in start
    assert c["agent"] == {"step_limit": 10, "cost_limit": 0.5}
    assert c["model"]["model_name"] == "vertex_ai/gemini-x"
    none = arm_config(
        None, "deterministic", model_class="deterministic", outputs=deterministic_outputs()
    )
    assert none["run"]["env_startup_command"] == NOOP_FILE_COMMAND
    assert none["model"]["outputs"][0]["extra"]["actions"][0]["command"] == SUBMIT_COMMAND
    assert "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT" in SUBMIT_COMMAND


def test_oracle_startup_renders_with_jinja():
    jinja2 = pytest.importorskip("jinja2")
    oracle = Skill.load("configs/skills/oracle-gold.json")
    cmd = arm_config(oracle, "m")["run"]["env_startup_command"]
    out = jinja2.Template(cmd, undefined=jinja2.StrictUndefined).render(**ROWS[0])
    assert "git apply" in out and "\ndiff\n" in out


def test_traj_usage_and_pairing():
    traj = {
        "messages": [
            {"role": "user", "content": "x"},
            {
                "role": "assistant",
                "extra": {
                    "cost": 0.25,
                    "response": {"usage": {"prompt_tokens": 100, "completion_tokens": 20}},
                },
            },
            {
                "role": "assistant",
                "extra": {"cost": 0.5, "usage": {"input_tokens": 50, "output_tokens": 5}},
            },
        ]
    }
    u = traj_usage(traj)
    assert u == {"tokens_in": 150, "tokens_out": 25, "cost_usd": 0.75, "api_calls": 2}
    u2 = traj_usage({**traj, "info": {"model_stats": {"instance_cost": 2.0, "api_calls": 7}}})
    assert u2["cost_usd"] == 2.0 and u2["api_calls"] == 7
    assert pair_losses({"a": 0.6, "b": 0.6}, {"b": 0.0, "c": 0.0}) == [("b", 0.0, 0.6)]
