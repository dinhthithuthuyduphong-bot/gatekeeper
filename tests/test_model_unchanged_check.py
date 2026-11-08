import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from model_unchanged_check import find_traj  # noqa: E402


def _mk(root: Path, run: str, task: str) -> Path:
    f = root / run / "none" / "agent" / task / f"{task}.traj.json"
    f.parent.mkdir(parents=True)
    f.write_text("{}")
    return f


def test_single(tmp_path):
    f = _mk(tmp_path, "g2-e2-s41-k3-p00", "a")
    assert find_traj(tmp_path, "a") == f


def test_rerun_in_later_part_wins(tmp_path):
    # merge(): a task re-run in a later part replaces the older data (A98)
    _mk(tmp_path, "g2-e2-s41-k2-p00", "a")
    later = _mk(tmp_path, "g2-e2-s41-k2-p01", "a")
    assert find_traj(tmp_path, "a") == later
    _mk(tmp_path, "g2-e2-s41-k15-p09", "b")
    last = _mk(tmp_path, "g2-e2-s41-k15-p10", "b")  # numeric, not lexical
    assert find_traj(tmp_path, "b") == last


def test_missing_or_two_batches(tmp_path):
    with pytest.raises(FileNotFoundError):
        find_traj(tmp_path, "a")
    _mk(tmp_path, "g2-e2-s41-k1-p00", "a")
    _mk(tmp_path, "g2-e2-s41-k2-p00", "a")
    with pytest.raises(FileNotFoundError):
        find_traj(tmp_path, "a")
