"""Integration test on skills with known answers (TODO.md Phase 5b 'Test tich hop')."""

import numpy as np
import pytest

from gatekeeper.admission import Gatekeeper
from gatekeeper.alpha_ledger import AlphaLedger
from gatekeeper.footprint import Footprint
from gatekeeper.scope import TargetContext
from gatekeeper.skill import Skill

THETA = 0.05
FP = {"python": "3.11", "dep:django": "4.2.1"}


class KnownEffectRunner:
    """Paired trials with a known true STR per procedure tuple.

    Without skill: loss ~ Bernoulli(0.4). With skill: a failing task is fixed with prob a, a
    passing task is broken with prob b, so E[Z] = -0.4 a + 0.6 b = STR.
    """

    def __init__(self, effects, seed=0):
        self.effects = effects
        self.rng = np.random.default_rng(seed)
        self.calls = 0

    def run_pair(self, procedures, task_id, seed):
        self.calls += 1
        s = self.effects.get(tuple(procedures), 0.0)
        a, b = (-s / 0.4, 0.0) if s < 0 else (0.0, s / 0.6)
        without = float(self.rng.random() < 0.4)
        if without:
            with_ = 0.0 if self.rng.random() < a else 1.0
        else:
            with_ = 1.0 if self.rng.random() < b else 0.0
        return with_, without


class PoolSampler:
    def __init__(self, n=500):
        self.tasks = [f"task-{i}" for i in range(n)]

    def sample(self, scope, rng):
        return self.tasks[int(rng.integers(len(self.tasks)))]


def skill(sid, region, cap="approved", preds=()):
    return Skill(
        id=sid,
        procedure={"rule": sid},
        fingerprints=dict(FP),
        input_predicates=preds,
        footprint=Footprint(regions=frozenset({region})),
        capability_verdict=cap,
    )


LIB = {
    "good": skill("good", "app:a"),
    "neutral": skill("neutral", "app:b"),
    "harmful": skill("harmful", "app:c"),
    "needs-celery": skill(
        "needs-celery", "app:d", preds=({"kind": "dependency", "name": "celery", "spec": ">=5"},)
    ),
    "retry": skill("retry", "app.db:save"),
    "asyncify": skill("asyncify", "app.db:save", cap="rejected"),
}
EFFECTS = {
    ("good",): -0.25,
    ("neutral",): 0.0,
    ("harmful",): 0.10,
    ("retry",): -0.25,
    ("asyncify",): -0.25,
    ("retry", "asyncify"): 0.60,  # Theorem 7: individually good, jointly harmful
}
TARGET = TargetContext(name="Rb", fingerprints=dict(FP), dependencies={"django": "4.2.1"})


def make_gk(budget=600):
    keys = {f"{s}@django4": 1.0 for s in LIB}
    ledger = AlphaLedger(0.05, keys)
    return Gatekeeper(
        LIB, ledger, KnownEffectRunner(EFFECTS), PoolSampler(), theta=THETA, budget_per_cell=budget
    )


def test_known_answers():
    gk = make_gk()
    cells = {
        s: gk.request(s, "django4", TARGET) for s in ("good", "neutral", "harmful", "needs-celery")
    }
    assert cells["needs-celery"].status == "out_of_scope"
    assert any("celery" in r for r in cells["needs-celery"].screen_reasons)
    used = gk.run(total_trials=3000)
    assert used > 0
    assert cells["good"].status == "admitted"
    assert cells["neutral"].status == "quarantine"  # harmless is not enough
    assert cells["harmful"].status == "quarantine"
    # allocation stops spending on cells that look neutral/harmful after the exploration phase
    assert cells["harmful"].n < 200
    assert gk.may_execute(["good"], "django4") == (True, [])
    ok, why = gk.may_execute(["neutral"], "django4")
    assert not ok and "functionally quarantine" in why[0]


def test_composition_is_screened_and_capability_kept_separate():
    gk = make_gk()
    gk.request("retry", "django4", TARGET)
    gk.request("asyncify", "django4", TARGET)
    comp = gk.cells["retry∘asyncify@django4"]
    assert comp.kind == "composite"
    assert comp.alpha < gk.ledger.composite_budget
    gk.run(total_trials=4000)
    assert gk.cells["retry@django4"].status == "admitted"
    assert gk.cells["asyncify@django4"].status == "admitted"  # functionally fine ...
    assert comp.status == "quarantine"  # ... but the pair is not
    ok, why = gk.may_execute(["retry", "asyncify"], "django4")
    assert not ok
    assert any("capability rejected" in w for w in why)  # separate decision, separate evidence
    assert any("composite not admitted" in w for w in why)
    assert gk.may_execute(["retry"], "django4") == (True, [])


def test_retirement_and_readmission_spend_their_own_alpha():
    gk = make_gk()
    c = gk.request("good", "django4", TARGET)
    gk.run(total_trials=1000)
    assert c.status == "admitted"
    retired = gk.on_environment_change("django4", {"python": "3.11", "dep:django": "5.0.0"})
    assert retired == ["good@django4"]
    assert c.status == "retired"
    ok, _ = gk.may_execute(["good"], "django4")
    assert not ok
    new_target = TargetContext(name="Rb", fingerprints={"python": "3.11", "dep:django": "4.2.9"})
    spent_before = gk.ledger.spent_readmit
    c2 = gk.request("good", "django4", new_target)
    assert c2.readmission and c2.n == 0 and c2.status == "quarantine"
    assert gk.ledger.spent_readmit > spent_before
    gk.ledger.check()


def test_lockfile_change_also_retires():
    gk = make_gk()
    t = TargetContext(name="Rb", fingerprints={**FP, "lock:uv.lock": "aaa"})
    gk.request("good", "django4", t)
    assert gk.on_environment_change("django4", {**FP, "lock:uv.lock": "bbb"}) == ["good@django4"]


def test_certificate_contents():
    gk = make_gk()
    c = gk.request("good", "django4", TARGET)
    gk.run(total_trials=1000)
    cert = gk.certificate(c)
    assert cert["decision"] == "Admit"
    assert cert["n_paired_trials"] == c.n > 0
    assert cert["log_e"] >= cert["log_threshold"]
    assert [g["implies_no_harm"] for g in cert["guarantee"]] == [True, True, True, False]
    assert cert["capability_verdicts"] == {"good": "approved"}
    assert "good@django4" in gk.certificates_json()


def test_runner_contract_is_enforced():
    class BadRunner:
        def run_pair(self, procedures, task_id, seed):
            return 1.5, 0.0

    gk = make_gk()
    gk.runner = BadRunner()
    c = gk.request("good", "django4", TARGET)
    with pytest.raises(ValueError):
        gk.step(c)


def test_budget_per_cell_and_idempotent_request():
    gk = make_gk(budget=40)
    c = gk.request("neutral", "django4", TARGET)
    assert gk.request("neutral", "django4", TARGET) is c
    gk.step(c, 100)
    assert c.n == 40 and c.status == "quarantine"
    assert gk.step(gk.request("needs-celery", "django4", TARGET)).n == 0
