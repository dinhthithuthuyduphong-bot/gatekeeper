import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("make_ablation", Path("scripts/make_ablation.py"))
ma = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ma)


def test_rule_drops_only_history_lines():
    text = "a\n- Check Git History: run `git log -n 5`\n- run `git diff` after edits\nb\n"
    new, drop = ma.ablate(text)
    assert drop == [2]
    assert new == "a\n- run `git diff` after edits\nb\n"


def test_committed_file_follows_the_rule():
    new, drop = ma.ablate(ma.SRC.read_text(encoding="utf-8"))
    assert drop == [7]
    assert ma.OUT.read_text(encoding="utf-8") == new
    assert "git log" not in new and "Bug Patch" not in new
    assert "git diff" in new
