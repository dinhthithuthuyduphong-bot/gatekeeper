"""Regression test on the vendored SWE-Skills-Bench paired data (TODO.md section 0.4)."""

import csv
from pathlib import Path

import numpy as np
import pytest

from gatekeeper.analysis import variance_components

SRC = Path(__file__).parents[1] / "data/external/swe-skills-bench/ALL_combined_cells.csv"


@pytest.mark.skipif(not SRC.exists(), reason="external data not present")
def test_external_pilot_key_numbers():
    rows = list(csv.DictReader(SRC.open(encoding="utf-8")))
    assert len(rows) == 3920
    recs = [
        (
            f"{r['harness_model']}|{r['skill']}|{r['requirement_batch']}",
            1 - float(r["one_pass_rate"]) / 100,
            1 - float(r["none_pass_rate"]) / 100,
        )
        for r in rows
    ]
    vc = variance_components(recs)
    assert vc["sigma_T2"] == pytest.approx(0.067, abs=0.002)
    assert vc["sigma_S2"] == pytest.approx(0.040, abs=0.002)
    assert vc["unpaired_over_paired"] == pytest.approx(4.31, abs=0.05)
    z = np.array([r[1] - r[2] for r in recs])
    assert (z == 0).mean() == pytest.approx(0.69, abs=0.01)
