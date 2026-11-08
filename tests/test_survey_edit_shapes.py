import importlib.util
from pathlib import Path

from gatekeeper.patches import change_blocks

spec = importlib.util.spec_from_file_location(
    "survey_edit_shapes", Path(__file__).resolve().parents[1] / "scripts" / "survey_edit_shapes.py"
)
ses = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ses)


def _patch(path, body):
    head = f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n"
    return head + f"@@ -1,3 +1,4 @@ def f(x):\n{body}"


GUARD_A = _patch(
    "pkg/a.py", "     y = g(x)\n+    if y is None:\n+        return 0\n     return y\n"
)
GUARD_B = _patch(
    "lib/b.py",
    "     val = load(path)\n+    if val is None:\n+        return 1.5\n     return val\n",
)
OTHER = _patch("lib/c.py", "-    return x + 1\n+    return x - 1\n")


def test_change_blocks_split_on_context_and_skip_tests_and_non_py():
    p = _patch("pkg/a.py", "-a = 1\n+a = 2\n ctx\n+b = 3\n") + _patch("tests/test_a.py", "+x = 1\n")
    p += _patch("docs/changes.rst", "+note\n")
    assert change_blocks(p) == [("pkg/a.py", ["a = 1"], ["a = 2"]), ("pkg/a.py", [], ["b = 3"])]


def test_normalise_abstracts_names_literals_keeps_keywords_and_drops_comments():
    assert ses.normalise("    if val is None:  # note") == "if ID is None :"
    assert ses.normalise('x = f"a{b}" + 0x1F') == "ID = STR + NUM"
    assert ses.normalise("   # only a comment") == ""


def test_same_shape_across_renamed_identifiers_and_literals():
    assert ses.block_shapes(GUARD_A) == ses.block_shapes(GUARD_B)
    assert ses.block_shapes(GUARD_A) != ses.block_shapes(OTHER)


def test_n_min_matches_eprocess_and_grows_with_K():
    n1 = ses.n_min(1, alpha=0.025, theta=0.0, c=0.5, cap=1000)
    n100 = ses.n_min(100, alpha=0.025, theta=0.0, c=0.5, cap=1000)
    assert n1 is not None and n100 is not None and n100 > n1
    e = ses.BettingEProcess(theta=0.0, alpha=0.025, c=0.5)
    for _ in range(n1 - 1):
        e.update(-1.0)
    assert not e.crossed
    e.update(-1.0)
    assert e.crossed


def test_survey_coverage_and_decision():
    train = [
        {"instance_id": "t1", "repo": "r/train1", "patch": GUARD_A},
        {"instance_id": "t2", "repo": "r/train2", "patch": GUARD_B},
    ]
    test = [{"instance_id": f"x{i}", "repo": "r/tgt", "patch": GUARD_B} for i in range(3)]
    test.append({"instance_id": "y", "repo": "r/tgt", "patch": OTHER})
    test.append({"instance_id": "z", "repo": "r/tgt", "patch": _patch("tests/test_z.py", "+a\n")})
    res = ses.survey(train, test, alpha=0.025, theta=0.0, c=0.5)
    assert res["test_tasks_without_py_blocks"] == 1
    assert res["single_skill_coverage"]["1"]["count"] == 3
    assert res["single_skill_coverage"]["2"]["count"] == 3
    assert res["single_skill_coverage"]["3"]["count"] == 0
    assert res["library_coverage"]["count"] == 3
    cell = res["per_repo_cells_k1"]
    assert cell["K"] == 1 and cell["max_count"] == 3
    assert cell["passes"] == (3 >= cell["n_min"])
    assert res["decision"]["proceed_to_step_2"] is False  # 3 tasks < n_min
