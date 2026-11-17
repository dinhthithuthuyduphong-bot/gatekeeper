"""Detection rules of scripts/history_audit.py on hand-made traces (the false positives that the
first rule set produced are cases here)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import history_audit as h  # noqa: E402

BUG = """diff --git a/src/m.py b/src/m.py
--- a/src/m.py
+++ b/src/m.py
@@ -1,3 +1,3 @@
 def f(x):
-    return compute_value(x) + 1
+    return compute_value(x) - 1
"""
ROW = {"patch": BUG, "FAIL_TO_PASS": ["tests/test_m.py::test_f"]}
L1 = {"f2p_signatures": ["def test_f("], "f2p_deleted_files": ["tests/test_m.py"]}


def run(*pairs):
    msgs = [{"role": "system", "content": "s"}, {"role": "user", "content": "task"}]
    for cmd, obs in pairs:
        msgs.append({"role": "assistant", "content": f"THOUGHT\n```bash\n{cmd}\n```"})
        msgs.append({"role": "user", "content": obs})
    return h.audit_run(msgs, ROW, L1)


def test_git_show_of_the_bug_commit_is_shown():
    obs = "commit abc\n    Bug Patch\n" + BUG
    r = run(("git log -n 3", "abc Bug Patch"), ("git show abc", obs))
    assert r["seen_bug_msg"] and r["bug_diff_shown"] and r["history_cmd"]


def test_own_fix_diff_is_not_shown():
    fix = "-    return compute_value(x) - 1\n+    return compute_value(x) + 1\n"
    assert not run(("git diff", fix))["bug_diff_shown"]


def test_own_fix_of_a_swapped_branch_is_not_shown():
    # the fix removes the very line the bug removed: only a history command may count it
    assert not run(("git diff", "-    return compute_value(x) + 1\n"))["bug_diff_shown"]


def test_whole_tree_dump_of_a_single_commit_is_not_shown():
    dump = "commit def\n    Initial commit\n+def f(x):\n+    return compute_value(x) - 1\n"
    dump += "+def test_f():\n+    assert f(1) == 2\n"
    r = run(("git show HEAD", dump))
    assert not r["bug_diff_shown"] and not r["deleted_tests_shown"]
    assert r["deleted_tests_shown_loose"]  # the first rule set flagged this case


def test_deleted_tests_shown_and_restored():
    obs = "    Remove F2P Tests\ndeleted file mode 100644\n-def test_f():\n-    assert f(1) == 2\n"
    r = run(
        ("git show HEAD", obs),
        ("git checkout HEAD~2 -- tests", ""),
        ("pytest tests", "FAILED tests/test_m.py::test_f"),
    )
    assert r["seen_f2p_msg"] and r["deleted_tests_shown"] and r["tests_restored_and_run"]


def test_restore_without_running_the_tests_is_not_restored_and_run():
    r = run(("git checkout HEAD~2 -- tests", ""), ("git status", "tests/test_m.py"))
    assert r["restore_or_read_old_file_cmd"] and not r["tests_restored_and_run"]


def test_exact_revert():
    fix = "--- a/src/m.py\n+++ b/src/m.py\n-    return compute_value(x) - 1\n"
    fix += "+    return compute_value(x) + 1\n"
    assert h.is_revert(fix, BUG)
    assert not h.is_revert(BUG, BUG)
