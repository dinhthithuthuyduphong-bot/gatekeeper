import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import gates  # noqa: E402

from gatekeeper.eprocess import run_admission  # noqa: E402


def test_holm_step_down():
    p = {"a": 0.001, "b": 0.012, "c": 0.04}
    assert gates.holm(p, 0.05) == {"a": True, "b": True, "c": True}  # 0.001<=.0167, .012<=.025
    assert gates.holm({"a": 0.02, "b": 0.001}, 0.025) == {"b": True, "a": True}
    assert gates.holm({"a": 0.03, "b": 0.001}, 0.025) == {"b": True, "a": False}
    assert gates.holm({"a": 0.02, "b": 0.02}, 0.025) == {"a": False, "b": False}  # .02 > .0125
    assert gates.holm({"a": 0.03, "b": 0.001}, 0.05) == {"b": True, "a": True}


def test_gatekeeper_p_matches_admission():
    z = [-1.0] * 30
    alpha = 0.01
    adm = run_admission(z, 0.0, alpha, budget=30)
    p = gates.gatekeeper_p(z, 0.0, alpha, 30)
    assert adm.admitted and p <= alpha
    assert gates.gatekeeper_p([1.0] * 30, 0.0, alpha, 30) == 1.0


def test_naive_rules():
    z = [-1.0, 0.0, 1.0, -1.0]
    assert gates.plug_in(z) and gates.b_g(z, None)
    assert gates.b_g(z, 3) is False  # first 3 sum to 0
    assert gates.b_g([0.0, 1.0, -1.0, -1.0], 3) is False  # first 3 sum to 0: not strictly better
    assert gates.b_x1([5.0]) is True and gates.plug_in([]) is False


@dataclass
class Stratum:
    instance_id: str
    a: int
    n1: int
    c: int
    n0: int


class FakeScore:
    Z95 = 1.959964
    Stratum = Stratum

    @staticmethod
    def mh_risk_difference(strata):
        if not strata:
            return None
        d = [s.a / s.n1 - s.c / s.n0 for s in strata]
        rd = sum(d) / len(d)
        var = sum((x - rd) ** 2 for x in d) / len(d) ** 2
        return rd, var**0.5


def test_b_x2_uses_their_statistic_and_z95():
    strong = [(1, 0, f"t{i}") for i in range(20)]
    assert gates.b_x2(strong, FakeScore) is False  # zero variance in fake: se == 0 -> no admit
    mixed = [(1, 0, f"t{i}") for i in range(15)] + [(0, 0, f"v{i}") for i in range(5)]
    assert gates.b_x2(mixed, FakeScore) is True
    assert gates.b_x2([(0, 1, "a"), (1, 1, "b")], FakeScore) is False
