import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "rq1_mini", Path(__file__).parents[1] / "scripts" / "rq1_mini.py"
)
rq = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rq)


def test_rules_and_summary():
    lucky_noise = [-1.0] * 3 + [0.0] * 37  # looks helpful on the screen, truth harmful
    strong = [-1.0] * 25 + [0.0] * 15
    cells = {
        "noise": {
            "decisions": rq.decide(lucky_noise, 0.05 / 2),
            "label": "harmful",
            "str_true": 0.1,
        },
        "good": {"decisions": rq.decide(strong, 0.05 / 2), "label": "beneficial", "str_true": -0.3},
    }
    s = rq.summarise(cells)
    assert s["Plug-in (mean < 0)"]["harmful_acceptance"] == 1.0  # naive admits the noise
    assert s["Gatekeeper"]["harmful_acceptance"] == 0.0  # anytime-valid test does not
    assert s["Gatekeeper"]["clean_reuse_coverage"] == 1.0  # but admits the strong skill
    assert s["B2 always"]["harmful_acceptance"] == 1.0 and s["B1 never"]["admitted"] == 0


def test_tested_labels_keep_undetermined():
    assert rq.label_tested([1.0] * 20, 0.05) == "harmful"
    assert rq.label_tested([-1.0] * 20, 0.05) == "beneficial"
    assert rq.label_tested([1.0, -1.0] * 10, 0.05) == "undetermined"
    cells = {
        "h": {"decisions": {"G": False, "N": True}, "label_tested": "harmful"},
        "u": {"decisions": {"G": False, "N": True}, "label_tested": "undetermined"},
    }
    s = rq.summarise_tested(cells)
    assert s["N"]["harmful_acceptance"] == 1.0 and s["G"]["harmful_acceptance"] == 0.0
    assert s["N"]["admitted_undetermined"] == 1 and s["N"]["clean_reuse_coverage"] is None
