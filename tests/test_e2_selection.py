import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "make_e2_selection", Path(__file__).parents[1] / "scripts" / "make_e2_selection.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

POOL = {"random_order": ["c", "a", "b", "d"]}


def sel(**rules):
    return {"per_task": {k: {"rule_ids": v, "error": ""} for k, v in rules.items()}}


def test_keeps_random_order_and_only_activated_usable():
    s = sel(a=["r1"], b=[], c=["r2"], d=["r3"])
    out = m.build(POOL, {"a", "b", "c"}, s, {"a": "G", "c": "G"})
    assert out == ["c", "a"]  # pool order; b has no rule; d is not usable


def test_stops_on_missing_or_errored_selection():
    with pytest.raises(SystemExit):
        m.build(POOL, {"a", "b"}, sel(a=["r1"]), {"a": "G"})
    s = sel(a=["r1"], b=["r2"])
    s["per_task"]["b"]["error"] = "APIError"
    with pytest.raises(SystemExit):
        m.build(POOL, {"a", "b"}, s, {"a": "G", "b": "G"})


def test_stops_when_an_activated_task_has_no_guidance_text():
    with pytest.raises(SystemExit):
        m.build(POOL, {"a"}, sel(a=["r1"]), {"a": "  "})


def test_blocks_must_be_a_prefix_of_the_random_order():
    assert m.validated_prefix(["c", "a", "b", "d"], [["a", "c"], ["b"]]) == 3
    with pytest.raises(SystemExit):  # skips "b"
        m.validated_prefix(["c", "a", "b", "d"], [["a", "c"], ["d"]])
    with pytest.raises(SystemExit):  # duplicate
        m.validated_prefix(["c", "a", "b", "d"], [["a", "c"], ["c"]])


def test_first_n_keeps_order_and_stops_when_short():
    assert m.first_n(["c", "a", "d"], 2) == ["c", "a"]
    with pytest.raises(SystemExit):
        m.first_n(["c"], 2)
