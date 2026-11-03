import pytest

from gatekeeper.alpha_ledger import AlphaLedger


def make(n_cells=1598):
    weights = {f"skill{i % 94}@scope{i // 94}": 1.0 + (i % 5) for i in range(n_cells)}
    return AlphaLedger(0.05, weights)


def test_cells_sum_to_their_share():
    led = make()
    assert sum(led.cell_alpha.values()) == pytest.approx(0.7 * 0.05)
    led.check()


def test_unbounded_composites_never_exceed_budget():
    led = make()
    for _ in range(200_000):
        led.next_composite()
    for _ in range(10_000):
        led.next_readmission()
    assert led.spent_composite < led.composite_budget
    assert led.spent_readmit < led.readmit_budget
    assert led.spent <= 0.05
    led.check()


def test_composite_alpha_is_decreasing():
    led = make(10)
    a1, a2, a3 = led.next_composite(), led.next_composite(), led.next_composite()
    assert a1 > a2 > a3 > 0


def test_invalid_configuration():
    with pytest.raises(ValueError):
        AlphaLedger(0.05, {"a": 1.0}, cell_frac=0.8, composite_frac=0.3)
    with pytest.raises(ValueError):
        AlphaLedger(0.05, {})
    with pytest.raises(ValueError):
        AlphaLedger(1.2, {"a": 1.0})


def test_from_plan_equal_weights_and_total():
    from gatekeeper.alpha_ledger import AlphaLedger

    led = AlphaLedger.from_plan(0.05, [f"c{i}" for i in range(8)], n_composite=2, n_readmit=0)
    assert all(abs(a - 0.05 / 10) < 1e-15 for a in led.cell_alpha.values())
    for _ in range(1000):  # many more composites than planned: total still bounded
        led.next_composite()
    led.check()
    assert led.committed <= 0.05 + 1e-12
