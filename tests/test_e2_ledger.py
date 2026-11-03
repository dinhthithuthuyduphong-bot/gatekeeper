import importlib.util
import subprocess
import time
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "e2_ledger", Path(__file__).parents[1] / "scripts" / "e2_ledger.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def _sh(*a, cwd):
    subprocess.run(a, cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def two_clones(tmp_path):
    bare = tmp_path / "origin.git"
    _sh("git", "init", "-q", "--bare", str(bare), cwd=tmp_path)
    clones = []
    for name in ("a", "b"):
        _sh("git", "init", "-q", name, cwd=tmp_path)
        _sh("git", "remote", "add", "origin", str(bare), cwd=tmp_path / name)
        clones.append(tmp_path / name)
    return clones


def test_cas_refuses_a_write_based_on_a_stale_tip(two_clones, monkeypatch):
    a, b = two_clones
    monkeypatch.chdir(b)
    tip_b, _ = m.read("L")  # b reads (empty ledger) ...
    monkeypatch.chdir(a)
    assert m.write("L", None, "ka", {"spent": 0.0, "reserved": 2.0}, "a")  # ... a writes first
    monkeypatch.chdir(b)
    assert not m.write("L", tip_b, "kb", {"spent": 0.0, "reserved": 2.0}, "b")  # stale: refused
    tip, entries = m.read("L")
    assert set(entries) == {"ka"}
    assert m.write("L", tip, "kb", {"spent": 0.0, "reserved": 2.0}, "b")  # re-read: accepted


def test_reserve_never_lets_total_exceed_the_cap(two_clones, monkeypatch):
    a, b = two_clones
    monkeypatch.chdir(a)
    far = time.time() + 3600
    assert m.reserve("L", "ka", 2.0, 3.0, far, 0.01) == 0
    monkeypatch.chdir(b)
    # a holds 2 of 3: b cannot reserve 2 now, and with no time left to wait it stops
    assert m.reserve("L", "kb", 2.0, 3.0, time.time(), 0.01) == m.EXHAUSTED
    monkeypatch.chdir(a)
    m.settle("L", "ka", 0.5, keep_reserved=False)  # a's call cost 0.5: room for b again
    monkeypatch.chdir(b)
    assert m.reserve("L", "kb", 2.0, 3.0, far, 0.01) == 0
    _, e = m.read("L")
    spent, reserved = m.totals(e)
    assert spent + reserved <= 3.0
    # spent alone already leaves no room for a worst-case call: stop for good
    monkeypatch.chdir(a)
    m.settle("L", "ka", 1.5, keep_reserved=False)
    assert m.reserve("L", "ka", 2.0, 3.0, far, 0.01) == m.EXHAUSTED


def test_settle_never_decreases_recorded_spend_and_can_keep_the_reservation(
    two_clones, monkeypatch
):
    a, _ = two_clones
    monkeypatch.chdir(a)
    assert m.reserve("L", "ka", 2.0, 10.0, time.time() + 60, 0.01) == 0
    m.settle("L", "ka", 0.7, keep_reserved=True)  # call lost its result: keep the worst case
    _, e = m.read("L")
    assert e["ka"] == {"spent": 0.7, "reserved": 2.0}
    with pytest.raises(SystemExit):
        m.settle("L", "ka", 0.1, keep_reserved=False)
