import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import memgovern_cell as mc  # noqa: E402

A = 0.025 / 9


def _pair(t, with_ok, without_ok):
    return {
        "instance_id": t,
        "loss_with": 0.0 if with_ok else 1.0,
        "loss_without": 0.0 if without_ok else 1.0,
    }


def _part(d, name, pairs, extra=(), spent=1.0):
    ids = [p["instance_id"] for p in pairs] + list(extra)
    (d / f"{name}.json").write_text(
        json.dumps(
            {"instances": ids, "spent_usd": spent, "skills": {"memgovern": {"pairs": pairs}}}
        )
    )


def test_prefix_order_and_skips(tmp_path):
    order = [f"o__r-{i}" for i in range(6)]
    # shard 0 runs tasks 0, 2, 4; shard 1 runs 1 (no pair: infra) and not yet 3, 5
    _part(tmp_path, "mg-s41-k0-p00", [_pair(order[0], True, False), _pair(order[2], True, False)])
    _part(tmp_path, "mg-s41-k0-p01", [_pair(order[4], True, False)])
    _part(tmp_path, "mg-s41-k1-p00", [], extra=[order[1]])
    out = mc.analyse(order, mc.merged_runs(tmp_path, "mg-s41"), A, 0.0, 0.5, 20.0)
    assert out["n_run"] == 4 and out["prefix_run"] == 3  # task 3 not run: prefix stops there
    assert out["n_trials"] == 2 and out["n_no_pair"] == 1  # tasks 0 and 2; task 1 skipped
    assert out["b_helps"] == 2 and not out["admit"]
    assert math.isclose(out["log_threshold"], math.log(360))


def test_rerun_in_later_part_replaces(tmp_path):
    order = ["o__r-1"]
    _part(tmp_path, "mg-s41-k0-p00", [_pair("o__r-1", False, False)])
    _part(tmp_path, "mg-s41-k0-p01", [_pair("o__r-1", True, False)])
    out = mc.analyse(order, mc.merged_runs(tmp_path, "mg-s41"), A, 0.0, 0.5, 20.0)
    assert out["b_helps"] == 1 and out["n_trials"] == 1


def test_admits_on_strong_benefit_and_cost_stop(tmp_path):
    order = [f"o__r-{i}" for i in range(109)]
    pairs = [_pair(t, True, False) for t in order[:60]]
    _part(tmp_path, "mg-s41-k0-p00", pairs, spent=6.0)
    out = mc.analyse(order, mc.merged_runs(tmp_path, "mg-s41"), A, 0.0, 0.5, 20.0)
    assert out["admit"] and out["crossed_at_trial"] < 60
    # 6 USD for 60 tasks -> 0.1 per task x 49 left = 4.9; 6 + 4.9 > 10 -> stop
    out = mc.analyse(order, mc.merged_runs(tmp_path, "mg-s41"), A, 0.0, 0.5, 10.0)
    assert out["stop_cost"]


def test_no_admit_under_null(tmp_path):
    order = [f"o__r-{i}" for i in range(109)]
    pairs = [_pair(t, i % 2 == 0, i % 2 == 1) for i, t in enumerate(order)]  # mean Z = 0
    _part(tmp_path, "mg-s41-k0-p00", pairs)
    out = mc.analyse(order, mc.merged_runs(tmp_path, "mg-s41"), A, 0.0, 0.5, 20.0)
    assert not out["admit"]


def test_phase_names_are_separate_shards(tmp_path):
    order = ["o__r-1", "o__r-2"]
    _part(tmp_path, "mg-s41-f000-k0-p00", [_pair("o__r-1", True, False)])
    _part(tmp_path, "mg-s41-f001-k0-p00", [_pair("o__r-2", True, True)])
    _part(tmp_path, "mgdry-s41-f000-k0-p00", [_pair("o__r-1", False, False)])  # other prefix
    out = mc.analyse(order, mc.merged_runs(tmp_path, "mg-s41"), A, 0.0, 0.5, 20.0)
    assert out["n_run"] == 2 and out["b_helps"] == 1 and out["n_trials"] == 2


def test_analysis_writes_nothing_outside(tmp_path):
    import run_batched_pilot as rbp

    before = set(rbp.RESULTS.glob("*")) if rbp.RESULTS.exists() else set()
    _part(tmp_path, "mg-s41-f000-k0-p00", [_pair("o__r-1", True, False)])
    mc.merged_runs(tmp_path, "mg-s41")
    after = set(rbp.RESULTS.glob("*")) if rbp.RESULTS.exists() else set()
    assert after == before  # A99
