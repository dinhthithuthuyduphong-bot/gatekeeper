import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import x1_alerts as xa  # noqa: E402

CAPS = json.loads((Path(__file__).resolve().parents[1] / "configs" / "x1.json").read_text())


def _probe(d, name, n, spent=0.1, infra=(), crash=None):
    runs = [{"instance_id": f"t{i}", "cost_usd": 0.01} for i in range(n)]
    for i in infra:
        runs[i]["infra_error"] = "scoring: timeout"
    if crash:
        runs[0]["crash_head"] = crash
    (d / f"{name}.json").write_text(json.dumps({"spent_usd": spent, "n_tasks": n, "runs": runs}))


def _ids(found):
    return sorted(a["id"] for a in found)


def test_clean_x2_stage_gives_no_alert(tmp_path):
    _probe(tmp_path, "x2_none", 34, 0.19)
    _probe(tmp_path, "x2_skill", 34, 0.67)
    assert xa.alerts([tmp_path], CAPS, "") == []


def test_infra_quota_and_incomplete(tmp_path):
    _probe(
        tmp_path,
        "x2_none",
        20,
        0.19,
        infra=[3],
        crash="litellm.RateLimitError: 429 RESOURCE_EXHAUSTED",
    )
    assert _ids(xa.alerts([tmp_path], CAPS, "")) == ["A1", "A2", "A3"]


def test_money_projection_before_scoring(tmp_path):
    _probe(tmp_path, "x2_none", 34, 0.19)
    _probe(tmp_path, "x2_skill", 34, 0.67)
    (tmp_path / "x1ship_learn_ledger_h1.json").write_text(json.dumps({"spent_total": 6.0}))
    assert xa.alerts([tmp_path], CAPS, "") == []  # 0.86 + 12.254 + 10.99 = 24.10 <= 24.509
    (tmp_path / "x1ship_learn_ledger_h1.json").write_text(json.dumps({"spent_total": 12.7}))
    found = xa.alerts([tmp_path], CAPS, "")  # 0.86 + 12.7 (rest of ship expected 0) + 10.99
    assert _ids(found) == ["A4"] and found[0]["limit_before_scoring"] == 24.509


def test_direction_alerts_after_learning(tmp_path):
    for tag, text in (("x1ship", "Run tests first.\n"), ("x1lf", "Read git log for hints.\n")):
        for h in (1, 2):
            (tmp_path / f"{tag}_learn_ledger_h{h}.json").write_text(
                json.dumps({"spent_total": 5.0})
            )
        (tmp_path / f"{tag}_best_skills.txt").write_text(text)
    found = xa.alerts([tmp_path], CAPS, "")
    assert sorted(a["tag"] for a in found if a["id"] == "A5") == ["x1lf", "x1ship"]
    (tmp_path / "x1ship_best_skills.txt").write_text("Check the commit history.\n")
    (tmp_path / "x1lf_best_skills.txt").write_text("Run tests first.\n")
    assert [a for a in xa.alerts([tmp_path], CAPS, "") if a["id"] == "A5"] == []


def test_dry_prefix_reads_only_dry_files_and_skips_a5(tmp_path):
    _probe(tmp_path, "x2_none", 34, 9.0, infra=[0])  # a paid file must not count in dry mode
    _probe(tmp_path, "dryx2_none", 2, 0.0)
    for h in (1, 2):
        (tmp_path / f"dryx1ship_learn_ledger_h{h}.json").write_text(
            json.dumps({"spent_total": 0.001})
        )
    (tmp_path / "dryx1ship_best_skills.txt").write_text("no history line\n")
    assert xa.alerts([tmp_path], CAPS, "dry") == []


def test_later_directory_wins(tmp_path):
    old, new = tmp_path / "prev", tmp_path / "results"
    old.mkdir(), new.mkdir()
    _probe(old, "x2_none", 10, 0.1)
    _probe(new, "x2_none", 34, 0.19)
    assert xa.alerts([old, new], CAPS, "") == []


def test_acknowledged_alert_no_longer_stops():
    found = [
        {"id": "A5", "tag": "x1ship", "history_lines": 0},
        {"id": "A1", "file": "x2_none.json"},
    ]
    acks = [{"id": "A5", "tag": "x1ship", "date": "2026-11-21", "decision": "tiếp tục"}]
    acked, stop = xa.acknowledged(found, acks)
    assert [a["id"] for a in acked] == ["A5"] and [a["id"] for a in stop] == ["A1"]
