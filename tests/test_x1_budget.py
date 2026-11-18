import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import x1_budget as xb  # noqa: E402


def test_learning_counted_once_and_probes_summed(tmp_path):
    (tmp_path / "x1ship_learn_ledger_h1.json").write_text(json.dumps({"spent_total": 6.0}))
    (tmp_path / "x1ship_learn_ledger_h2.json").write_text(json.dumps({"spent_total": 12.0}))
    (tmp_path / "x2_none.json").write_text(json.dumps({"spent_usd": 0.2, "runs": []}))
    (tmp_path / "x2_none.cost.json").write_text(json.dumps({"endpoint_usd": 9.0}))
    (tmp_path / "s30_none.json").write_text(json.dumps({"spent_usd": 5.0}))  # other section
    s = xb.spent(tmp_path)
    assert s["learn"] == {"x1ship": 12.0, "x1lf": 0.0}
    assert abs(s["total"] - 12.2) < 1e-9
