import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from s36_analysis import groups, is_revert, split_trace  # noqa: E402

BUG = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1,2 +1,2 @@
 x = 1
-return a + b
+return a - b
"""
FIX = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1,2 +1,2 @@
 x = 1
-return a - b
+return a + b
""".replace("+return a + b", "+return a + b   ")  # trailing spaces ignored
OTHER = FIX.replace("+return a + b   ", "+return b + a")


def test_exact_revert_ignores_trailing_space_and_rejects_other_fixes():
    assert is_revert(FIX, BUG)
    assert not is_revert(OTHER, BUG)
    assert not is_revert("", BUG)


def test_split_trace_drops_system_and_task_prompt():
    t = (
        "[SYSTEM]\nskill says Bug Patch\n[USER]\ntask Bug Patch\n"
        "[ASSISTANT]\ngit log -n 5\n[USER]\nabc Bug Patch\n"
    )
    cmd, obs = split_trace(t)
    assert cmd.strip() == "git log -n 5"
    assert [o.strip() for o in obs] == ["abc Bug Patch"]
    cmd, obs = split_trace("[SYSTEM]\nBug Patch\n[USER]\nBug Patch\n[ASSISTANT]\nls\n[USER]\nok\n")
    assert not any("Bug Patch" in o for o in obs)


def test_groups_headings_or_numbered():
    assert groups("# A\ntext\n# B & C\n1. inner") == ["A", "B & C"]
    assert groups("1. 🛑 First 🛑\n   1. nested\n2. Second (x)") == ["First", "Second (x)"]
