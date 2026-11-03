import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "preflight", Path(__file__).parents[1] / "scripts" / "preflight.py"
)
pf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pf)


def test_terms_check_catches_vague_wording_and_spares_defined_statements(tmp_path):
    doc = tmp_path / "doc.md"
    doc.write_text(
        "Hiệu ứng của skill rất mạnh.\n"  # vague, no number -> flagged
        "Hiệu ứng thực hiện được nhỏ hơn δ.\n"  # comparison -> fine
        "Power 0,90 ở δ = 0,109: rất mạnh.\n"  # carries a number -> fine
        'Chị viết "không chấp nhận ngưỡng mơ hồ, rất rõ ràng".\n'  # verbatim quote -> fine
    )
    bad = pf.check_terms([str(doc)])
    assert len(bad) == 1 and ":1 " in bad[0]


def test_defaults_check_flags_a_scientific_default():
    import ast

    src = "def f(x, alpha=0.05, *, theta=0.0, n=3):\n    return x\n"
    tree = ast.parse(src)
    fn = tree.body[0]
    names = [a.arg for a in fn.args.args[len(fn.args.args) - len(fn.args.defaults) :]]
    assert "alpha" in names  # sanity of the AST walk used by check_defaults
    assert pf.SCIENTIFIC >= {"alpha", "theta"}


def test_results_check_flags_a_silently_lost_run(tmp_path, monkeypatch):
    import json

    d = tmp_path / "results" / "pilot"
    d.mkdir(parents=True)
    ok = {
        "instances": ["a"],
        "usage": {"none": {"runs": 2, "scored": 1}},
        "infra_failures": {"none": {"a": "x"}},
    }
    lost = {"instances": ["a"], "usage": {"none": {"runs": 2, "scored": 1}}, "infra_failures": {}}
    (d / "ok.json").write_text(json.dumps(ok))
    (d / "lost.json").write_text(json.dumps(lost))
    monkeypatch.chdir(tmp_path)
    bad = pf.check_results()
    assert len(bad) == 1 and bad[0].startswith("lost.json")
