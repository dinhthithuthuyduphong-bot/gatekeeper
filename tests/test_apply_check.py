import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apply_check  # noqa: E402


def _repo(tmp_path):
    work = tmp_path / "w"
    work.mkdir()
    g = ["git", "-C", str(work), "-c", "user.email=a@b", "-c", "user.name=a"]
    subprocess.run(["git", "init", "-q", str(work)], check=True)
    (work / "f.py").write_text("a = 1\nb = 2\n")
    subprocess.run([*g, "add", "."], check=True)
    subprocess.run([*g, "commit", "-qm", "Initial commit"], check=True)
    (work / "f.py").write_text("a = 1\nb = 3\n")
    subprocess.run([*g, "commit", "-qam", "Bug Patch"], check=True)
    (work / "t.py").write_text("x\n")
    subprocess.run([*g, "add", "."], check=True)
    subprocess.run([*g, "commit", "-qm", "Remove F2P Tests"], check=True)
    subprocess.run([*g, "branch", "-q", "-M", "task1"], check=True)
    bare = tmp_path / "m.git"
    subprocess.run(["git", "clone", "-q", "--mirror", str(work), str(bare)], check=True)
    return bare


def test_check_passes_clean_patch_and_fails_stale_one(tmp_path):
    bare = _repo(tmp_path)
    c = apply_check.bug_commit(bare, "task1")
    good = "--- a/f.py\n+++ b/f.py\n@@ -1,2 +1,2 @@\n a = 1\n-b = 3\n+b = 2\n"
    stale = "--- a/f.py\n+++ b/f.py\n@@ -1,2 +1,2 @@\n a = 1\n-b = 9\n+b = 2\n"
    assert apply_check.check(bare, c, good)
    assert not apply_check.check(bare, c, stale)
