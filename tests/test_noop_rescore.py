import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import noop_rescore as nr  # noqa: E402


def test_noop_patch_applies_and_adds_only_a_comment(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "p.diff").write_text(nr.NOOP_PATCH)
    r = subprocess.run(["git", "apply", "p.diff"], cwd=tmp_path, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "gk_noop.py").read_text() == "# no-op\n"


def test_targets_are_fixed_and_sized():
    t = nr.targets()
    assert len(t) == 40 and len(set(t)) == 40
    assert t == nr.targets()  # deterministic
