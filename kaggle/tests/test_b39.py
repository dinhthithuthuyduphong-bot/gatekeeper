import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "kaggle" / "scripts"))
import b39_analyse as ba  # noqa: E402

NB = ROOT / "kaggle" / "notebooks"


def _body(p: Path) -> list[str]:
    s = p.read_text()
    return s[s.index("# " + "-" * 98) :].splitlines()


def test_b39_cell_is_a38_cell_outside_its_config_block():
    assert _body(NB / "a38_run_cell.py") == _body(NB / "b39_run_cell.py")


def test_b39_cell_config():
    ns = {"__name__": "cell_test"}
    exec(compile((NB / "b39_run_cell.py").read_text(), "b39", "exec"), ns)
    assert ns["NAME"] == "b39" and ns["SEEDS"] == (1,) and ns["TEMPERATURE"] is None
    assert ns["ITEM_CAP_USD"] == 8.0 and ns["MODELS"] == {}


def test_analysis_counts_and_bound():
    prompts = [
        {"sha256": f"s{i}", "condition": c} for i, c in enumerate(["real"] * 4 + ["sham", "plain"])
    ]
    yes = '{"attributed": true, "confidence": 0.9, "category": "task_implementation_fault"}'
    no = '{"attributed": false, "confidence": 0.9, "category": "not_caused_by_skill"}'
    res = [
        {"sha256": "s0", "model": "m", "ok": True, "response": yes},
        {"sha256": "s1", "model": "m", "ok": True, "response": yes},
        {"sha256": "s2", "model": "m", "ok": True, "response": "no json here"},
        {"sha256": "s3", "model": "m", "ok": True, "response": no},
        {"sha256": "s4", "model": "m", "ok": True, "response": yes},
        {"sha256": "s5", "model": "m", "ok": True, "response": no},
        {"sha256": "s5", "model": "m", "ok": False, "error": "x"},
    ]
    e = ba.analyse(prompts, res, 0.25)["auditors"]["m"]
    assert e["unparsed"] == 1 and e["n_ok"] == 6
    assert e["real"] == {"k": 2, "n": 4, "share": 0.5, "lower_bound": 0.25}
    assert e["sham"]["k"] == 1 and e["plain"]["k"] == 0


def test_cp95_matches_paper_convention():
    lo, hi = ba.cp95(25, 25)
    assert lo == pytest.approx(0.8628, abs=1e-4) and hi == 1.0
    assert ba.cp95(0, 25)[0] == 0.0


def test_paper_counts_reproduced_from_saved_rows():
    # the analysis rule applied to the saved Gemini rows gives the paper's 25, 3, 5 of 25
    for f, k in (("sham_audit", 25), ("sham_audit_flash", 3), ("sham_audit_pro", 5)):
        rows = json.loads((ROOT / "results" / f"{f}.json").read_text())["rows"]
        sham = [r for r in rows if r["condition"] == "sham"]
        assert sum(bool((r.get("decision") or {}).get("attributed")) for r in sham) == k
