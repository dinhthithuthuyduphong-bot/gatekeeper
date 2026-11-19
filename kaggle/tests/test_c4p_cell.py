"""kaggle/notebooks/c4p_cell.py: the day cap counts this session's spend only (K27)."""

from pathlib import Path

CELL = (Path(__file__).resolve().parents[1] / "notebooks" / "c4p_cell.py").read_text()


def test_day_cap_uses_the_drivers_session_spend():
    assert "start_spent" not in CELL
    assert "left_day = DAY_CAP - session_spent" in CELL
    assert 'session_spent += float(m["summary"]["spent_this_session"])' in CELL


def test_missing_summary_stops_the_session():
    assert "session_spent = DAY_CAP" in CELL
