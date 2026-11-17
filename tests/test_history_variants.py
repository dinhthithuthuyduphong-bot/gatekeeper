import importlib.util
import subprocess
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "history_variants", Path(__file__).parents[1] / "scripts" / "history_variants.py"
)
hv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hv)


def git(root, *a, env=None):
    return subprocess.run(
        ["git", *a], cwd=root, check=True, capture_output=True, text=True, env=env
    ).stdout.strip()


def make_task(tmp_path):
    """A three-commit history shaped like a SWE-smith task, with a remote and a mirror."""
    root, mirror = tmp_path / "testbed", tmp_path / "mirror.git"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    env = {
        "GIT_AUTHOR_NAME": "swesmith",
        "GIT_AUTHOR_EMAIL": "s@x",
        "GIT_COMMITTER_NAME": "swesmith",
        "GIT_COMMITTER_EMAIL": "s@x",
        "PATH": "/usr/bin:/bin",
        "HOME": str(tmp_path),
    }
    (root / "src.py").write_text("def f(x):\n    return x + 1\n")
    (root / "tests").mkdir()
    (root / "tests" / "test_f.py").write_text("def test_f():\n    assert f(1) == 2\n")
    for msg, date, change in [
        ("Initial commit", "2025-01-01T00:00:00+00:00", None),
        ("Bug Patch", "2025-01-02T00:00:00+07:00", ("src.py", "def f(x):\n    return x - 1\n")),
        ("Remove F2P Tests", "2025-01-03T00:00:00+00:00", ("tests/test_f.py", None)),
    ]:
        if change and change[1] is None:
            (root / change[0]).unlink()
        elif change:
            (root / change[0]).write_text(change[1])
        git(root, "add", "-A")
        e = {**env, "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}
        git(root, "commit", "-q", "-m", msg, env=e)
    git(tmp_path, "clone", "-q", "--mirror", str(root), str(mirror))
    git(root, "remote", "add", "origin", str(mirror))
    git(root, "tag", "v0", "HEAD~2")
    return root, mirror


@pytest.mark.parametrize("detached", [False, True])
@pytest.mark.parametrize("variant", hv.VARIANTS)
def test_variants(tmp_path, variant, detached):
    root, mirror = make_task(tmp_path)
    if detached:
        git(root, "checkout", "-q", "--detach")
    shipped = {k: git(root, "rev-parse", f"HEAD{k}") for k in ("", "~1", "~2")}
    trees = {k: git(root, "rev-parse", f"HEAD{k}^{{tree}}") for k in ("", "~1", "~2")}
    msg = "Update source" if variant == "B" else None
    sh = hv.history_variant_sh(variant, msg, str(root), str(mirror))
    r = subprocess.run(["bash", "-c", sh], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip().splitlines()[-1] == hv.expected_check(variant)
    assert not mirror.exists()
    assert git(root, "rev-parse", "HEAD^{tree}") == trees[""]  # agent works on the same tree
    assert git(root, "status", "--porcelain") == ""
    refs = git(root, "for-each-ref", "--format=%(refname)").splitlines()
    assert refs == ([] if detached else ["refs/heads/main"])
    subjects = git(root, "log", "--format=%s").splitlines()
    # "Remove F2P Tests" (T1 -> T2) identical in every variant
    assert subjects[0] == "Remove F2P Tests"
    assert git(root, "diff", "HEAD~1", "HEAD") == git(root, "diff", trees["~1"], trees[""])
    # raw date (epoch and offset): the ISO form differs between git versions ("Z" or "+00:00")
    assert git(root, "log", "-1", "--date=raw", "--format=%an %ad|%cd", "HEAD") == (
        "swesmith 1735862400 +0000|1735862400 +0000"
    )
    if variant == "A":
        assert git(root, "rev-parse", "HEAD") == shipped[""]  # metadata kept bit for bit
    if variant == "B":
        assert subjects == ["Remove F2P Tests", "Update source", "Initial commit"]
        assert "return x - 1" in git(root, "show", "HEAD~1")
    if variant == "C":
        assert subjects == ["Remove F2P Tests", "Bug Patch", "Initial commit"]
        assert git(root, "diff", "HEAD~2", "HEAD~1") == ""
        assert "return x + 1" not in git(root, "log", "-p", "--all")
    if variant == "D":
        assert subjects == ["Remove F2P Tests", "Initial commit"]
        assert "return x + 1" not in git(root, "log", "-p", "--all")


def test_neutral_message_rules():
    with pytest.raises(ValueError):
        hv.history_variant_sh("B", None, "/t", "/m")
    with pytest.raises(ValueError):
        hv.history_variant_sh("A", "x", "/t", "/m")
    with pytest.raises(ValueError):
        hv.history_variant_sh("B", "Bug fix", "/t", "/m")
    with pytest.raises(ValueError):
        hv.history_variant_sh("E", None, "/t", "/m")
