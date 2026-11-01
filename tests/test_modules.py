import json

import pytest

from gatekeeper.footprint import Footprint, analyse_source, overlaps
from gatekeeper.loss import functional_loss, loss_from_test_results
from gatekeeper.scope import (
    TargetContext,
    compare_fingerprints,
    evaluate_predicate,
    fingerprint_repo,
    screen,
)
from gatekeeper.skill import Postcondition, Skill

RETRY_SRC = """
def save(db, row):
    for k in range(3):
        try:
            return db.execute(row)
        except TransientError:
            pass

def unrelated(x):
    y = x + 1
    return y
"""

ASYNC_SRC = """
async def save(db, row):
    await db.execute_async(row)
"""


# ---- loss ---------------------------------------------------------------------------------
def test_loss_is_bounded_and_monotone():
    assert functional_loss(0, 0) == 0.0
    assert functional_loss(1, 1) == 1.0
    assert functional_loss(1, 1, w=10) == 1.0  # paper's "+0.5 per regression" could exceed 1
    assert functional_loss(0.5, 0.0) < functional_loss(0.5, 0.5)
    with pytest.raises(ValueError):
        functional_loss(1.2, 0)
    with pytest.raises(ValueError):
        functional_loss(0.1, 0.1, w=-1)


def test_loss_from_swebench_results():
    f2p = {"t1": "PASSED", "t2": "FAILED"}
    p2p = {"a": "PASSED", "b": "PASSED", "c": "FAILED", "d": "PASSED"}
    assert loss_from_test_results(f2p, p2p, w=0.5) == pytest.approx((0.5 + 0.5 * 0.25) / 1.5)
    assert loss_from_test_results({}, {}) == 0.0


# ---- footprint ----------------------------------------------------------------------------
def test_static_read_write_analysis():
    k = analyse_source(RETRY_SRC, "app.db", ["save"])
    assert k.regions == {"app.db:save"}
    assert "db.execute" in k.reads
    assert "db" in k.writes  # method call may mutate the client
    with pytest.raises(ValueError):
        analyse_source(RETRY_SRC, "app.db", ["missing"])
    allk = analyse_source(RETRY_SRC, "app.db")
    assert "app.db:unrelated" in allk.regions and "y" in allk.writes


def test_overlap_rules():
    retry = analyse_source(RETRY_SRC, "app.db", ["save"])
    asyncify = analyse_source(ASYNC_SRC, "app.db", ["save"])
    other = analyse_source(RETRY_SRC, "app.util", ["unrelated"])
    assert overlaps(retry, asyncify)  # same region: Theorem 7's pair is screened
    assert not overlaps(retry, other)
    p1 = Footprint(properties=frozenset({"delivery_semantics"}))
    p2 = Footprint(properties=frozenset({"delivery_semantics"}))
    assert overlaps(p1, p2)
    assert Footprint.from_dict(retry.to_dict()) == retry
    assert retry.union(other).regions == retry.regions | other.regions


# ---- skill --------------------------------------------------------------------------------
def make_skill(sid="retry-wrap", **kw):
    base = dict(
        id=sid,
        procedure={"kind": "ast_rewrite", "rule": "wrap-retry"},
        fingerprints={"python": "3.11", "dep:sqlalchemy": "2.0.30"},
        input_predicates=({"kind": "symbol_present", "name": "db.execute"},),
        postconditions=(Postcondition("no_duplicate_writes", ("Ra@abc123",)),),
        footprint=Footprint(frozenset({"app.db:save"}), frozenset({"db.execute"})),
        capability_verdict="approved",
    )
    base.update(kw)
    return Skill(**base)


def test_skill_roundtrip(tmp_path):
    s = make_skill()
    p = tmp_path / "s.json"
    s.save(p)
    assert Skill.load(p) == s
    d = json.loads(p.read_text())
    assert d["schema_version"] == 1
    with pytest.raises(ValueError):
        Skill.from_dict({**d, "schema_version": 99})
    with pytest.raises(ValueError):
        Skill.from_dict({"id": "x"})


