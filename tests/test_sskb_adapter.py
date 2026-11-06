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
