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
    assert set(specs) == {"gemini-pro", "gemini-flash", "gemini-flash-lite"}
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
    assert u == {
        "tokens_in": 150,
        "tokens_out": 25,
        "tokens_cached": 0,
        "cost_usd": 0.75,
        "api_calls": 2,
    }
    u2 = traj_usage({**traj, "info": {"model_stats": {"instance_cost": 2.0, "api_calls": 7}}})
    assert u2["cost_usd"] == 2.0 and u2["api_calls"] == 7
    assert pair_losses({"a": 0.6, "b": 0.6}, {"b": 0.0, "c": 0.0}) == [("b", 0.0, 0.6)]


def test_pool_ids(tmp_path):
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location(
        "run_pilot", Path(__file__).parents[1] / "scripts" / "run_pilot.py"
    )
    pytest.importorskip("yaml")
    rp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rp)
    p = tmp_path / "summary.json"
    p.write_text(json.dumps({"usable": ["a", "b"], "n_usable": 2}))
    assert rp.pool_ids(str(p)) == ["a", "b"]
    assert rp.pool_ids("") is None
    assert rp.pool_ids(str(tmp_path / "missing.json")) is None


def test_activated_rows():
    import importlib.util
    from pathlib import Path

    pytest.importorskip("yaml")
    spec = importlib.util.spec_from_file_location(
        "run_pilot", Path(__file__).parents[1] / "scripts" / "run_pilot.py"
    )
    rp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rp)
    ng = Skill.load("configs/skills/null-guard.json")
    rows = [
        {
            "instance_id": "a",
            "repo": "r",
            "problem_statement": "foo() returns None instead of an empty list",
        },
        {"instance_id": "b", "repo": "r", "problem_statement": "legend colour is wrong"},
    ]
    assert [r["instance_id"] for r in rp.activated(ng, rows)] == ["a"]
    oracle = Skill.load("configs/skills/oracle-gold.json")  # no predicates: always active
    assert len(rp.activated(oracle, rows)) == 2


def test_cached_pricing_and_registry():
    from gatekeeper.pilot import litellm_registry

    spec = load_model_specs("configs/models/vertex_gemini.json")["gemini-flash"]
    full = estimate_cost_usd(spec, 1_000_000, 0)
    cached = estimate_cost_usd(spec, 1_000_000, 0, tokens_cached=900_000)
    assert cached < full / 5  # cached input is ~10x cheaper
    reg = litellm_registry(spec)[spec.litellm_name]
    assert reg["input_cost_per_token"] == spec.usd_per_mtok_in / 1e6
    assert reg["cache_read_input_token_cost"] == spec.usd_per_mtok_cached / 1e6


def test_positive_control_and_noise_control():
    pos = Skill.load("configs/skills/control-oracle-files.json")
    rows = [
        {
            "instance_id": "a",
            "problem_statement": "Bug",
            "patch": "diff --git a/pkg/m.py b/pkg/m.py\n",
        }
    ]
    assert "pkg/m.py" in arm_rows(rows, pos)[0]["problem_statement"]
    noise = Skill.load("configs/skills/control-none-seed1.json")
    assert arm_rows(rows, noise)[0]["problem_statement"] == "Bug"
    c = arm_config(noise, "vertex_ai/x", {"temperature": 0.0, "seed": 0})
    assert c["model"]["model_kwargs"]["seed"] == 1


def test_usage_summary():
    import importlib.util
    from pathlib import Path

    pytest.importorskip("yaml")
    spec = importlib.util.spec_from_file_location(
        "run_pilot", Path(__file__).parents[1] / "scripts" / "run_pilot.py"
    )
    rp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rp)
    u = {
        "a": {
            "tokens_in": 1000,
            "tokens_cached": 800,
            "tokens_out": 10,
            "cost_usd": 0.2,
            "api_calls": 5,
        },
        "b": {
            "tokens_in": 3000,
            "tokens_cached": 2400,
            "tokens_out": 30,
            "cost_usd": 0.4,
            "api_calls": 7,
        },
        "c": {},
    }
    s = rp.usage_summary(u, {"a": 0.0, "b": 2 / 3})
    assert s["runs"] == 2 and abs(s["usd_per_run"] - 0.3) < 1e-12
    assert s["cached_share"] == 0.8 and s["solve_rate"] == 0.5 and s["api_calls_per_run"] == 6


def test_infra_failures_are_not_scored(tmp_path):
    import importlib.util
    from pathlib import Path

    pytest.importorskip("yaml")
    spec = importlib.util.spec_from_file_location(
        "run_pilot", Path(__file__).parents[1] / "scripts" / "run_pilot.py"
    )
    rp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rp)
    t = tmp_path / "x.traj.json"
    t.write_text(json.dumps({"info": {"exit_status": "CalledProcessError"}}))
    assert rp.is_infra_failure(rp.agent_exit_status(t))
    t.write_text(json.dumps({"info": {"exit_status": "LimitsExceeded"}}))
    assert not rp.is_infra_failure(rp.agent_exit_status(t))
    assert rp.is_infra_failure(rp.agent_exit_status(tmp_path / "missing.json"))
    assert (
        rp.image_name({"instance_id": "a__b-1", "image": "swebench/x:latest"})
        == "docker.io/swebench/x:latest"
    )
    assert rp.image_name({"instance_id": "psf__requests-1"}).endswith("psf_1776_requests-1:latest")
