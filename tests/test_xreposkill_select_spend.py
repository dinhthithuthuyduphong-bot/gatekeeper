import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "xreposkill_select", Path(__file__).parents[1] / "scripts" / "xreposkill_select.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_spend_counts_every_request_on_disk(tmp_path):
    """A59: spending is what was requested, not what the current --ids list covers."""
    for i, (a, b) in enumerate([(1000, 10), (3000, 30)]):
        (tmp_path / f"t{i}.json").write_text(
            json.dumps({"usage": [{"in_tokens": a, "out_tokens": b}]})
        )
    from gatekeeper.pilot import ModelSpec

    spec_ = ModelSpec("x", "vertex_ai/x", 1.0, 2.0, {})
    assert m.spent_on_disk(tmp_path, spec_) == (4000 * 1.0 + 40 * 2.0) / 1e6