def test_skill_validation():
    with pytest.raises(ValueError):
        make_skill(capability_verdict="maybe")
    with pytest.raises(ValueError):
        make_skill(input_predicates=({"kind": "telepathy"},))
    with pytest.raises(ValueError):
        make_skill(sid="")


# ---- scope --------------------------------------------------------------------------------
def test_fingerprint_repo(tmp_path):
    (tmp_path / "requirements.txt").write_text("SQLAlchemy==2.0.30\nrequests>=2\n")
    (tmp_path / ".gatekeeper").mkdir()
    (tmp_path / ".gatekeeper" / "behaviour.json").write_text('{"delivery": "exactly-once"}')
    d = fingerprint_repo(tmp_path, interpreter="3.11")
    assert d["python"] == "3.11"
    assert d["dep:sqlalchemy"] == "2.0.30"
    assert d["class:delivery"] == "exactly-once"
    assert "lock:requirements.txt" in d and "dep:requests" not in d


def test_compare_fingerprints():
    skill_d = {"python": "3.11", "dep:django": "4.2.1", "lock:uv.lock": "aaa"}
    assert compare_fingerprints(skill_d, {"python": "3.11", "dep:django": "4.1.0"}) == []
    probs = compare_fingerprints(skill_d, {"python": "3.12", "dep:django": "5.0"})
    assert any("python" in p for p in probs) and any("major" in p for p in probs)
    assert compare_fingerprints({"class:tx": "a"}, {}) == ["class:tx: missing on target"]


def target(**kw):
    base = dict(
        name="Rb",
        fingerprints={"python": "3.11", "dep:sqlalchemy": "2.0.31"},
        symbols=frozenset({"db.execute"}),
        files=frozenset({"app/db.py"}),
        dependencies={"sqlalchemy": "2.0.31"},
        declared_classes={},
    )
    base.update(kw)
    return TargetContext(**base)


def test_predicates():
    t = target(declared_classes={"delivery": "at-least-once"})
    assert evaluate_predicate({"kind": "file_exists", "path": "app/db.py"}, t)
    assert evaluate_predicate({"kind": "dependency", "name": "SQLAlchemy", "spec": ">=2,<3"}, t)
    assert not evaluate_predicate({"kind": "dependency", "name": "sqlalchemy", "spec": "<2"}, t)
    assert not evaluate_predicate({"kind": "dependency", "name": "flask", "spec": ">=1"}, t)
    assert evaluate_predicate(
        {"kind": "declared_class", "key": "delivery", "value": "at-least-once"}, t
    )
    assert evaluate_predicate({"kind": "python", "spec": ">=3.10"}, t)
    assert evaluate_predicate({"kind": "dependency", "name": "sqlalchemy", "spec": "==2.0"}, t)
    assert evaluate_predicate({"kind": "dependency", "name": "sqlalchemy", "spec": "!=1"}, t)
    with pytest.raises(ValueError):
        evaluate_predicate({"kind": "dependency", "name": "sqlalchemy", "spec": "~2"}, t)
    with pytest.raises(ValueError):
        evaluate_predicate({"kind": "nope"}, t)


def test_figure1_skill_passes_the_screen():
    # The motivating harmful skill passes the screen: the client semantics is not recorded.
    r = screen(make_skill(), target())
    assert r.in_scope and r.reasons == ()


def test_screen_rejects_out_of_scope():
    r = screen(make_skill(), target(fingerprints={"python": "3.9"}, symbols=frozenset()))
    assert not r.in_scope
    assert any(x.startswith("D python") for x in r.reasons)
    assert any(x.startswith("I failed") for x in r.reasons)


def test_footprint_assignment_forms():
    src = """
def f(cache, cfg, items):
    a, b = cfg.split()
    cache["k"] = a
    cfg.retries += 1
    total: int = len(items)
    obj.attr = b
    (lambda: None)()
    return total
"""
    k = analyse_source(src, "m", ["f"])
    assert {"a", "b", "cache", "cfg.retries", "total", "obj.attr"} <= k.writes
    assert {"cfg.split", "cfg.retries", "len", "items", "obj"} <= k.reads
