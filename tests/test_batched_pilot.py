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
    (res / "old.json").write_text(json.dumps({"instances": ["z"], "spent_usd": 19.9}))
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


def test_spend_ignores_analysis_files_and_merge_counts(tmp_path, monkeypatch):
    res = tmp_path / "pilot"
    (res / "invalid").mkdir(parents=True)
    monkeypatch.setattr(bp, "RESULTS", res)
    part = {
        "instances": ["a", "b"],
        "spent_usd": 0.5,
        "skills": {"s": {"pairs": [{"instance_id": "a", "loss_with": 0.0, "loss_without": 1.0}]}},
        "usage": {"none": {"runs": 2, "usd_per_run": 0.1, "solved": 1, "scored": 2}},
    }
    (res / "g-p00.json").write_text(json.dumps(part))
    (res / "invalid" / "old.json").write_text(json.dumps({**part, "spent_usd": 1.0}))
    # analysis output carries spent_usd too, but no instances: must not be double counted
    (res / "invalid" / "g1_decision.json").write_text(json.dumps({"spent_usd": 3.0}))
    assert bp.pilot_spent_total() == 1.5
    m = bp.merge("g", [res / "g-p00.json"])
    assert m["usage"]["none"]["solved"] == 1 and m["usage"]["none"]["scored"] == 2
    assert bp.pilot_spent_total() == 1.5  # merged file not counted either


def test_infra_failed_tasks_are_rerun_and_replaced(tmp_path, monkeypatch):
    res = tmp_path / "pilot"
    res.mkdir()
    monkeypatch.setattr(bp, "RESULTS", res)

    def pair(i, lw):
        return {"instance_id": i, "loss_with": lw, "loss_without": 0.5}

    (res / "g-p00.json").write_text(
        json.dumps(
            {
                "instances": ["a", "b"],
                "spent_usd": 0.1,
                "infra_failures": {"s": {"b": "harness"}},
                "skills": {"s": {"pairs": [pair("a", 0.0)]}, "t": {"pairs": [pair("b", 1.0)]}},
            }
        )
    )
    assert bp.done_tasks([res / "g-p00.json"]) == {"a"}  # b is re-run
    (res / "g-p01.json").write_text(
        json.dumps(
            {
                "instances": ["b"],
                "spent_usd": 0.1,
                "skills": {"s": {"pairs": [pair("b", 0.0)]}, "t": {"pairs": [pair("b", 0.0)]}},
            }
        )
    )
    m = bp.merge("g", [res / "g-p00.json", res / "g-p01.json"])
    assert m["instances"] == ["a", "b"]
    assert sorted(p["instance_id"] for p in m["skills"]["t"]["pairs"]) == ["b"]  # no duplicate
    assert m["skills"]["t"]["pairs"][0]["loss_with"] == 0.0  # latest part wins
    assert m["skills"]["s"]["n"] == 2 and not m["infra_failures"]["s"]


def test_registry_limit_waits_and_retries(tmp_path, monkeypatch):
    res = tmp_path / "pilot"
    res.mkdir()
    monkeypatch.setattr(bp, "RESULTS", res)
    pool = tmp_path / "summary.json"
    pool.write_text(json.dumps({"usable": ["a"]}))
    calls = []

    def fake_run(cmd, **kw):
        class R:
            returncode = 0

        if "scripts/run_pilot.py" in cmd:
            calls.append(cmd)
            if len(calls) == 1:
                R.returncode = bp.EX_TEMPFAIL  # first attempt: images not pullable
            else:
                name = cmd[cmd.index("--name") + 1]
                (res / f"{name}.json").write_text(
                    json.dumps({"instances": ["a"], "spent_usd": 0.0, "skills": {}})
                )
        return R()

    monkeypatch.setattr(bp.subprocess, "run", fake_run)
    monkeypatch.setattr(bp.time, "sleep", lambda s: None)
    monkeypatch.setattr(bp.shutil, "disk_usage", lambda p: type("U", (), {"free": 100e9})())
    argv = ["x", "--name", "g", "--model", "m", "--skills", "s.json", "--tasks-from", str(pool)]
    monkeypatch.setattr(sys, "argv", argv + ["--dataset-file", "d"])
    bp.main()
    assert len(calls) == 2 and (res / "g-p00.json").exists()


