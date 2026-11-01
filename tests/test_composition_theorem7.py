"""Corrected Theorem 7: individually beneficial skills, jointly harmful, and no function g."""

import pytest

from gatekeeper.composition_example import FlakyDB, scope_str, task_loss, write_s1_o_s2

THETA = 0.05


@pytest.mark.parametrize("variant", ["S1", "S2", "S1prime"])
def test_each_skill_alone_fixes_the_transient_failure(variant):
    assert task_loss("baseline", fail_first=1) == 1.0
    assert task_loss(variant, fail_first=1) == 0.0
    assert task_loss(variant, fail_first=0) == 0.0


def test_composition_fails_silently():
    db = FlakyDB(fail_first=0)
    write_s1_o_s2(db, {"id": 1})  # no exception is raised ...
    assert db.rows == []  # ... and the write never happened


def test_str_values_match_corrected_statement():
    # individually admissible: STR <= -theta
    assert scope_str("S1", THETA) == pytest.approx(-THETA)
    assert scope_str("S2", THETA) == pytest.approx(-THETA)
    # jointly harmful, and the bound 1 - theta is attained (tight)
    assert scope_str("S1oS2", THETA) == pytest.approx(1 - THETA)


def test_no_function_g_of_individual_risks():
    # Same individual STRs (-theta, -theta), different composite STR -> no g exists.
    assert scope_str("S1prime", THETA) == pytest.approx(scope_str("S1", THETA))
    assert scope_str("S1primeoS2", THETA) == pytest.approx(-THETA)
    assert scope_str("S1oS2", THETA) != pytest.approx(scope_str("S1primeoS2", THETA))
