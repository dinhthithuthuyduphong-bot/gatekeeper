import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ease_pdf_check  # noqa: E402
import preflight  # noqa: E402

GOOD = "\n".join(
    [
        preflight.EASE_CLASS,
        preflight.EASE_CONF,
        r"\begin{document}",
        r"A gain of 5\% % a comment that says the author",
        r"\section{Conclusion}",
        "Done.",
        r"\section*{Data Availability}",
        "A package.",
        r"\bibliography{refs}",
    ]
)


def write(tmp_path, text):
    p = tmp_path / "main.tex"
    p.write_text(text)
    return p


def test_good_source_passes(tmp_path):
    assert preflight.check_ease(write(tmp_path, GOOD), owner="someowner", repo="somerepo") == []


def test_wrong_class_and_conference(tmp_path):
    t = GOOD.replace("review,anonymous", "review").replace("15--18", "16--18")
    bad = preflight.check_ease(write(tmp_path, t), owner="x", repo="somerepo")
    assert any(b.startswith("E-F4") for b in bad) and any(b.startswith("E-F5") for b in bad)


def test_data_availability_must_follow_conclusion(tmp_path):
    t = GOOD.replace(r"\section{Conclusion}", "").replace(
        r"\begin{document}", r"\begin{document}" + "\n" + r"\section{Conclusion}"
    )
    assert preflight.check_ease(write(tmp_path, t), owner="x", repo="somerepo") == []
    t2 = GOOD.replace(r"\section*{Data Availability}", "").replace(
        r"\begin{document}", r"\begin{document}" + "\n" + r"\section*{Data Availability}"
    )
    bad = preflight.check_ease(write(tmp_path, t2), owner="x", repo="somerepo")
    assert any(b.startswith("E-O2") for b in bad)


def test_anonymity(tmp_path):
    t = GOOD.replace("Done.", r"\author{X} As in our previous work, the author ran someowner/repo.")
    bad = preflight.check_ease(write(tmp_path, t), owner="someowner", repo="somerepo")
    codes = {b.split(":")[0] for b in bad}
    assert codes == {"E-A1", "E-A2", "E-A3"}
    assert sum(b.startswith("E-A1") for b in bad) == 2


def test_comment_is_ignored_but_escaped_percent_kept(tmp_path):
    # 'the author' sits after an unescaped %, so it is a comment; '5\%' must not start a comment
    assert preflight.check_ease(write(tmp_path, GOOD), owner="x", repo="somerepo") == []


def test_pdf_pages():
    main9 = ["text"] * 8 + ["end\n  REFERENCES  \n[1] a"] + ["[2] b"] * 2
    assert ease_pdf_check.evaluate(main9, "") == []
    too_long = ["text"] * 10 + ["REFERENCES"] + ["[2]"]
    assert any("page 11" in b for b in ease_pdf_check.evaluate(too_long, ""))
    many_refs = ["text"] * 5 + ["REFERENCES"] + ["[2]"] * 3
    assert any("3 pages" in b for b in ease_pdf_check.evaluate(many_refs, ""))
    assert any(b.startswith("E-A1") for b in ease_pdf_check.evaluate(main9, "Someone"))


def test_mandatory_warnings():
    log = (
        "Class acmart Warning: CCS concepts are mandatory for papers over two pages.\n"
        "Class acmart Warning: some other warning\n"
    )
    w = ease_pdf_check.mandatory_warnings(log)
    assert w == ["CCS concepts are mandatory for papers over two pages."]


def test_placeholder_link_fails():
    pages = ["see (ANON-\nLINK-PENDING)", "REFERENCES"]
    assert any(b.startswith("E-A4") for b in ease_pdf_check.evaluate(pages, ""))


def test_repository_name_is_a_search_key(tmp_path):
    t = GOOD.replace("Done.", "We call the test Gatekeeper.")
    bad = preflight.check_ease(write(tmp_path, t), owner="x", repo="gatekeeper")
    assert any("repository name" in b for b in bad)
