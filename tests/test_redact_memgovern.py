import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from redact_memgovern import redact  # noqa: E402

FIX = (
    "Strategic Approach: replace the deprecated alias everywhere and keep the semantics intact. "
    * 2
)
BUG = "Statistical distribution moments are defined as infinite instead of undefined for some laws."
CARDS = {
    "scipy/scipy733": {"repo": "scipy/scipy", "bug_description": BUG, "fix_experience": FIX},
    "other/repo1": {"repo": "other/repo", "bug_description": "x" * 70, "fix_experience": "y" * 70},
}
GUIDE = "3. **Search and Retrieve Experience**: use exp_search then exp_read before editing code."


def _traj(tmp: Path) -> Path:
    msgs = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "issue text\n\n" + GUIDE},
        {"role": "assistant", "content": "", "tool_calls": [{"function": {"arguments": "{}"}}]},
        {"role": "tool", "content": f"[1] ID: scipy/scipy733\n    Issue Content: {BUG}\n"},
        {"role": "assistant", "content": ""},
        {
            "role": "tool",
            "content": f"ID:   scipy/scipy733\nRepo: scipy/scipy\n\nContent:\n\n{FIX}",
        },
        {"role": "assistant", "content": ""},
        {"role": "tool", "content": "<returncode>0</returncode> plain ls output"},
    ]
    d = tmp / "runs" / "p" / "memgovern" / "agent" / "t"
    d.mkdir(parents=True)
    f = d / "t.traj.json"
    f.write_text(json.dumps({"messages": msgs}, indent=1))
    (d.parent / "minisweagent.log").write_text("\n".join(m["content"] for m in msgs))
    return f


def test_redacts_cards_and_instructions(tmp_path):
    f = _traj(tmp_path)
    changed, bad = redact([tmp_path / "runs"], {"t": GUIDE}, CARDS)
    assert changed == 2 and bad == []
    msgs = json.loads(f.read_text())["messages"]
    assert "<<MEMGOVERN_TEXT sha256=" in msgs[1]["content"] and GUIDE not in msgs[1]["content"]
    assert msgs[3]["content"].startswith("<<MEMGOVERN_TEXT") and msgs[5]["content"].startswith("<<")
    assert "plain ls output" in msgs[7]["content"]  # ordinary observations stay
    log = (f.parent.parent / "minisweagent.log").read_text()
    assert FIX[:60] not in log and BUG[:60] not in log


def test_non_trajectory_file_still_carrying_text_is_removed_and_listed(tmp_path):
    f = _traj(tmp_path)
    # the agent copies card text into a file it writes (not a trajectory string)
    (f.parent / "patch.diff").write_text("+# " + FIX[10:130])
    _, bad = redact([tmp_path / "runs"], {"t": GUIDE}, CARDS)
    assert bad == [] and not (f.parent / "patch.diff").exists()
    assert json.loads((f.parent / "REDACTION.json").read_text())["removed"] == ["patch.diff"]


def test_reindented_instructions_and_extra_fields_are_scrubbed(tmp_path):
    long_guide = GUIDE + " Then read the card and apply its strategy to the repository code."
    d = tmp_path / "runs" / "p" / "memgovern" / "agent" / "t"
    d.mkdir(parents=True)
    msgs = [
        {"role": "user", "content": "issue\n    " + long_guide.replace(" use ", "\n    use ")},
        {"role": "assistant", "content": ""},
        {"role": "tool", "content": "ok", "extra": {"raw_output": f"Repo: x\nContent:\n{FIX}"}},
    ]
    f = d / "t.traj.json"
    f.write_text(json.dumps({"messages": msgs}))
    _, bad = redact([tmp_path / "runs"], {"t": long_guide}, CARDS)
    out = json.loads(f.read_text())["messages"]
    assert bad == []
    assert out[0]["content"].startswith("<<MEMGOVERN_TEXT")
    assert out[2]["extra"]["raw_output"].startswith("<<MEMGOVERN_TEXT")
    assert out[2]["content"] == "ok"


def test_card_ids_from_read_output_and_commands(tmp_path):
    f = tmp_path / "a.log"
    f.write_text('ID:   other/repo1\n{"command": "exp_read \\"scipy/scipy733\\""}')
    from redact_memgovern import referenced_ids

    assert referenced_ids([f]) == {"other/repo1", "scipy/scipy733"}
