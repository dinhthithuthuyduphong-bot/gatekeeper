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
    from gatekeeper.pilot import PREEXISTING_COMMAND

    # dry run: record pre-existing untracked files first (audit A36), then the no-op file
    assert none["run"]["env_startup_command"] == f"{PREEXISTING_COMMAND} && {NOOP_FILE_COMMAND}"
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
    c = arm_config(noise, "vertex_ai/x", {"temperature": 0.0, "seed": 1})
    assert c["model"]["model_kwargs"]["seed"] == 2
    c7 = arm_config(noise, "vertex_ai/x", {"seed": 7})  # replicate with run seed 7
    assert c7["model"]["model_kwargs"]["seed"] == 8


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


def test_score_arm_rescores_and_flags_harness_infra(tmp_path, monkeypatch):
    import importlib.util
    from pathlib import Path

    pytest.importorskip("yaml")
    spec = importlib.util.spec_from_file_location(
        "run_pilot", Path(__file__).parents[1] / "scripts" / "run_pilot.py"
    )
    rp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rp)
    (tmp_path / "preds.json").write_text(
        json.dumps(
            {
                "ok": {"model_patch": "diff --git a/x b/x"},
                "flaky": {"model_patch": "diff --git a/y b/y"},
                "dead": {"model_patch": "diff --git a/z b/z"},
                "empty": {"model_patch": ""},
            }
        )
    )
    calls = []
    good = {"resolved": True}

    def fake_run(preds, ids, run_id, workers, dataset):
        calls.append((run_id, sorted(ids)))

    def fake_read(run_id, model, iid):
        if iid == "ok":
            return good
        if iid == "flaky" and run_id.endswith("-r1"):
            return good  # report only on the re-score
        return None  # "dead" never gets a report, "empty" was skipped by the harness

    monkeypatch.setattr(rp, "run_harness", fake_run)
    monkeypatch.setattr(rp, "read_report", fake_read)
    r = rp.score_arm(tmp_path, ["ok", "flaky", "dead", "empty"], "run", 1, "ds.jsonl")
    assert r["ok"] is good and r["flaky"] is good
    assert r["dead"] is rp.HARNESS_INFRA  # excluded, never scored as unsolved
    assert r["empty"] is None  # agent did not submit: legitimately unsolved
    assert calls == [("run", ["dead", "empty", "flaky", "ok"]), ("run-r1", ["dead", "flaky"])]


def test_seed_zero_is_rejected():
    """Vertex AI drops seed=0 (unseeded sampling) while seed>=1 is deterministic (stage B bug)."""
    with pytest.raises(ValueError):
        arm_config(None, "vertex_ai/x", {"seed": 0})
    assert arm_config(None, "vertex_ai/x", {"seed": 1})["model"]["model_kwargs"]["seed"] == 1
    specs = load_model_specs("configs/models/vertex_gemini.json")
    for spec in specs.values():  # every configured model can actually build an arm
        arm_config(None, spec.litellm_name, spec.kwargs)


def test_strong_control_template_and_test_file_stripping():
    from gatekeeper.patches import drop_files, touched_files
    from gatekeeper.pilot import fill_template

    row = {
        "patch": "diff --git a/pkg/m.py b/pkg/m.py\n--- a/pkg/m.py\n+++ b/pkg/m.py\n"
        "@@ -1,2 +1,2 @@ def run(x):\n-    return x\n+    return x + 1\n",
        "FAIL_TO_PASS": '["tests/test_m.py::test_run"]',
        "test_patch": "diff --git a/tests/test_m.py b/tests/test_m.py\nnew file mode 100644\n",
    }
    s = fill_template("{files}|{functions}|{tests}|{test_patch}", row)
    assert "pkg/m.py|run (pkg/m.py)|- tests/test_m.py::test_run|diff --git a/tests" in s
    model = (
        "diff --git a/pkg/m.py b/pkg/m.py\n+fix\n"
        "diff --git a/tests/test_m.py b/tests/test_m.py\n+copied test\n"
    )
    out = drop_files(model, touched_files(row["test_patch"]))
    assert "pkg/m.py" in out and "tests/test_m.py" not in out
    assert drop_files(model, set()) == model


