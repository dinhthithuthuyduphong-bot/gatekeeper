import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import harness_audit as ha  # noqa: E402


def rep(resolved, f2p_fail=(), p2p_fail=(), applied=True):
    return {
        "resolved": resolved,
        "patch_successfully_applied": applied,
        "tests_status": {
            "FAIL_TO_PASS": {"success": ["t"], "failure": list(f2p_fail)},
            "PASS_TO_PASS": {"success": ["p"], "failure": list(p2p_fail)},
        },
    }


def test_endpoints():
    assert ha.endpoints(None, set()) == {"S": False, "F": False, "B": False}
    assert ha.endpoints(rep(True), set()) == {"S": True, "F": True, "B": True}
    r = rep(False, p2p_fail=["env"])
    assert ha.endpoints(r, set()) == {"S": False, "F": True, "B": False}
    assert ha.endpoints(r, {"env"})["B"] is True
    r = rep(False, f2p_fail=["t"], p2p_fail=["env"])
    assert ha.endpoints(r, {"env"}) == {"S": False, "F": False, "B": False}


def test_broken_needs_every_run_and_min_runs():
    mk = lambda iid, fails: {"iid": iid, "rep": rep(False, p2p_fail=fails)}  # noqa: E731
    rs = [mk("a", ["x", "y"]), mk("a", ["x"]), mk("a", ["x", "z"]), mk("b", ["x"]), mk("b", ["x"])]
    assert ha.broken_tests(rs) == {"a": {"x"}}  # b has only 2 runs


def test_no_report_loss_is_two_thirds():
    assert abs(ha.NO_REPORT - 2 / 3) < 1e-12
