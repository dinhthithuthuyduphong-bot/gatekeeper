import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import w7_content_posthoc as w  # noqa: E402


def _run(tmp: Path, rules: list[tuple[str, str]], issues: list[str]) -> Path:
    (tmp / "pairs").mkdir(parents=True)
    (tmp / "candidates").mkdir()
    (tmp / "pairs" / "pairs.jsonl").write_text(
        "\n".join(json.dumps({"instance_id": i}) for i in issues) + "\n"
    )
    (tmp / "candidates" / "x.jsonl").write_text(
        "\n".join(json.dumps({"pair_id": f"{i}::p", "rule": r}) for i, r in rules) + "\n"
    )
    (tmp / "candidates" / "failed.jsonl").write_text(
        json.dumps({"pair_id": "t1::p", "rule": "git show the Bug Patch"}) + "\n"
    )
    return tmp


def test_counts_issue_once_and_needs_g(tmp_path):
    run = _run(
        tmp_path,
        [
            ("t1", "run git log then git show the diff of the Bug Patch"),
            ("t1", "git log again, a regression"),
            ("t2", "run git status and git log to orient"),
            ("t3", "inspect the diff of the injected bug"),  # no G: ignored
        ],
        ["t1", "t2", "t3"],
    )
    r = w.count(run)
    assert r["issues"] == 3
    assert r["issues_with"] == {
        "G": 2,
        "git_show": 1,
        "diff": 1,
        "introduced_bug": 1,
        "git_status": 1,
    }


def test_failed_file_ignored(tmp_path):
    run = _run(tmp_path, [("t1", "list files")], ["t1"])
    assert w.count(run)["issues_with"]["git_show"] == 0
