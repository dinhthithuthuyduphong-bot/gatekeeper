import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from rescore import summarise  # noqa: E402


def test_summary_counts_flips_and_infra(tmp_path):
    out = tmp_path / "r.jsonl"
    recs = [
        {
            "file": "a.json",
            "instance_id": "t1",
            "repeat": 0,
            "orig": True,
            "resolved": True,
            "status": "completed",
        },
        {
            "file": "a.json",
            "instance_id": "t1",
            "repeat": 1,
            "orig": True,
            "resolved": False,
            "status": "completed",
        },
        {
            "file": "a.json",
            "instance_id": "t2",
            "repeat": 0,
            "orig": False,
            "resolved": False,
            "status": "completed",
        },
        {
            "file": "a.json",
            "instance_id": "t3",
            "repeat": 0,
            "orig": False,
            "resolved": None,
            "status": "error: X",
        },
    ]
    out.write_text("".join(json.dumps(r) + "\n" for r in recs))
    s = summarise(out)["a.json"]
    assert s["patches"] == 2 and s["tasks_with_any_flip"] == 1 and s["flipped_tasks"] == ["t1"]
    assert s["infra_not_completed"] == 1 and s["orig_resolved"] == 1


def test_infra_errors_are_not_done(tmp_path):
    from rescore import done_keys

    out = tmp_path / "r.jsonl"
    out.write_text(
        json.dumps({"file": "a", "instance_id": "t", "repeat": 0, "status": "completed"})
        + "\n"
        + json.dumps({"file": "a", "instance_id": "u", "repeat": 0, "status": "error: X"})
        + "\n"
    )
    assert done_keys(out) == {("a", "t", 0)}
