import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "harness_smoke", Path(__file__).parents[1] / "scripts" / "harness_smoke.py"
)
hs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hs)


def test_loss_of_harness_report():
    rep = {
        "resolved": True,
        "tests_status": {
            "FAIL_TO_PASS": {"success": ["a", "b"], "failure": []},
            "PASS_TO_PASS": {"success": ["c", "d", "e"], "failure": ["f"]},
        },
    }
    loss, info = hs.loss_of(rep)
    assert info["F"] == 0.0 and info["R"] == 0.25
    assert loss == (0 + 0.5 * 0.25) / 1.5


def test_missing_report_means_nothing_fixed():
    loss, info = hs.loss_of(None)
    assert loss == 1 / 1.5 and not info["resolved"]


def test_read_report(tmp_path, monkeypatch):
    d = tmp_path / "logs/run_evaluation/r/gold/x__y-1"
    d.mkdir(parents=True)
    (d / "report.json").write_text('{"x__y-1": {"resolved": true}}')
    monkeypatch.chdir(tmp_path)
    assert hs.read_report("r", "gold", "x__y-1") == {"resolved": True}
    assert hs.read_report("r", "gold", "missing") is None


def test_read_report_searches_other_layouts(tmp_path, monkeypatch):
    d = tmp_path / "logs/run_evaluation/r/some/nested/x__y-2"
    d.mkdir(parents=True)
    (d / "report.json").write_text('{"x__y-2": {"resolved": false}}')
    monkeypatch.chdir(tmp_path)
    assert hs.read_report("r", "gold", "x__y-2") == {"resolved": False}
