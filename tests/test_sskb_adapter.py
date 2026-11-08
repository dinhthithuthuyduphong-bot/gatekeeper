import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import sskb_adapter as sa  # noqa: E402


def test_parse_pytest_matches_their_rule():
    out = "....\n\x1b[1m===== 8 passed, 4 failed, 1 skipped in 2.31s =====\x1b[0m\n"
    r = sa.parse_pytest(out)
    assert (r["passed"], r["failed"], r["skipped"], r["total"]) == (8, 4, 1, 13)
    assert r["pass_rate"] == pytest.approx(8 / 13)
    r = sa.parse_pytest("==== 5 passed, 2 failed, 1 skipped, 38 errors in 1.23s ====")
    assert r["total"] == 46 and r["errors"] == 38
    r = sa.parse_pytest("test_a PASSED\ntest_b FAILED\n")  # fallback without summary line
    assert (r["passed"], r["total"]) == (1, 2)
    assert sa.parse_pytest("nothing")["pass_rate"] is None


def test_strip_cd_like_their_lifecycle():
    assert sa.strip_cd("cd /workspace/viper-configuration && go mod download") == "go mod download"
    assert sa.strip_cd("pip install x") == "pip install x"


def test_task_text_only_skill_arm_has_skill():
    assert sa.task_text("REQ", None) == "REQ"
    t = sa.task_text("REQ", "SKILLDOC")
    assert "SKILLDOC" in t and t.endswith("REQ")


PINNED = Path(
    "/tmp/claude-0/-home-user-gatekeeper/cfb16e31-7b52-5c1a-8071-d03b24bd210f/scratchpad/pilotenv/"
    "lib/python3.11/site-packages/minisweagent/config/benchmarks/swebench.yaml"
)


@pytest.mark.skipif(not PINNED.exists(), reason="agent environment only on the work machine")
def test_adapt_template_on_the_pinned_swebench_config():
    import yaml

    tpl = yaml.safe_load(PINNED.read_text())["agent"]["instance_template"]
    out = sa.adapt_template(tpl, "/workspace/aiohttp")
    assert "non-test files" not in out and "DO NOT MODIFY" not in out and "patch.txt" not in out
    assert "/testbed" not in out and "/workspace/aiohttp" in out
    assert out.count("COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT") == 1
    assert out.rstrip().endswith("</instructions>") or "</instructions>" in out


def test_adapt_template_refuses_unexpected_text():
    with pytest.raises(ValueError):
        sa.adapt_template("unrelated", "/x")


def test_probe_plan_is_balanced_and_interleaved():
    import run_sskb as rs

    c = rs.cells(rs.PLANS["probe"])
    assert len(c) == 2 * 10 * 1 * 2
    assert c[:4] == [
        ("viper-configuration", 1, 41, "none"),
        ("viper-configuration", 1, 41, "skill"),
        ("asyncio-patterns", 1, 41, "none"),
        ("asyncio-patterns", 1, 41, "skill"),
    ]


@pytest.fixture
def vertex_env(monkeypatch):
    for v in ("VERTEXAI_PROJECT", "VERTEXAI_LOCATION", "GOOGLE_APPLICATION_CREDENTIALS"):
        monkeypatch.setenv(v, "x")


def test_model_config_refuses_without_credentials(tmp_path, monkeypatch):
    monkeypatch.delenv("VERTEXAI_PROJECT", raising=False)
    with pytest.raises(SystemExit):
        sa.model_config("gemini-flash", 41, tmp_path)


def test_model_config_flash_lite_equals_section22_setting(tmp_path, vertex_env):
    import json

    c = sa.model_config("gemini-flash-lite", 41, tmp_path)
    assert c["model_kwargs"] == {"seed": 41, "drop_params": True, "parallel_tool_calls": True}
    reg = json.loads(Path(c["litellm_model_registry"]).read_text())
    # runs/ is local raw data, absent in CI (raw-archive: archive/g1-e1-s41/g1-e1-s41-p00.tar.gz):
    # compare with the pinned copy, and check the copy against the original wherever the original
    # exists (A112m; same fix as trial's A88)
    e1 = json.loads((Path(__file__).parent / "fixtures" / "e1_litellm_registry.json").read_text())
    if sa.E1_REGISTRY.exists():
        assert json.loads(sa.E1_REGISTRY.read_text()) == e1
    assert reg.keys() == e1.keys()
    for k, v in e1.items():
        for f, x in v.items():
            assert reg[k][f] == pytest.approx(x)


