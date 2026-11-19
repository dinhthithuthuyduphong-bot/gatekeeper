"""Cost guard of kaggle/notebooks/w7_run_cell.py (A145, A147): the spend never passes a cap."""

import ast
import threading
import types
from pathlib import Path

import pytest

CELL = Path(__file__).resolve().parents[1] / "notebooks" / "w7_run_cell.py"
KEEP = {"PIN", "POUT", "MAX_OUT", "CHARS_PER_TOKEN"}
FUNCS = {"worst_call_usd", "snapshot", "rollback", "call_usd", "guard_completion"}


def ns() -> dict:
    tree = ast.parse(CELL.read_text())
    body = [
        n
        for n in tree.body
        if (isinstance(n, ast.FunctionDef) and n.name in FUNCS)
        or (isinstance(n, ast.ClassDef) and n.name == "BudgetStop")
        or (isinstance(n, ast.Assign) and any(isinstance(t, ast.Tuple) for t in n.targets))
        or (isinstance(n, ast.Assign) and any(getattr(t, "id", "") in KEEP for t in n.targets))
    ]
    g: dict = {"os": __import__("os"), "threading": threading}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(CELL), "exec"), g)
    return g


def reply(tin, tout):
    u = types.SimpleNamespace(prompt_tokens=tin, completion_tokens=tout, cost=None)
    return types.SimpleNamespace(usage=u)


def make(g, cap, sent):
    spent = {"session": 0.0, "calls": 0, "tokens_in": 0, "tokens_out": 0, "failed_calls": 0}
    acct, log = {"reserved": 0.0, "stopped": False}, []
    f = g["guard_completion"](sent, lambda: cap - spent["session"], acct, spent, log)
    return f, spent, acct, log


def test_output_cap_dominates_one_call():
    g = ns()
    assert abs(g["worst_call_usd"](0) - 24000 * 12e-6) < 1e-12


def test_guard_refuses_the_call_that_could_pass_the_cap():
    g = ns()
    worst = g["worst_call_usd"](30)  # 30 characters of messages below
    msgs = [{"role": "user", "content": "x" * 30}]
    f, spent, acct, log = make(g, 2.5 * worst, lambda **kw: reply(1000, 1000))
    f(messages=msgs)
    f(messages=msgs)  # spent is small; two worst cases still fit
    n_ok = spent["calls"]
    while True:
        try:
            f(messages=msgs)
        except g["BudgetStop"]:
            break
    assert acct["stopped"] and spent["session"] <= 2.5 * worst
    assert spent["calls"] >= n_ok and len(log) == spent["calls"]


def test_failed_attempt_is_charged_its_worst_case():
    g = ns()

    def boom(**kw):
        raise RuntimeError("timeout")

    f, spent, acct, log = make(g, 10.0, boom)
    with pytest.raises(RuntimeError):
        f(messages=[{"content": "abc"}])
    assert spent["failed_calls"] == 1 and spent["session"] == g["worst_call_usd"](3)
    assert abs(acct["reserved"]) < 1e-12


def test_concurrent_calls_never_pass_the_cap():
    g = ns()
    worst = g["worst_call_usd"](10)
    cap = 3.2 * worst
    gate = threading.Barrier(3)

    def slow(**kw):
        gate.wait(timeout=5)
        return reply(0, 24000)  # every call costs its worst case

    f, spent, acct, log = make(g, cap, slow)
    errs = []

    def one():
        try:
            f(messages=[{"content": "x" * 10}])
        except g["BudgetStop"] as e:
            errs.append(e)

    ts = [threading.Thread(target=one) for _ in range(3)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert spent["session"] <= cap + 1e-12 and abs(acct["reserved"]) < 1e-12


def test_rollback_restores_files(tmp_path):
    g = ns()
    a = tmp_path / "a.jsonl"
    a.write_text("one\n")
    snap = g["snapshot"](str(tmp_path))
    a.write_text("one\ntwo\n")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "new.jsonl").write_text("x")
    assert g["rollback"](str(tmp_path), snap) == 2
    assert a.read_text() == "one\n" and not (tmp_path / "sub" / "new.jsonl").exists()


def test_paid_run_refuses_a_dry_run_state():
    src = CELL.read_text()
    assert 'state.get("dry_run"' in src and "do not attach the dry run's zip" in src
