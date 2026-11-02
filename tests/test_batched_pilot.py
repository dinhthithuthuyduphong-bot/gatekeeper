import importlib.util
import json
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "run_batched_pilot", Path(__file__).parents[1] / "scripts" / "run_batched_pilot.py"
)
bp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bp)


def test_resume_by_task_and_cap(tmp_path, monkeypatch):
    res = tmp_path / "results" / "pilot"
    res.mkdir(parents=True)
    monkeypatch.setattr(bp, "RESULTS", res)
    pool = tmp_path / "summary.json"
    pool.write_text(json.dumps({"usable": [f"t{i}" for i in range(7)]}))
    # an earlier run (batch size 4) already finished t0..t3 and spent 1.0 USD
    (res / "g-p00.json").write_text(
        json.dumps(
            {
                "instances": ["t0", "t1", "t2", "t3"],
                "spent_usd": 1.0,
                "skills": {"s": {"pairs": []}},
                "usage": {},
            }
        )
    )
    ran = []

    def fake_run(cmd, **kw):
        class R:
            returncode = 0

        if "scripts/run_pilot.py" in cmd:
            name = cmd[cmd.index("--name") + 1]
            ids = cmd[cmd.index("--instances") + 1].split(",")
            ran.append(ids)
            (res / f"{name}.json").write_text(
                json.dumps(
                    {
                        "instances": ids,
                        "spent_usd": 0.5,
                        "usage": {},
                        "skills": {
                            "s": {
                                "pairs": [
                                    {"instance_id": i, "loss_with": 0.0, "loss_without": 2 / 3}
                                    for i in ids
                                ]
                            }
                        },
                    }
                )
            )
        return R()

    monkeypatch.setattr(bp.subprocess, "run", fake_run)
    monkeypatch.setattr(bp.shutil, "disk_usage", lambda p: type("U", (), {"free": 100e9})())
    argv = [
        "x",
        "--name",
        "g",
        "--model",
        "m",
        "--skills",
        "s.json",
        "--tasks-from",
        str(pool),
        "--dataset-file",
        "d.jsonl",
        "--batch",
        "2",
        "--cap-usd",
        "5",
        "--cost-limit",
        "0.1",
    ]
    monkeypatch.setattr(sys, "argv", argv)
    bp.main()
    assert ran == [["t4", "t5"], ["t6"]]  # resumed by task with the new batch size
    merged = json.loads((res / "g.json").read_text())
    assert merged["merged_from"] == ["g-p00", "g-p01", "g-p02"]
    assert merged["spent_usd"] == 2.0 and len(merged["skills"]["s"]["pairs"]) == 3
    assert bp.pilot_spent_total() == 2.0  # merged file is not double counted


def test_cap_stops_before_overspending(tmp_path, monkeypatch):
    res = tmp_path / "results" / "pilot"
    res.mkdir(parents=True)
    monkeypatch.setattr(bp, "RESULTS", res)
    (res / "old.json").write_text(json.dumps({"spent_usd": 19.9}))
    pool = tmp_path / "summary.json"
    pool.write_text(json.dumps({"usable": ["a", "b"]}))
    called = []
    monkeypatch.setattr(bp.subprocess, "run", lambda cmd, **kw: called.append(cmd))
    monkeypatch.setattr(bp.shutil, "disk_usage", lambda p: type("U", (), {"free": 100e9})())
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "x",
            "--name",
            "g",
            "--model",
            "m",
            "--skills",
            "s.json",
            "--tasks-from",
            str(pool),
            "--dataset-file",
            "d",
            "--cap-usd",
            "20",
        ],
    )
    bp.main()
    assert called == []  # 19.9 + worst batch > 20: nothing is run