def test_pull_via_mirror_tags_docker_io_name(monkeypatch):
    import importlib.util
    from pathlib import Path

    pytest.importorskip("yaml")
    spec = importlib.util.spec_from_file_location(
        "run_pilot", Path(__file__).parents[1] / "scripts" / "run_pilot.py"
    )
    rp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rp)
    calls = []

    def fake(cmd, **kw):
        calls.append(cmd)
        return type("R", (), {"returncode": 0})()

    monkeypatch.setattr(rp.subprocess, "run", fake)
    assert rp.pull_via_mirror("docker.io/swebench/x:latest")
    assert ["docker", "pull", "-q", "mirror.gcr.io/swebench/x:latest"] in calls
    assert [
        "docker",
        "tag",
        "mirror.gcr.io/swebench/x:latest",
        "docker.io/swebench/x:latest",
    ] in calls
    assert not rp.pull_via_mirror("ghcr.io/other/x:latest")


def test_prepull_reports_full_disk(monkeypatch):
    import importlib.util
    from pathlib import Path

    pytest.importorskip("yaml")
    spec = importlib.util.spec_from_file_location(
        "run_pilot", Path(__file__).parents[1] / "scripts" / "run_pilot.py"
    )
    rp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rp)

    def fake(cmd, **kw):
        rc = 1  # nothing local, every pull fails
        err = "write ...: no space left on device"
        return type("R", (), {"returncode": rc, "stderr": err})()

    monkeypatch.setattr(rp.subprocess, "run", fake)
    failed = rp.prepull([{"instance_id": "a__b-1"}], tries=3)
    assert failed and rp._NO_SPACE


def test_scoring_run_id_is_unique_per_attempt():
    import importlib.util
    from pathlib import Path

    pytest.importorskip("yaml")
    spec = importlib.util.spec_from_file_location(
        "run_pilot", Path(__file__).parents[1] / "scripts" / "run_pilot.py"
    )
    rp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rp)
    a = rp.scoring_run_id("g1-c-s31-p05", "none")
    assert a.startswith("g1-c-s31-p05-none-") and a != "g1-c-s31-p05-none"


def test_per_instance_guidance_prepended(tmp_path):
    import json as _json

    from gatekeeper.skill import Skill as _Skill

    gfile = tmp_path / "g.json"
    gfile.write_text(_json.dumps({"a": "RULE A"}))
    sk = _Skill.from_dict(
        {
            "schema_version": 1,
            "id": "third-party",
            "procedure": {
                "kind": "guidance",
                "guidance_by_instance_file": str(gfile),
                "position": "prepend",
            },
            "fingerprints": {},
            "input_predicates": [],
            "postconditions": [],
            "footprint": {"regions": [], "reads": [], "writes": [], "properties": []},
            "capability_verdict": "approved",
            "source": "test",
        }
    )
    out = arm_rows(
        [
            {"instance_id": "a", "problem_statement": "Bug"},
            {"instance_id": "b", "problem_statement": "Bug"},
        ],
        sk,
    )
    assert out[0]["problem_statement"].startswith('<skill id="third-party">\nRULE A')
    assert out[0]["problem_statement"].endswith("Bug") and out[1]["problem_statement"] == "Bug"


def test_unwrapped_guidance_is_verbatim(tmp_path):
    import json as _json

    from gatekeeper.skill import Skill as _Skill

    gfile = tmp_path / "g.json"
    gfile.write_text(_json.dumps({"a": "<relevant_skills>\nR\n</relevant_skills>\n"}))
    sk = _Skill.from_dict(
        {
            "schema_version": 1,
            "id": "xreposkill",
            "procedure": {
                "kind": "guidance",
                "guidance_by_instance_file": str(gfile),
                "position": "prepend",
                "wrap": False,
            },
            "fingerprints": {},
            "input_predicates": [],
            "postconditions": [],
            "footprint": {"regions": [], "reads": [], "writes": [], "properties": []},
            "capability_verdict": "approved",
            "source": "test",
        }
    )
    out = arm_rows([{"instance_id": "a", "problem_statement": "Bug"}], sk)
    assert out[0]["problem_statement"] == "<relevant_skills>\nR\n</relevant_skills>\n\nBug"
    assert "<skill" not in out[0]["problem_statement"]


