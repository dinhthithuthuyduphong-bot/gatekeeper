import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import split_compare as sc  # noqa: E402


def test_identical_only_when_ids_labels_and_order_all_match(tmp_path):
    rows = [{"instance_id": "a", "_gskill_split": "train", "_gskill_order": 0}]
    (tmp_path / "x.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    old = sc.load(tmp_path / "x.jsonl")
    assert sc.compare(old, dict(old))["identical"]
    assert not sc.compare(old, {"a": ("test", 0)})["identical"]
    assert not sc.compare(old, {"a": ("train", 1)})["identical"]
    assert not sc.compare(old, {"b": ("train", 0)})["identical"]
