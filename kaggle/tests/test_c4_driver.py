"""c4_driver.py with a stand-in c3_agent.py: chunk layout (test then extra, never mixed), arm
subset, and the arguments passed to the agent (isolation, split, skill, single commit)."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "kaggle" / "scripts"))
import c4_monitor  # noqa: E402

FAKE_AGENT = r"""
import json, sys
from pathlib import Path
args = sys.argv[1:]
log = Path(__file__).with_name("calls.jsonl")
with log.open("a") as fh:
    fh.write(json.dumps(args) + "\n")
rest = args[args.index("--") + 1:]
rows = [json.loads(x) for x in Path(rest[rest.index("--rows") + 1]).read_text().splitlines() if x]
split = rest[rest.index("--split") + 1]
runs = [{"instance_id": r["instance_id"], "order": r["_gskill_order"]} for r in rows
        if r["_gskill_split"] == split]
out = Path(rest[rest.index("--out") + 1])
out.write_text(json.dumps({"runs": runs}))
out.with_suffix(".cost.json").write_text(json.dumps({"endpoint_usd": 0.001}))
"""


def rows(path, split, n, start=0):
    path.write_text(
        "".join(
            json.dumps({"instance_id": f"{split}{k}", "_gskill_split": split, "_gskill_order": k})
            + "\n"
            for k in range(start, start + n)
        )
    )


def run_driver(tmp_path, extra=True, arms=None, chunk_cap=None):
    code = tmp_path / "code"
    code.mkdir()
    shutil.copy(ROOT / "kaggle" / "scripts" / "c4_driver.py", code)
    (code / "c3_agent.py").write_text(FAKE_AGENT)
    rows(tmp_path / "rows.jsonl", "test", 5)
    rows(tmp_path / "extra.jsonl", "extra", 3)
    cmd = [sys.executable, str(code / "c4_driver.py"), "--tag", "m", "--model", "openai/x"]
    cmd += ["--rows", str(tmp_path / "rows.jsonl"), "--skills-file", "s.txt", "--registry", "r"]
    cmd += ["--isolation", "chroot", "--gskill-yaml", "y", "--outdir", str(tmp_path / "out")]
    cmd += ["--chunk", "2", "--seed", "41", "--cost-limit", "0.3", "--day-cap", "9"]
    cmd += ["--total-cap", "9", "--hours", "1"]
    if extra:
        cmd += ["--extra-rows", str(tmp_path / "extra.jsonl")]
    if arms:
        cmd += ["--arms", *arms]
    if chunk_cap is not None:
        cmd += ["--chunk-cap", str(chunk_cap)]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    calls = [json.loads(x) for x in (code / "calls.jsonl").read_text().splitlines()]
    summary = json.loads((tmp_path / "out" / "m_summary.json").read_text())
    return calls, summary


def test_pool_b_chunks_test_then_extra_with_all_arms(tmp_path):
    calls, summary = run_driver(tmp_path)
    # test: 5 tasks in chunks of 2 -> 3 chunks; extra: 3 tasks -> 2 chunks; 4 arms each
    assert summary["status"] == "all done" and summary["chunks_total"] == 20
    assert summary["chunks_done"] == 20 and len(calls) == 20
    splits = [c[c.index("--split") + 1] for c in calls]
    assert splits == ["test"] * 12 + ["extra"] * 8
    assert all(c[:2] == ["--isolation", "chroot"] and "--packages" not in c for c in calls)
    lf = ["--leak-free" in c for c in calls[:4]]
    sk = ["--skills-file" in c for c in calls[:4]]
    assert lf == [False, False, True, True] and sk == [False, True, False, True]


def test_pool_a_and_arm_subset(tmp_path):
    calls, summary = run_driver(tmp_path, extra=False, arms=["lf_none"])
    assert summary["chunks_total"] == 3 and len(calls) == 3
    assert all("--leak-free" in c and "--skills-file" not in c for c in calls)
    # default cap of f1_probe: tasks in the chunk x cost_limit + cost_limit (chunks of 2, 2, 1)
    caps = [round(float(c[c.index("--cap") + 1]), 6) for c in calls]
    assert caps == [0.9, 0.9, 0.6]


def test_chunk_cap_is_passed_to_f1_probe(tmp_path):
    calls, _ = run_driver(tmp_path, extra=False, arms=["lf_none"], chunk_cap=0.5)
    assert {c[c.index("--cap") + 1] for c in calls} == {"0.5"}


def test_monitor_flags_attempt_and_exposure(tmp_path):
    import gzip

    msgs = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "task"},
        {"role": "assistant", "content": "```bash\nfind / -name x.py\n```"},
        {"role": "user", "content": "<returncode>0</returncode><output>/var/lib/cshim/base/x.py"},
        {"role": "assistant", "content": "```bash\ngit log\n```"},
        {"role": "user", "content": "<output>Bug Patch</output>"},
    ]
    with gzip.open(tmp_path / "m_lf_none_c00.traces.jsonl.gz", "wt") as fh:
        fh.write(json.dumps({"instance_id": "t0", "messages": msgs}) + "\n")
        clean = msgs[:2] + [
            {"role": "assistant", "content": "```bash\nfind / -name y\n```"},
            {"role": "user", "content": "<output>/testbed/y</output>"},
        ]
        fh.write(json.dumps({"instance_id": "t1", "messages": clean}) + "\n")
    res = c4_monitor.scan(tmp_path, include_bad=False)
    a = res["per_arm"]["lf_none"]
    assert (a["runs"], a["attempt"], a["exposure"], a["bug_patch_seen"]) == (2, 2, 1, 1)


def test_monitor_path_not_found_is_not_exposure():
    seen = "<returncode>0</returncode>\n<output>\n/kaggle/working/c4out/x.json\n</output>"
    missing = (
        "<returncode>2</returncode>\n<output>\n"
        "ls: cannot access '/kaggle': No such file or directory\n"
        "ls: cannot access '/var/lib/cshim': No such file or directory\n</output>"
    )
    assert c4_monitor.exposed_in(seen)
    assert not c4_monitor.exposed_in(missing)
    assert c4_monitor.exposed_in(missing + "\n/var/lib/cshim/base/etc\n")


CRASH_AGENT = FAKE_AGENT.replace(
    'runs = [{"instance_id": r["instance_id"], "order": r["_gskill_order"]} for r in rows',
    'runs = [{"instance_id": r["instance_id"], "order": r["_gskill_order"],'
    ' "crashed": r["instance_id"] == "test1"} for r in rows',
)


def run_crash(tmp_path, agent):
    code = tmp_path / "code"
    code.mkdir(exist_ok=True)
    shutil.copy(ROOT / "kaggle" / "scripts" / "c4_driver.py", code)
    (code / "c3_agent.py").write_text(agent)
    rows(tmp_path / "rows.jsonl", "test", 2)
    cmd = [sys.executable, str(code / "c4_driver.py"), "--tag", "m", "--model", "openai/x"]
    cmd += ["--rows", str(tmp_path / "rows.jsonl"), "--skills-file", "s.txt", "--registry", "r"]
    cmd += ["--isolation", "chroot", "--gskill-yaml", "y", "--outdir", str(tmp_path / "out")]
    cmd += ["--chunk", "2", "--seed", "41", "--cost-limit", "0.3", "--day-cap", "9"]
    cmd += ["--total-cap", "9", "--hours", "1", "--arms", "none"]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads((tmp_path / "out" / "m_summary.json").read_text())


def test_second_crash_of_a_chunk_is_kept_with_the_crash_listed(tmp_path):
    # note 40-23: the same session re-runs the set-aside chunk once and keeps it
    first = run_crash(tmp_path, CRASH_AGENT)
    out = tmp_path / "out"
    d = json.loads((out / "m_none_c00.json").read_text())
    assert first["chunks_done"] == 1 and d["accepted_with_crashes"] == ["test1"]
    assert (out / "m_none_c00.json.bad1").exists()
    assert (out / "m_none_c00.try1.cost.json").exists()  # first attempt's money still counted
    assert abs(first["spent_total"] - 0.002) < 1e-9


def test_spend_counts_this_model_only(tmp_path):
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "other_none_c00.cost.json").write_text(json.dumps({"endpoint_usd": 5.0}))
    s = run_crash(tmp_path, FAKE_AGENT)
    assert abs(s["spent_total"] - 0.001) < 1e-9


INFRA_AGENT = FAKE_AGENT.replace(
    'runs = [{"instance_id": r["instance_id"], "order": r["_gskill_order"]} for r in rows',
    'runs = [{"instance_id": r["instance_id"], "order": r["_gskill_order"],'
    ' "infra_error": "scoring: strict status \'timeout\'" if r["instance_id"] == "test0"'
    " else None} for r in rows",
)


def test_second_infra_failure_of_a_chunk_is_kept_with_the_task_listed(tmp_path):
    first = run_crash(tmp_path, INFRA_AGENT)
    d = json.loads((tmp_path / "out" / "m_none_c00.json").read_text())
    assert first["chunks_done"] == 1 and d["accepted_with_infra"] == ["test0"]


FAIL_AGENT = "import sys\nsys.exit(3)\n"  # never writes a result


def test_a_chunk_is_tried_at_most_twice_across_sessions(tmp_path):
    first = run_crash(tmp_path, FAIL_AGENT)
    out = tmp_path / "out"
    assert first["chunks_done"] == 0 and len(list(out.glob("m_none_c00.*bad*"))) >= 1
    calls_before = len(list(out.glob("m_none_c00*.bad*")))
    second = run_crash(tmp_path, FAIL_AGENT)
    assert second["chunks_done"] == 0
    assert len(list(out.glob("m_none_c00*.bad*"))) == calls_before  # no third attempt


def test_strip_format_tags_keeps_the_text():
    import c3_agent

    msgs = [
        {"role": "user", "content": "go"},
        {"role": "assistant", "content": "<|channel|>commentary<|message|>```bash\nls\n```<|end|>"},
        {"role": "tool", "content": None},
    ]
    out = c3_agent.strip_format_tags(msgs)
    assert "<|" not in out[1]["content"] and "```bash\nls\n```" in out[1]["content"]
    assert out[0] == msgs[0] and out[2] == msgs[2] and "<|" in msgs[1]["content"]


def test_driver_passes_strip_format_tags(tmp_path):
    code = tmp_path / "code"
    code.mkdir()
    shutil.copy(ROOT / "kaggle" / "scripts" / "c4_driver.py", code)
    (code / "c3_agent.py").write_text(FAKE_AGENT)
    rows(tmp_path / "rows.jsonl", "test", 2)
    cmd = [sys.executable, str(code / "c4_driver.py"), "--tag", "m", "--model", "openai/x"]
    cmd += ["--rows", str(tmp_path / "rows.jsonl"), "--skills-file", "s.txt", "--registry", "r"]
    cmd += ["--isolation", "chroot", "--gskill-yaml", "y", "--outdir", str(tmp_path / "out")]
    cmd += ["--chunk", "2", "--seed", "41", "--cost-limit", "0.3", "--day-cap", "9"]
    cmd += ["--total-cap", "9", "--hours", "1", "--arms", "none", "--strip-format-tags"]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    calls = [json.loads(x) for x in (code / "calls.jsonl").read_text().splitlines()]
    assert all("--strip-format-tags" in c[: c.index("--")] for c in calls)
