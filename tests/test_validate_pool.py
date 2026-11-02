import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "validate_pool", Path(__file__).parents[1] / "scripts" / "validate_pool.py"
)
vp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vp)


def test_pool_is_sharded_without_overlap():
    pool = json.loads(Path("configs/pools/default.json").read_text())["instances"]
    shards = [vp.shard_ids(k, 4) for k in range(4)]
    assert sorted(sum(shards, [])) == sorted(pool)
    assert len(pool) == len(set(pool)) == 40


def test_merge(tmp_path, monkeypatch):
    monkeypatch.setattr(vp, "OUT", tmp_path)
    monkeypatch.setattr(vp, "TAG", "t")
    (tmp_path / "t").mkdir()
    (tmp_path / "t" / "shard0.json").write_text(json.dumps({"a": {"usable": True, "reason": ""}}))
    (tmp_path / "t" / "shard1.json").write_text(
        json.dumps({"b": {"usable": False, "reason": "unstable"}})
    )
    (tmp_path / "t" / "shard2.json").write_text(
        json.dumps({"c": {"usable": False, "infra_error": True, "reason": "infra"}})
    )
    s = vp.merge()
    assert s["n_checked"] == 3 and s["usable"] == ["a"] and s["rejected"] == {"b": "unstable"}
    assert s["infra_error"] == ["c"]


def test_classify():
    ok = {
        "resolved": True,
        "tests_status": {
            "FAIL_TO_PASS": {"success": ["t"], "failure": []},
            "PASS_TO_PASS": {"success": ["p"], "failure": []},
        },
    }
    noop = {
        "resolved": False,
        "tests_status": {
            "FAIL_TO_PASS": {"success": [], "failure": ["t"]},
            "PASS_TO_PASS": {"success": ["p"], "failure": []},
        },
    }
    assert vp.classify(ok, ok, noop)["usable"]
    assert vp.classify(ok, None, noop)["infra_error"]
    dirty = {
        **noop,
        "tests_status": {**noop["tests_status"], "PASS_TO_PASS": {"success": [], "failure": ["p"]}},
    }
    r = vp.classify(ok, ok, dirty)
    assert not r["usable"] and not r["infra_error"] and r["reason"] == "noop arm not clean"
