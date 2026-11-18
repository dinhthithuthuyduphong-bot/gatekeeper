import json
import sys
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "kaggle" / "scripts"))
import w7_analyse as wa  # noqa: E402


def _run(tmp: Path, name: str, issues: int, with_g: int) -> Path:
    run = tmp / name
    (run / "pairs").mkdir(parents=True)
    (run / "candidates").mkdir()
    pairs, cands = [], []
    for k in range(issues):
        iid = f"pallets__jinja-{k + 1}"
        pid = f"{iid}::f::p"
        pairs.append({"instance_id": iid, "pair_id": pid})
        rule = "Run `git log -n 5` and inspect the bug commit." if k < with_g else "Run the tests."
        cands.append({"pair_id": pid, "rule": rule})
    (run / "pairs" / "pairs.jsonl").write_text("".join(json.dumps(p) + "\n" for p in pairs))
    (run / "candidates" / "process_delta.jsonl").write_text(
        "".join(json.dumps(c) + "\n" for c in cands)
    )
    return run


def test_fisher_matches_hypergeometric_tail():
    p = wa.fisher_greater(5, 6, 0, 6)
    assert abs(p - comb(6, 5) * comb(6, 0) / comb(12, 5)) < 1e-12


def test_issue_level_indicator_and_gate(tmp_path):
    a = _run(tmp_path, "A", issues=31, with_g=25)
    b = _run(tmp_path, "B", issues=6, with_g=0)
    res = wa.analyse(a, b, alpha=0.025, min_issues_b=5)
    assert res["A"]["issues_G"] == 25 and res["B"]["issues_G"] == 0
    assert res["test_run"] and res["reject_G"]
    small = _run(tmp_path, "B2", issues=3, with_g=0)
    res2 = wa.analyse(a, small, alpha=0.025, min_issues_b=5)
    assert not res2["test_run"] and not res2["reject_G"]
