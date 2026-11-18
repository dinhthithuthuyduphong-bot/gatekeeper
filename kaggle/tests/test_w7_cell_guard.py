"""Cost guard of kaggle/notebooks/w7_run_cell.py counts every billed attempt (A143)."""

import ast
from pathlib import Path

CELL = Path(__file__).resolve().parents[1] / "notebooks" / "w7_run_cell.py"
KEEP = {"PIN", "POUT", "MAX_OUT", "CHARS_PER_TOKEN"}


def guard_ns() -> dict:
    tree = ast.parse(CELL.read_text())
    body = [
        n
        for n in tree.body
        if (isinstance(n, ast.FunctionDef) and n.name.startswith("worst_"))
        or (isinstance(n, ast.Assign) and any(getattr(t, "id", "") in KEEP for t in n.targets))
        or (isinstance(n, ast.Assign) and any(isinstance(t, ast.Tuple) for t in n.targets))
    ]
    ns: dict = {}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(CELL), "exec"), ns)
    return ns


def test_discover_bound_counts_guard_retries():
    ns = guard_ns()
    one = ns["worst_call_usd"](9000)
    assert ns["worst_discover_usd"]([9000], 3, 2) == 6 * one
    assert ns["worst_discover_usd"]([9000, 9000], 3, 2) == 12 * one


def test_merge_judge_bound_scales_with_candidates():
    ns = guard_ns()
    m, j = ns["worst_call_usd"](40000), ns["worst_call_usd"](4000)
    assert ns["worst_merge_judge_usd"](0, 40000, 4000) == 0
    assert abs(ns["worst_merge_judge_usd"](10, 40000, 4000) - 10 * (2 * m + 2 * j)) < 1e-12


def test_output_cap_dominates_one_call():
    ns = guard_ns()
    assert abs(ns["worst_call_usd"](0) - 24000 * 12e-6) < 1e-12
