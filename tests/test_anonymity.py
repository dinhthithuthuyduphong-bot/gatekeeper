import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "check_anonymity", Path(__file__).parents[1] / "scripts" / "check_anonymity.py"
)
anon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(anon)


def test_detects_leaks(tmp_path):
    (tmp_path / "a.md").write_text("contact jane.doe@uni.edu or github.com/janedoe\n")
    (tmp_path / "b.py").write_text(
        "# Co-Authored-By: x <noreply@anthropic.com>\nAUTHOR = 'Jane Doe'\n"
    )
    (tmp_path / "p.pdf").write_bytes(b"%PDF-1.4 /Author (Jane Doe) /Producer (pdfTeX)")
    kinds = {(f["kind"], f["match"]) for f in anon.scan(tmp_path, ["Jane Doe"])}
    assert ("email", "jane.doe@uni.edu") in kinds
    assert ("account-url", "github.com/janedoe") in kinds
    assert ("name", "Jane Doe") in kinds
    assert ("pdf-author", "Jane Doe") in kinds
    assert not any(m == "noreply@anthropic.com" for _, m in kinds)


def test_clean_dir(tmp_path):
    (tmp_path / "x.py").write_text("print('anonymous')\n")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("me@example.com")
    assert anon.scan(tmp_path, []) == []


def test_pdf_anonymous_author_is_not_a_leak(tmp_path):
    (tmp_path / "anon.pdf").write_bytes(
        rb"/Author (\376\377\000A\000n\000o\000n\000y\000m\000o\000u\000s)"
    )
    assert anon.scan(tmp_path, []) == []
    assert anon._pdf_string(rb"\376\377\000J\000o") == "Jo"


def test_named_only_keeps_named_addresses_and_drops_third_party(tmp_path):
    (tmp_path / "patch.json").write_text(
        "author dev@golang.org see github.com/blevesearch; jane.doe@uni.edu github.com/janedoe\n"
    )
    found = {f["match"] for f in anon.scan(tmp_path, ["janedoe", "jane.doe"], named_only=True)}
    assert "jane.doe@uni.edu" in found and "github.com/janedoe" in found
    assert "dev@golang.org" not in found and "github.com/blevesearch" not in found
    # without the flag every address is reported
    loose = {f["match"] for f in anon.scan(tmp_path, [])}
    assert "dev@golang.org" in loose
