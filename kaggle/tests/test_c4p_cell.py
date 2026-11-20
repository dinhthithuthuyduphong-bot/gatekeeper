"""kaggle/notebooks/c4p_cell.py: the day cap counts this session's spend only (K27)."""

from pathlib import Path

CELL = (Path(__file__).resolve().parents[1] / "notebooks" / "c4p_cell.py").read_text()


def test_day_cap_uses_the_drivers_session_spend():
    assert "start_spent" not in CELL
    assert "left_day = DAY_CAP - session_spent" in CELL
    assert 'session_spent += float(m["summary"]["spent_this_session"])' in CELL


def test_missing_summary_stops_the_session():
    assert "session_spent = DAY_CAP" in CELL


def test_session_stops_without_exactly_one_previous_output():
    assert "EXPECT_PREVIOUS = True" in CELL
    assert "if EXPECT_PREVIOUS and len(done_before) != 1:" in CELL
    i, j = CELL.index("if EXPECT_PREVIOUS"), CELL.index("for tag, model, pin, pout in MODELS")
    assert i < j  # checked before any model call


def test_finished_models_must_come_back_finished():
    assert 'DONE_MODELS = ("haiku", "nano")' in CELL
    assert CELL.index("for tag in DONE_MODELS") < CELL.index("for tag, model, pin, pout in MODELS")


def test_gpt_oss_cap_raised_per_note_40_25():
    assert 'CAP_BY_TAG = {"ossh": 13.11}' in CELL
    assert "CAP_BY_TAG.get(tag, MODEL_CAP) - SPENT_BEFORE_RESTART.get(tag, 0.0)" in CELL
