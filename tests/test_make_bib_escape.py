import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import make_bib  # noqa: E402


def test_commands_in_titles_print_as_written():
    t = make_bib.bib_escape("(`git checkout HEAD~1 -- .`) and --hide-git-history, 5% & #6 a_b")
    assert "HEAD\\textasciitilde{}1" in t
    assert "-{}-hide-git-history" in t and "-{}- ." in t
    assert "--" not in t
    assert t.startswith("(\\textasciigrave{}git")
    assert "5\\%" in t and "\\&" in t and "\\#6" in t and "a\\_b" in t
