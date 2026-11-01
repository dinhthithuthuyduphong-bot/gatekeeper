"""Functional loss normalised to [0, 1] (docs/theory/corrections.md section 1.1).

    loss = (F + w * R) / (1 + w)

F = fraction of FAIL_TO_PASS tests still failing, R = fraction of PASS_TO_PASS tests broken.
"""

from __future__ import annotations

from collections.abc import Mapping

__all__ = ["functional_loss", "loss_from_test_results", "PASSED"]

PASSED = {"PASSED", "PASS", "passed", "pass", True}


def functional_loss(fail_fraction: float, regress_fraction: float, w: float = 0.5) -> float:
    if not (0.0 <= fail_fraction <= 1.0 and 0.0 <= regress_fraction <= 1.0):
        raise ValueError("fractions must lie in [0, 1]")
    if w < 0:
        raise ValueError("w must be non-negative")
    return (fail_fraction + w * regress_fraction) / (1.0 + w)


def _fraction_not_passed(results: Mapping[str, object]) -> float:
    if not results:
        return 0.0
    return sum(1 for v in results.values() if v not in PASSED) / len(results)


def loss_from_test_results(
    fail_to_pass: Mapping[str, object],
    pass_to_pass: Mapping[str, object],
    w: float = 0.5,
) -> float:
    """Loss from SWE-bench style per-test outcomes ({test_id: status})."""
    return functional_loss(
        _fraction_not_passed(fail_to_pass), _fraction_not_passed(pass_to_pass), w
    )
