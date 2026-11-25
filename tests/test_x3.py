import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import x3_analyse as xa  # noqa: E402
import x3_build as xb  # noqa: E402


def _run(iid, resolved, msg, diff, tests=False, restored=False, revert=False):
    return {
        "instance_id": iid,
        "resolved_S": resolved,
        "seen_bug_msg": msg,
        "bug_diff_shown": diff,
        "deleted_tests_shown": tests,
        "tests_restored_and_run": restored,
        "exact_revert": revert,
    }


def _setup():
    audit = {
        "runs": {
            "s27_trace34": {"runs": [_run("a", True, True, True, revert=True)]},
            "s27_trace34b": {"runs": []},
            "s33_ship_skill": {"runs": [_run("b", False, True, False)]},
            "s35_ship_skill": {"runs": [_run("c", True, False, False, restored=True)]},
        }
    }
    key = {
        "codes": {
            "T001": {"stem": "s33_ship_skill", "instance_id": "b"},
            "T002": {"stem": "s27_trace34", "instance_id": "a"},
            "T003": {"stem": "s35_ship_skill", "instance_id": "c"},
        }
    }
    return audit, key


def test_tables_and_disagreements():
    audit, key = _setup()
    labels = {
        "T001": {"q1": "yes", "q2": "yes", "q3": "no", "q4": "no"},  # q2 disagrees
        "T002": {"q1": "yes", "q2": "yes", "q3": "no", "q4": "yes"},
        "T003": {"q1": "no", "q2": "no", "q3": "yes", "q4": "na"},
    }
    assert xa.validate(labels, key["codes"]) == []
    out = xa.analyse(labels, key, audit)
    assert out["tables"]["q2"] == {
        "human_yes_detector_yes": 1,
        "human_yes_detector_no": 1,
        "human_no_detector_yes": 0,
        "human_no_detector_no": 1,
        "agree": 2,
        "n": 3,
    }
    assert out["tables"]["q3"]["agree"] == 3  # restored-and-run counts as the detector's Q3
    assert out["tables_resolved"]["q2"]["n"] == 2
    assert out["paper_counts"]["resolved_with_q2"] == {"human": 1, "detector": 1, "resolved": 2}
    assert [(d["code"], d["question"]) for d in out["disagreements"]] == [("T001", "q2")]
    assert out["q4"]["by_exact_revert"]["yes"] == {"True": 1}


def test_validate_rejects_bad_labels():
    _, key = _setup()
    bad = {
        "T001": {"q1": "yes", "q2": "no", "q3": "no", "q4": "yes"},  # q4 must be na
        "T002": {"q1": "maybe", "q2": "yes", "q3": "no", "q4": "yes"},
    }
    errs = xa.validate(bad, key["codes"])
    assert any("missing" in e for e in errs)
    assert any("T001" in e for e in errs)
    assert any("T002 q1" in e for e in errs)


def test_blind_is_a_fixed_permutation_without_ids(tmp_path):
    items = [
        {
            "stem": "s",
            "instance_id": f"i{k}",
            "messages": [],
            "agent_patch": "",
            "bug_patch": "",
            "f2p": [],
        }
        for k in range(10)
    ]
    b1, k1 = xb.blind(items, 4901)
    b2, k2 = xb.blind(items, 4901)
    assert k1 == k2 and len(b1) == 10
    assert sorted(v["instance_id"] for v in k1.values()) == [f"i{k}" for k in range(10)]
    text = json.dumps(b1)
    assert "instance_id" not in text and '"stem"' not in text


def test_audit_runs_as_lists():
    """results/history_audit.json keeps each stem's runs as a plain list (A151)."""
    audit, key = _setup()
    audit = {"runs": {k: v["runs"] for k, v in audit["runs"].items()}}
    labels = {
        "T001": {"q1": "yes", "q2": "no", "q3": "no", "q4": "na"},
        "T002": {"q1": "yes", "q2": "yes", "q3": "no", "q4": "yes"},
        "T003": {"q1": "no", "q2": "no", "q3": "yes", "q4": "na"},
    }
    out = xa.analyse(labels, key, audit)
    assert out["n"] == 3 and out["tables"]["q2"]["agree"] == 3
