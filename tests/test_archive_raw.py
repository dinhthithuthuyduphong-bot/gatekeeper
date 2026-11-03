import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("archive_raw", ROOT / "scripts" / "archive_raw.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def _sh(*a, cwd):
    subprocess.run(a, cwd=cwd, check=True, capture_output=True)


def _clone(tmp, bare, name):
    d = tmp / name
    _sh("git", "init", "-q", str(d), cwd=tmp)
    _sh("git", "remote", "add", "origin", str(bare), cwd=d)
    _sh("git", "config", "user.email", "t@t", cwd=d)
    _sh("git", "config", "user.name", "t", cwd=d)
    return d


def _batch(d, part):
    traj = d / "runs" / part / "none" / "agent" / "x__y-1" / "x__y-1.traj.json"
    traj.parent.mkdir(parents=True)
    traj.write_text(json.dumps({"info": {"exit_status": "Submitted"}}))
    res = d / "results" / "pilot" / f"{part}.json"
    res.parent.mkdir(parents=True, exist_ok=True)
    res.write_text(json.dumps({"name": part, "instances": ["x__y-1"], "skills": {}}))


def test_concurrent_writer_is_merged_not_overwritten(tmp_path, monkeypatch):
    """A68: B built its commit on a stale tip; its push is refused, it re-reads the tip, merges
    A's manifest entry with its own, and pushes. Both batches survive."""
    bare = tmp_path / "o.git"
    _sh("git", "init", "-q", "--bare", str(bare), cwd=tmp_path)
    a, b = _clone(tmp_path, bare, "a"), _clone(tmp_path, bare, "b")
    _batch(a, "sa-p00")
    _batch(b, "sb-p00")
    monkeypatch.setattr(m, "is_running", lambda part: False)
    monkeypatch.setattr(sys, "argv", ["archive_raw.py"])
    monkeypatch.chdir(b)
    stale = m.load_manifest()  # B reads the (empty) tip first ...
    monkeypatch.chdir(a)
    assert m.main() == 0  # ... A archives and pushes
    monkeypatch.chdir(b)
    real = m.load_manifest
    calls = {"n": 0}

    def first_stale():
        calls["n"] += 1
        return json.loads(json.dumps(stale)) if calls["n"] == 1 else real()

    monkeypatch.setattr(m, "load_manifest", first_stale)
    assert m.main() == 0
    out = subprocess.run(
        ["git", "show", "origin/raw-archive:archive/MANIFEST.json"],
        cwd=b,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    batches = json.loads(out)["batches"]
    assert {"sa-p00", "sb-p00"} <= set(batches)
    files = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", "origin/raw-archive"],
        cwd=b,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert any("sa-p00" in f for f in files) and any("sb-p00" in f for f in files)
