import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import preflight  # noqa: E402

BIB = """@misc{a,
  title = {x},
  howpublished = {\\url{https://example.org/f.py}}
}

@misc{b,
  title = {y},
  howpublished = {\\url{https://example.org/f.py}}
}

@misc{c,
  title = {z},
  howpublished = {\\url{https://example.org/g.py}}
}
"""


def test_duplicate_url_among_cited_keys(tmp_path):
    bib = tmp_path / "refs.bib"
    bib.write_text(BIB)
    tex = tmp_path / "main.tex"
    tex.write_text(r"see~\cite{a,c} and~\cite{b}")
    bad = preflight.check_bib_duplicates(tex, bib)
    assert len(bad) == 1 and "a and b" in bad[0]


def test_uncited_duplicate_is_ignored(tmp_path):
    bib = tmp_path / "refs.bib"
    bib.write_text(BIB)
    tex = tmp_path / "main.tex"
    tex.write_text(r"see~\cite{a,c}")
    assert preflight.check_bib_duplicates(tex, bib) == []
