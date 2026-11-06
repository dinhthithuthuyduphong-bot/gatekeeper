import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


f0 = _load("f0_scorer_check")

BUG = (
    "diff --git a/tests/test_x.py b/tests/test_x.py\n--- a/tests/test_x.py\n+++ b/tests/test_x.py\n"
    "@@ -1 +1 @@\n-a\n+b\n"
    "diff --git a/src/jinja2/lexer.py b/src/jinja2/lexer.py\n--- a/src/jinja2/lexer.py\n"
    "+++ b/src/jinja2/lexer.py\n@@ -1 +1 @@\n-x = 1\n+x = 2\n"
)


def test_first_source_file_skips_tests():
    pytest.importorskip("unidiff")
    assert f0.first_source_file(BUG) == "src/jinja2/lexer.py"


def test_wilson_bounds():
    lo, hi = f0.wilson(0, 100, 1.959963984540054)
    assert lo == pytest.approx(0.0, abs=1e-12) and 0.03 < hi < 0.04
    lo, hi = f0.wilson(100, 100, 1.959963984540054)
    assert hi == 1.0 and 0.96 < lo < 0.97


def test_summarise_counts_and_excludes_infra():
    rows = [
        {
            "L_noop": {"passed": True},
            "S_noop": {"resolved": False},
            "L_gold": {"passed": True},
            "S_gold": {"resolved": True},
        },
        {"infra_error": "x"},
    ]
    s = f0.summarise(rows)
    assert s["n_scored"] == 1 and s["infra_errors"] == 1
    assert s["noop"]["L_pass"] == 1 and s["noop"]["S_resolved"] == 0
    assert s["gold"]["S_rate"] == 1.0


def test_f1_config_sets_only_registered_fields(tmp_path):
    pytest.importorskip("yaml")
    sys.modules.pop("f1_probe", None)
    f1 = _load("f1_probe")
    src = tmp_path / "mini.yaml"
    src.write_text(
        "agent:\n  system_template: s\n  cost_limit: 3.\n  step_limit: 0.\n"
        "model:\n  model_kwargs: {}\n"
    )
    out = f1.make_config(src, tmp_path / "o.yaml", 0.3, {"seed": 41})
    import yaml

    cfg = yaml.safe_load(out.read_text())
    assert cfg["agent"]["cost_limit"] == 0.3 and cfg["agent"]["system_template"] == "s"
    assert cfg["agent"]["step_limit"] == 0.0  # run_agent overrides to 50 itself
    assert cfg["model"]["model_kwargs"] == {"seed": 41}


def test_tool_failures_are_infra_not_scores():
    assert f0.infra_reason({"passed": False}, {"status": "error", "resolved": False})
    nf = {"passed": False, "status": "f2p_failed", "f2p_tail": "Test output file not found - x"}
    assert f0.infra_reason(nf, {"status": "completed", "resolved": False})
    real = {"passed": False, "status": "f2p_failed", "f2p_tail": "FAILED tests/test_a.py::t"}
    assert f0.infra_reason(real, {"status": "completed", "resolved": False}) is None