def test_model_config_flash_keeps_registered_reasoning_effort(tmp_path, vertex_env):
    import json

    c = sa.model_config("gemini-flash", 51, tmp_path)
    assert c["model_kwargs"]["reasoning_effort"] == "low"
    assert c["model_kwargs"]["seed"] == 51
    reg = json.loads(Path(c["litellm_model_registry"]).read_text())
    assert reg[c["model_name"]]["input_cost_per_token"] == pytest.approx(0.75e-6)
    with pytest.raises(ValueError):
        sa.model_config("gemini-flash", 0, tmp_path)


def _rows(skills, diffs_by_skill, seed=41):
    rows = []
    for sk in skills:
        for b in range(1, 11):
            rows.append({"skill": sk, "batch": b, "seed": seed, "arm": "none", "pass_rate": 0.5})
            rows.append(
                {
                    "skill": sk,
                    "batch": b,
                    "seed": seed,
                    "arm": "skill",
                    "pass_rate": 0.5 + diffs_by_skill[sk],
                }
            )
    return rows


def test_s23_plans_registered_models_and_groups():
    import run_sskb as rs

    assert rs.PLANS["s23a"]["model"] == "gemini-flash"
    assert len(rs.cells(rs.PLANS["s23a"])) == 40
    assert len(rs.cells(rs.PLANS["s23b-screen"])) == 100
    assert rs.PLANS["s23b-screen"]["group"] == rs.PLANS["s23b-confirm"]["group"]
    assert not set(rs.S23B_SKILLS) & {"viper-configuration", "asyncio-patterns"}


def test_select_confirm_picks_largest_abs_effect_with_sign():
    import run_sskb as rs

    sk = rs.S23B_SKILLS
    d = dict(zip(sk, [0.05, -0.20, 0.10, 0.0, 0.15], strict=True))
    assert rs.select_confirm(_rows(sk, d), sk, 10) == ("langsmith-fetch", -1)
    tie = dict(zip(sk, [0.1, -0.1, 0.0, 0.0, 0.0], strict=True))
    assert rs.select_confirm(_rows(sk, tie), sk, 10) == ("go-fx-di", 1)


def test_select_confirm_refuses_incomplete_screen():
    import run_sskb as rs

    sk = rs.S23B_SKILLS
    rows = _rows(sk, dict.fromkeys(sk, 0.0))
    rows = [
        r for r in rows if not (r["skill"] == sk[2] and r["batch"] == 7 and r["arm"] == "skill")
    ]
    with pytest.raises(SystemExit):
        rs.select_confirm(rows, sk, 10)


def test_health_stop_rules():
    import run_sskb as rs

    ok = {"n_calls": 30, "cost_usd": 0.03, "exit_status": "Submitted"}
    assert rs.health_stop(ok, 1, 0) is None
    assert "cost 0" in rs.health_stop({**ok, "cost_usd": 0.0}, 1, 0)
    assert "unreachable" in rs.health_stop({**ok, "exit_status": "APIConnectionError"}, 1, 0)
    assert rs.health_stop({"infra_error": "x"}, 3, 1) is None
    assert "infra" in rs.health_stop({"infra_error": "x"}, 5, 1)


def test_dm11_plans():
    import run_sskb as rs

    assert rs.PLANS["s23a-pro"]["model"] == "gemini-pro"
    assert len(rs.cells(rs.PLANS["s23b-flash-screen"])) == 60
    assert rs.PLANS["s23b-flash-confirm"]["seeds"] == [51]
    g = {p for p, v in rs.PLANS.items() if v["group"] == "s23b-flash"}
    assert g == {"s23b-flash-screen", "s23b-flash-confirm"}
    sk = rs.S23B_SKILLS
    rows = [r for r in _rows(sk, dict.fromkeys(sk, 0.0)) if r["batch"] <= 6]
    assert rs.select_confirm(rows, sk, 6)[0] == sk[0]
