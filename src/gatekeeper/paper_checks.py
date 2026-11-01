"""Re-derive every arithmetic claim of the FSE-2027-13 draft (TODO.md section 2).

All inputs are the *projected* numbers printed in docs/01-FSE-2027-13-paper.pdf.
Each check returns (claimed, recomputed, verdict) so the report can show the table.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

__all__ = ["Check", "PAPER", "run_checks"]

# Values as printed in the paper (Tables 1-3, abstract, RQ text).
PAPER = {
    "pairs": {"A": 68, "B": 74, "C": 38, "total": 180},
    "harmful": {"A": 14, "B": 27, "C": 22},
    "harm_rate_pct": {"A": 20.6, "B": 36.5, "C": 57.9},
    "regime_ratio": 2.8,
    "skills_in_library": 94,
    "scope_classes": 17,
    "footprint_overlap_pct": 11.4,
    "dbar": 0.34,
    "sigma_ratio": 2.1,
    "pairing_savings_claim": 3.1,
    "harmful_acc": {"B2": 22.7, "B6": 11.5, "B8": 2.4, "GK": 5.1},
    "clean_reuse": {"B2": 100.0, "B6": 86.0, "B8": 79.3, "GK": 84.3},
    "margin_ci_B6": (3.1, 9.8),
    "margin_threshold": 5.0,
    "naive_share_pct": 64,
    "cost": {"B8": 3.87, "GK": 2.02},
    "cost_ratio_claim": 1.9,
    "composition": {"caught": 41, "total": 46, "pct": 89.1},
    "ablation": {
        "full": (5.1, 84.3, 2.02),
        "no_scope": (13.9, 88.6, 1.71),
        "unpaired": (7.8, 79.1, 2.94),
        "no_composition": (12.6, 86.0, 1.83),
        "no_alloc": (5.4, 81.2, 2.71),
        "no_margin": (5.9, 92.1, 2.02),
    },
    "repair": {"GK": 52.3, "B9": 49.8, "B1": 44.1},
    "failure_taxonomy_pct": (58, 27, 15),
}


@dataclass(frozen=True)
class Check:
    item: str
    claimed: str
    recomputed: str
    verdict: str  # "ok" | "wrong" | "inconsistent" | "clarify"
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _close(a: float, b: float, tol: float = 0.051) -> bool:
    return abs(a - b) <= tol


def run_checks(p: dict = PAPER) -> list[Check]:
    out: list[Check] = []
    pr, hm = p["pairs"], p["harmful"]

    tot = pr["A"] + pr["B"] + pr["C"]
    out.append(
        Check("Tổng cặp A+B+C", str(pr["total"]), str(tot), "ok" if tot == pr["total"] else "wrong")
    )
    rates = {k: 100 * hm[k] / pr[k] for k in "ABC"}
    ok_rates = all(_close(rates[k], p["harm_rate_pct"][k]) for k in "ABC")
    out.append(
        Check(
            "Tỉ lệ harm A/B/C (%)",
            " / ".join(f"{p['harm_rate_pct'][k]}" for k in "ABC"),
            " / ".join(f"{rates[k]:.1f}" for k in "ABC"),
            "ok" if ok_rates else "wrong",
        )
    )
    ratio = rates["C"] / rates["A"]
    out.append(
        Check(
            "Chênh lệch regime C/A",
            f"{p['regime_ratio']}×",
            f"{ratio:.2f}×",
            "ok" if _close(ratio, p["regime_ratio"], 0.05) else "wrong",
        )
    )

    ha = p["harmful_acc"]
    m6, m2 = ha["B6"] - ha["GK"], ha["B2"] - ha["GK"]
    out.append(Check("Margin vs B6", "6.4", f"{m6:.1f}", "ok" if _close(m6, 6.4) else "wrong"))
    out.append(Check("Margin vs B2", "17.6", f"{m2:.1f}", "ok" if _close(m2, 17.6) else "wrong"))
    share = 100 * (ha["B2"] - ha["B6"]) / m2
    out.append(
        Check(
            "Phần đã đạt bởi B6",
            f"~{p['naive_share_pct']}%",
            f"{share:.1f}%",
            "ok" if abs(share - p["naive_share_pct"]) < 1 else "wrong",
        )
    )
    cr = p["cost"]["B8"] / p["cost"]["GK"]
    out.append(
        Check(
            "Cost B8/Gatekeeper",
            f"{p['cost_ratio_claim']}×",
            f"{cr:.2f}×",
            "ok" if _close(cr, p["cost_ratio_claim"]) else "wrong",
        )
    )
    c = p["composition"]
    cp = 100 * c["caught"] / c["total"]
    out.append(
        Check(
            "Composition 41/46",
            f"{c['pct']}%",
            f"{cp:.1f}%",
            "ok" if _close(cp, c["pct"]) else "wrong",
        )
    )

    ab = p["ablation"]
    full = ab["full"]
    d_scope = ab["no_scope"][0] - full[0]
    d_comp = ab["no_composition"][0] - full[0]
    x_pair = ab["unpaired"][2] / full[2]
    x_alloc = ab["no_alloc"][2] / full[2]
    d_cov = ab["no_margin"][1] - full[1]
    d_harm = ab["no_margin"][0] - full[0]
    ok_ab = (
        _close(d_scope, 8.8)
        and _close(d_comp, 7.5)
        and _close(x_pair, 1.45, 0.01)
        and _close(x_alloc, 1.34, 0.01)
        and _close(d_cov, 7.8)
        and _close(d_harm, 0.8)
    )
    out.append(
        Check(
            "Ablation +8.8 / +7.5 / ×1.45 / ×1.34 / +7.8 / +0.8",
            "như paper",
            f"+{d_scope:.1f} / +{d_comp:.1f} / ×{x_pair:.2f} / ×{x_alloc:.2f}"
            f" / +{d_cov:.1f} / +{d_harm:.1f}",
            "ok" if ok_ab else "wrong",
        )
    )
    rp = p["repair"]
    out.append(
        Check(
            "Repair GK−B9, GK−B1",
            "2.5 / 8.2",
            f"{rp['GK'] - rp['B9']:.1f} / {rp['GK'] - rp['B1']:.1f}",
            "ok"
            if _close(rp["GK"] - rp["B9"], 2.5) and _close(rp["GK"] - rp["B1"], 8.2)
            else "wrong",
        )
    )
    tx = sum(p["failure_taxonomy_pct"])
    out.append(Check("Phân loại lỗi 58+27+15", "100%", f"{tx}%", "ok" if tx == 100 else "wrong"))

    # ---- the four issues
    n_harm = sum(hm.values())
    b2_if_def = 100.0  # B2 admits everything; harmful acceptance = admitted harmful / harmful
    b2_if_all = 100 * n_harm / tot
    out.append(
        Check(
            "B2 harmful acceptance",
            f"{ha['B2']}%",
            f"{b2_if_def:.0f}% (theo định nghĩa) hoặc {b2_if_all:.1f}% (trên mọi cặp)",
            "inconsistent",
            "B2 admit mọi skill (clean reuse 100%), nên không thể là 22,7%",
        )
    )
    lo, hi = p["margin_ci_B6"]
    out.append(
        Check(
            "CI margin vs B6 vượt 5 điểm",
            f"[{lo}, {hi}] vượt",
            f"cận dưới {lo} {'>' if lo > p['margin_threshold'] else '<'} {p['margin_threshold']}",
            "ok" if lo > p["margin_threshold"] else "wrong",
            "Chỉ ước lượng điểm vượt 5, CI thì không",
        )
    )
    cg, c6 = p["clean_reuse"]["GK"], p["clean_reuse"]["B6"]
    out.append(
        Check(
            "So sánh 'at matched clean reuse'",
            f"{cg} vs {c6}",
            "không bằng nhau" if cg != c6 else "bằng nhau",
            "ok" if cg == c6 else "wrong",
            "Cần đường harm–coverage và so tại cùng coverage",
        )
    )
    partners = p["footprint_overlap_pct"] / 100 * (p["skills_in_library"] - 1)
    out.append(
        Check(
            "d̄ (partner giao footprint)",
            f"{p['dbar']}",
            f"{partners:.1f} nếu tính toàn library",
            "clarify",
            "Chỉ đúng nếu tính trong từng scope L_s; phải ghi rõ",
        )
    )
    corrected = 1 + 2 * p["sigma_ratio"]
    out.append(
        Check(
            "Prop. 9 mức tiết kiệm của pairing",
            f"{p['pairing_savings_claim']}× (net 1.55×)",
            f"{corrected:.1f}×",
            "ok" if _close(corrected, p["pairing_savings_claim"]) else "wrong",
            "Đúng là 1 + 2σ_T²/σ_S²; unpaired cũng tốn 2 lần chạy/mẫu",
        )
    )
    return out
