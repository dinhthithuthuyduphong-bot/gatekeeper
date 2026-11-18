import gzip
import io
import json
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "kaggle" / "scripts"))
import w7_build as wb  # noqa: E402


def test_tool_format_moves_command_and_observation():
    msgs = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "task"},
        {"role": "assistant", "content": "look\n\n```bash\nls src\n```"},
        {"role": "user", "content": "<returncode>0</returncode>\n<output>\na\n</output>"},
        {"role": "assistant", "content": "two\n```bash\nls\n```\n```bash\npwd\n```"},
        {"role": "user", "content": "Please always provide EXACTLY ONE action"},
        {
            "role": "assistant",
            "content": "done\n```bash\necho COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT\n```",
        },
        {"role": "user", "content": ""},
    ]
    out = wb.to_tool_format(msgs)
    assert [m["role"] for m in out] == [
        "system",
        "user",
        "assistant",
        "tool",
        "assistant",
        "user",
        "assistant",
    ]
    assert json.loads(out[2]["tool_calls"][0]["function"]["arguments"]) == {"command": "ls src"}
    assert (
        "tool_calls" not in out[4]
    )  # two blocks: the harness ran nothing, a format error followed
    assert [m["content"] for m in out if m["role"] != "assistant"] == [
        "sys",
        "task",
        msgs[3]["content"],
        msgs[5]["content"],
    ]


def test_pool_a_archive_is_deterministic_and_consistent(tmp_path):
    files, summary = wb.build("A", ROOT / "results")
    a = wb.write_tar(files, tmp_path / "a.tar.gz")
    b = wb.write_tar(files, tmp_path / "b.tar.gz")
    assert a == b
    assert summary["tasks"] == 34
    assert summary["submissions"]["w7a__flash_s41"]["resolved"] == 31
    with tarfile.open(
        fileobj=io.BytesIO(gzip.decompress((tmp_path / "a.tar.gz").read_bytes()))
    ) as tf:
        names = tf.getnames()
        assert sum(n.endswith(".traj.json") for n in names) == 3 * 34
        idmap = json.load(tf.extractfile("id_map.json"))
    assert sorted(idmap.values()) == sorted(f"pallets__jinja-{k}" for k in range(1, 35))
    # XRepoSkill's rule (ingest.adapt_trajectory): an assistant turn followed by a tool turn is an
    # action; every command we found must become exactly one such action
    for name, data in files.items():
        if not name.endswith(".traj.json"):
            continue
        m = json.loads(data)["messages"]
        actions = sum(
            1
            for i, x in enumerate(m[:-1])
            if x["role"] == "assistant" and m[i + 1]["role"] == "tool"
        )
        calls = sum(1 for x in m[:-1] if x["role"] == "assistant" and x.get("tool_calls"))
        assert actions == calls, name
