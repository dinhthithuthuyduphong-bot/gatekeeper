import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "apply_timeout_rule", Path(__file__).parents[1] / "scripts" / "apply_timeout_rule.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

RESOLVED = {"resolved": True, "tests_status": {"FAIL_TO_PASS": {"success": ["t"], "failure": []}}}


def _log(root, rid, iid, text="", report=None):
    d = root / rid / "model" / iid
    d.mkdir(parents=True)
    (d / "run_instance.log").write_text(text)
    if report is not None:
        (d / "report.json").write_text(json.dumps({iid: report}))


def _part():
    return {
        "name": "x-p1",
        "instances": ["a", "b"],
        "exit_status": {"none": {}, "sk": {}},
        "infra_failures": {"none": {"b": m.NO_REPORT}},
        "skills": {"sk": {"pairs": [{"instance_id": "a", "loss_with": 0.0, "loss_without": 0.0}]}},
    }


def test_first_timeout_is_unresolved_even_if_the_rescore_resolved(tmp_path):
    n, s = "x-p1-none-20261103T115546-1", "x-p1-sk-20261103T115136-1"
    _log(tmp_path, n, "a", report=RESOLVED)
    _log(tmp_path, n, "b", "Test timed out after 1800 seconds")
    _log(tmp_path, f"{n}-r1", "b", "Test timed out after 1800 seconds")
    _log(tmp_path, s, "a", "Test timed out after 1800 seconds")
    _log(tmp_path, f"{s}-r1", "a", report=RESOLVED)  # old code would have used this
    _log(tmp_path, s, "b", report=RESOLVED)
    d = _part()
    t = m.apply(d, tmp_path)
    assert t == {"none": ["b"], "sk": ["a"]}
    assert d["infra_failures"] == {}  # b is no longer an infrastructure failure (not re-run)
    pairs = {
        p["instance_id"]: (p["loss_with"], p["loss_without"]) for p in d["skills"]["sk"]["pairs"]
    }
    lt = m.loss_of(dict(m.TEST_TIMED_OUT))[0]
    assert pairs == {"a": (lt, 0.0), "b": (0.0, lt)}
    assert m.apply(d, tmp_path) == {}  # idempotent: new-format file is left alone


def test_no_timeout_changes_nothing(tmp_path):
    _log(tmp_path, "x-p1-none-20261103T115546-1", "a", report=RESOLVED)
    _log(tmp_path, "x-p1-sk-20261103T115136-1", "a", report=RESOLVED)
    d = _part()
    before = json.dumps(d, sort_keys=True)
    assert m.apply(d, tmp_path) == {}
    assert json.dumps(d, sort_keys=True) == before


def test_agent_infra_with_a_timeout_log_stops(tmp_path):
    _log(tmp_path, "x-p1-none-20261103T115546-1", "b", "Test timed out after 1800 seconds")
    _log(tmp_path, "x-p1-sk-20261103T115136-1", "a", report=RESOLVED)
    d = _part()
    d["infra_failures"]["none"]["b"] = "APIError"
    with pytest.raises(SystemExit):
        m.apply(d, tmp_path)