def test_stops_cleanly_when_time_is_short(tmp_path, monkeypatch):
    res = tmp_path / "pilot"
    res.mkdir()
    monkeypatch.setattr(bp, "RESULTS", res)
    pool = tmp_path / "summary.json"
    pool.write_text(json.dumps({"usable": ["a", "b"]}))
    called = []
    monkeypatch.setattr(bp.subprocess, "run", lambda cmd, **kw: called.append(cmd))
    monkeypatch.setattr(bp.shutil, "disk_usage", lambda p: type("U", (), {"free": 100e9})())
    argv = ["x", "--name", "g", "--model", "m", "--skills", "s.json", "--tasks-from", str(pool)]
    argv += ["--dataset-file", "d", "--stop-after-min", "10", "--batch-min", "25"]
    monkeypatch.setattr(sys, "argv", argv)
    bp.main()
    assert called == []  # less time left than one batch: nothing started


def test_full_disk_halves_the_batch(tmp_path, monkeypatch):
    res = tmp_path / "pilot"
    res.mkdir()
    monkeypatch.setattr(bp, "RESULTS", res)
    pool = tmp_path / "summary.json"
    pool.write_text(json.dumps({"usable": ["a", "b", "c", "d"]}))
    sizes = []

    def fake_run(cmd, **kw):
        class R:
            returncode = 0

        if "scripts/run_pilot.py" in cmd:
            ids = cmd[cmd.index("--instances") + 1].split(",")
            sizes.append(len(ids))
            if len(ids) > 2:
                R.returncode = bp.EX_NOSPACE
            else:
                name = cmd[cmd.index("--name") + 1]
                (res / f"{name}.json").write_text(
                    json.dumps({"instances": ids, "spent_usd": 0.0, "skills": {}})
                )
        return R()

    monkeypatch.setattr(bp.subprocess, "run", fake_run)
    monkeypatch.setattr(bp.shutil, "disk_usage", lambda p: type("U", (), {"free": 100e9})())
    argv = ["x", "--name", "g", "--model", "m", "--skills", "s.json", "--tasks-from", str(pool)]
    monkeypatch.setattr(sys, "argv", argv + ["--dataset-file", "d", "--batch", "4"])
    bp.main()
    assert sizes == [4, 2, 2] and len(list(res.glob("g-p*.json"))) == 2


def test_keep_images_plan_removes_only_unneeded_task_images():
    import importlib.util as _u
    from pathlib import Path as _P

    spec = _u.spec_from_file_location(
        "rbp", _P(__file__).parents[1] / "scripts" / "run_batched_pilot.py"
    )
    rbp = _u.module_from_spec(spec)
    spec.loader.exec_module(rbp)
    m = "mirror.gcr.io"
    a = "swebench/sweb.eval.x86_64.django_1776_django-1:latest"
    b = "swebench/sweb.eval.x86_64.django_1776_django-2:latest"
    live = "starryzhang/sweb.eval.x86_64.conan-io_1776_conan-3:latest"
    local = {a, f"{m}/{a}", b, f"{m}/{b}", "python:3.11", live}
    needed = {
        f"docker.io/{a}",
        f"docker.io/{live}",
        "docker.io/swebench/sweb.eval.x86_64.new-4:latest",
    }
    remove, missing = rbp.plan_images(local, needed, m)
    assert remove == {b, f"{m}/{b}"}  # unneeded task image and its mirror alias only
    assert "python:3.11" not in remove and a not in remove and f"{m}/{a}" not in remove
    assert missing == 1  # only new-4 has to be pulled


def test_merge_carries_timeouts_and_a_rerun_replaces_them(tmp_path, monkeypatch):
    import importlib.util as _u
    import json as _json
    from pathlib import Path as _P

    spec = _u.spec_from_file_location(
        "rbp2", _P(__file__).parents[1] / "scripts" / "run_batched_pilot.py"
    )
    rbp = _u.module_from_spec(spec)
    spec.loader.exec_module(rbp)
    monkeypatch.setattr(rbp, "RESULTS", tmp_path)
    p0 = {"instances": ["a", "b"], "skills": {}, "harness_test_timeout": {"none": ["a"]}}
    p1 = {"instances": ["a"], "skills": {}, "harness_test_timeout": {}}  # 'a' re-run, no timeout
    p2 = {"instances": ["c"], "skills": {}, "patch_apply_failed": {"s": ["c"]}}
    for k, d in enumerate((p0, p1, p2)):
        (tmp_path / f"x-p{k:02d}.json").write_text(_json.dumps(d))
    m = rbp.merge("x", sorted(tmp_path.glob("x-p*.json")))
    assert m["harness_test_timeout"] == {"none": []} and m["patch_apply_failed"] == {"s": ["c"]}
