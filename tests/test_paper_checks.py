from gatekeeper.paper_checks import run_checks


def test_arithmetic_claims_reproduce():
    checks = {c.item: c for c in run_checks()}
    for item in [
        "Tổng cặp A+B+C",
        "Tỉ lệ harm A/B/C (%)",
        "Chênh lệch regime C/A",
        "Margin vs B6",
        "Margin vs B2",
        "Phần đã đạt bởi B6",
        "Cost B8/Gatekeeper",
        "Composition 41/46",
        "Repair GK−B9, GK−B1",
        "Phân loại lỗi 58+27+15",
    ]:
        assert checks[item].verdict == "ok", checks[item]
    assert checks["Ablation +8.8 / +7.5 / ×1.45 / ×1.34 / +7.8 / +0.8"].verdict == "ok"


def test_known_problems_are_flagged():
    checks = {c.item: c for c in run_checks()}
    assert checks["B2 harmful acceptance"].verdict == "inconsistent"
    assert checks["CI margin vs B6 vượt 5 điểm"].verdict == "wrong"
    assert checks["So sánh 'at matched clean reuse'"].verdict == "wrong"
    assert checks["d̄ (partner giao footprint)"].verdict == "clarify"
    assert checks["Prop. 9 mức tiết kiệm của pairing"].verdict == "wrong"
    assert "5.2" in checks["Prop. 9 mức tiết kiệm của pairing"].recomputed