def test_repeated_format_error_is_agent_behaviour():
    import sys as _sys
    from pathlib import Path as _P

    _sys.path.insert(0, str(_P(__file__).parents[1] / "scripts"))
    import run_pilot as rp

    assert not rp.is_infra_failure("RepeatedFormatError")
    assert not rp.is_infra_failure("LimitsExceeded")
    assert rp.is_infra_failure(None) and rp.is_infra_failure("APIError")


def test_dry_run_records_preexisting_untracked_files_only():
    from gatekeeper.pilot import PREEXISTING_COMMAND, arm_config, deterministic_outputs

    dry = arm_config(None, "deterministic", outputs=deterministic_outputs())
    real = arm_config(None, "vertex_ai/x", {"seed": 1})
    assert dry["run"]["env_startup_command"].startswith(PREEXISTING_COMMAND)
    assert PREEXISTING_COMMAND not in real["run"]["env_startup_command"]  # real agents unchanged


def test_score_arm_classifies_timeouts_and_apply_failures_without_rescoring(tmp_path, monkeypatch):
    import json as _json
    import sys as _sys
    from pathlib import Path as _P

    _sys.path.insert(0, str(_P(__file__).parents[1] / "scripts"))
    import run_pilot as rp

    monkeypatch.chdir(tmp_path)
    agent = tmp_path / "agent"
    agent.mkdir()
    ids = ["o__r-1", "o__r-2", "o__r-3"]
    (agent / "preds.json").write_text(_json.dumps({i: {"model_patch": "diff x"} for i in ids}))
    calls = []

    def fake_harness(preds, todo, run_id, workers, dataset, **kw):
        calls.append((run_id, list(todo)))
        for i, msg in (
            ("o__r-1", "Test timed out after 1800 seconds"),
            ("o__r-2", ">>>>> Patch Apply Failed"),
        ):
            if i in todo:
                d = tmp_path / "logs/run_evaluation" / run_id / "m" / i
                d.mkdir(parents=True)
                (d / "run_instance.log").write_text(f"INFO - {msg}\n")

    monkeypatch.setattr(rp, "run_harness", fake_harness)
    monkeypatch.setattr(rp, "read_report", lambda run_id, model, iid: None)
    rep = rp.score_arm(agent, ids, "rid", 1, "ds", retries=1)
    assert rep["o__r-1"].get("_test_timeout") and rep["o__r-2"].get("_apply_failed")
    assert rep["o__r-3"] == rp.HARNESS_INFRA
    assert calls == [("rid", ids), ("rid-r1", ["o__r-3"])]  # only the unexplained one re-scored


def test_oracle_patch_control_leaks_patch_not_test_patch():
    sk = Skill.load("configs/skills/control-oracle-patch.json")
    row = {
        "instance_id": "a__b-1",
        "problem_statement": "Bug X",
        "patch": (
            "diff --git a/src/m.py b/src/m.py\n--- a/src/m.py\n+++ b/src/m.py\n"
            "@@ -1 +1 @@ def f():\n-x\n+GOLDLINE\n"
        ),
        "test_patch": "diff --git a/tests/t.py b/tests/t.py\n+TESTONLYLINE\n",
        "FAIL_TO_PASS": '["tests/t.py::test_a"]',
    }
    ps = arm_rows([row], sk)[0]["problem_statement"]
    assert "GOLDLINE" in ps and ps.count("GOLDLINE") == 1
    assert "{gold_patch}" not in ps and "Bug X" in ps
