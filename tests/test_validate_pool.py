import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "validate_pool", Path(__file__).parents[1] / "scripts" / "validate_pool.py"
)
vp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vp)


def test_pool_is_sharded_without_overlap():
    pool = json.loads(Path("configs/pilot_pool.json").read_text())["instances"]
    shards = [vp.shard_ids(k, 4) for k in range(4)]
    assert sorted(sum(shards, [])) == sorted(pool)
    assert len(pool) == len(set(pool)) == 40


def test_merge(tmp_path, monkeypatch):
    monkeypatch.setattr(vp, "OUT", tmp_path)
    (tmp_path / "shard0.json").write_text(json.dumps({"a": {"usable": True, "reason": ""}}))
    (tmp_path / "shard1.json").write_text(
        json.dumps({"b": {"usable": False, "reason": "unstable"}})
    )
    s = vp.merge()
    assert s["n_checked"] == 2 and s["usable"] == ["a"] and s["rejected"] == {"b": "unstable"}
