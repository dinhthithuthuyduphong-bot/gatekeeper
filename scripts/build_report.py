"""Build report/index.html: from theory to experiments (TODO.md Phase H).

Inputs (all optional except TODO.md):
  TODO.md                        -> progress per phase (checkbox counts)
  results/simulation.json        -> feasibility simulation (section 4)
  results/confseq_crosscheck.json-> cross-check against confseq (R1)
  results/junit.xml              -> unit-test outcome (pytest --junitxml)

Usage: python scripts/build_report.py [--out report/index.html]
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def esc(x: object) -> str:
    return html.escape(str(x))


def load_json(rel: str) -> dict | None:
    p = ROOT / rel
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def todo_progress() -> list[tuple[str, int, int]]:
    phases: list[tuple[str, int, int]] = []
    current = None
    done = total = 0
    for line in (ROOT / "TODO.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^### (Phase .+)$", line)
        if m:
            if current:
                phases.append((current, done, total))
            current, done, total = m.group(1), 0, 0
            continue
        if line.startswith("## ") and current:
            phases.append((current, done, total))
            current = None
        if current and re.match(r"^- \[( |x|X)\] ", line):
            total += 1
            done += line[3] in "xX"
    if current:
        phases.append((current, done, total))
    return phases


def junit_summary() -> dict | None:
    p = ROOT / "results" / "junit.xml"
    if not p.exists():
        return None
    root = ET.parse(p).getroot()
    suites = [root] if root.tag == "testsuite" else list(root)
    tot = {k: 0 for k in ("tests", "failures", "errors", "skipped")}
    cases = []
    for s in suites:
        for k in tot:
            tot[k] += int(s.get(k, 0))
        for c in s.iter("testcase"):
            status = "pass"
            if c.find("failure") is not None or c.find("error") is not None:
                status = "fail"
            elif c.find("skipped") is not None:
                status = "skip"
            cases.append((c.get("classname", ""), c.get("name", ""), status))
    tot["cases"] = cases
    return tot


def pct(x: float | None) -> str:
    return "—" if x is None else f"{100 * x:.1f}%".replace(".", ",")


def num(x: float | None) -> str:
    if x is None:
        return "—"
    return f"{x:,.0f}".replace(",", ".")


def admit_chart(grid: list[dict]) -> str:
    """Inline SVG: admission rate vs true STR at the Bonferroni cell alpha."""
    pts = sorted((r["str_true"], r["admit_rate"]) for r in grid if r["alpha"] < 0.01)
    if not pts:
        return ""
    w, h, pl, pr, pt, pb = 560, 260, 48, 16, 16, 40
    xs = [p[0] for p in pts]
    x0, x1 = min(xs), max(xs)

    def X(v: float) -> float:
        return pl + (v - x0) / (x1 - x0) * (w - pl - pr)

    def Y(v: float) -> float:
        return pt + (1 - v) * (h - pt - pb)

    path = " ".join(
        f"{'M' if i == 0 else 'L'}{X(a):.1f},{Y(b):.1f}" for i, (a, b) in enumerate(pts)
    )
    grid_lines = "".join(
        f'<line x1="{pl}" x2="{w - pr}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" class="gl"/>'
        f'<text x="{pl - 8}" y="{Y(t) + 4:.1f}" class="tick" text-anchor="end">{int(t * 100)}%</text>'
        for t in (0, 0.25, 0.5, 0.75, 1)
    )
    xt = "".join(
        f'<text x="{X(a):.1f}" y="{h - pb + 18}" class="tick" text-anchor="middle">'
        f"{str(a).replace('.', ',')}</text>"
        for a, _ in pts
    )
    dots = "".join(
        f'<circle cx="{X(a):.1f}" cy="{Y(b):.1f}" r="4" class="dot"><title>STR {a}: {pct(b)}</title></circle>'
        for a, b in pts
    )
    return f"""
<figure class="chart">
<svg viewBox="0 0 {w} {h}" role="img" aria-label="Tỉ lệ admit theo STR thật">
{grid_lines}{xt}
<path d="{path}" class="line"/>{dots}
<text x="{(pl + w - pr) / 2}" y="{h - 4}" class="axis" text-anchor="middle">STR thật của skill (θ = 0,05)</text>
</svg>
<figcaption>Tỉ lệ skill tốt được admit với α mỗi ô = 3,1e-5 (Bonferroni trên ~1.600 ô),
budget 2.000 cặp trial. Skill phải tốt hơn khoảng 3θ mới gần như chắc được admit.</figcaption>
</figure>"""


VERDICT = {
    "ok": ("ok", "Đúng"),
    "wrong": ("bad", "Sai"),
    "inconsistent": ("bad", "Mâu thuẫn"),
    "clarify": ("warn", "Cần giải thích"),
}


def paper_checks_html() -> str:
    try:
        from gatekeeper.paper_checks import run_checks
    except ImportError:
        return "<p class='muted'>Cài package (<code>pip install -e .</code>) để sinh bảng này.</p>"
    rows = []
    for c in run_checks():
        cls, label = VERDICT[c.verdict]
        note = f"<br><span class='muted'>{esc(c.note)}</span>" if c.note else ""
        rows.append(
            f"<tr><td>{esc(c.item)}</td><td>{esc(c.claimed)}</td><td>{esc(c.recomputed)}</td>"
            f"<td class='{cls}'>{label}{note}</td></tr>"
        )
    return (
        "<div class='tbl'><table><thead><tr><th>Chỗ</th><th>Paper</th><th>Tính lại</th>"
        f"<th>Kết luận</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
    )


def benchmarks_html(summary: dict | None, sim: dict | None) -> str:
    if not summary:
        return (
            "<p class='muted'>Chưa có <code>data/benchmarks/summary.json</code> "
            "(workflow <code>Data snapshots</code> sinh ra).</p>"
        )
    need = None
    if sim:
        meds = [r["median_trials_admitted"] for r in sim["grid"] if r["alpha"] < 0.01]
        meds = [m for m in meds if m]
        need = min(meds) if meds else None
    rows = []
    for name, v in summary.items():
        if not isinstance(v, dict) or "status" not in v:
            continue
        if v["status"] != "ok":
            rows.append(
                f"<tr><td>{esc(name)}</td><td colspan='5' class='bad'>không tải được</td></tr>"
            )
            continue
        top = list(v.get("top_repo_versions", {}).values())
        enough = sum(1 for n in top if need and n >= need)
        rng = v.get("created_at_range") or ["", ""]
        rows.append(
            f"<tr><td>{esc(name)}</td><td class='n'>{num(v['n_tasks'])}</td>"
            f"<td class='n'>{num(v['n_repos'])}</td><td class='n'>{num(v['n_repo_versions'])}</td>"
            f"<td class='n'>{num(max(top) if top else None)}</td>"
            f"<td>{esc(rng[0])} → {esc(rng[1])}</td></tr>"
        )
        if need is not None:
            rows[-1] = rows[-1].replace("</tr>", f"<td class='n'>{enough}</td></tr>")
    head = (
        "<th>Benchmark</th><th>Task</th><th>Repo</th><th>(repo, version)</th>"
        "<th>Task nhiều nhất / scope</th><th>Ngày tạo</th>"
    )
    if need is not None:
        head += f"<th>Scope ≥ {num(need)} task</th>"
    overlap = summary.get("repo_overlap", {})
    ov = "".join(f"<li><code>{esc(k)}</code>: {len(v)} repo chung</li>" for k, v in overlap.items())
    note = (
        f"<p>Cột cuối: số scope (repo, version) có đủ task khác nhau cho trung vị số trial nhỏ nhất "
        f"trong mô phỏng ({num(need)} cặp, STR = −0,25). Đây là kiểm tra R2: nếu gần 0 thì phải "
        "rút có hoàn lại từ pool hoặc gộp scope.</p>"
        if need
        else ""
    )
    return (
        f"<div class='tbl'><table><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}"
        f"</tbody></table></div>{note}<p>Repo trùng giữa các benchmark (cần cho split theo repo):</p>"
        f"<ul>{ov}</ul><p class='muted'>Sinh lúc {esc(summary.get('generated_utc', ''))}.</p>"
    )


def design_html(d: dict | None) -> str:
    if not d:
        return "<p class='muted'>Chưa có <code>results/design_table.json</code>.</p>"
    effs = list(d["rows"][0]["trials"].keys())
    head = "".join(f"<th>STR {e.replace('.', ',')}</th>" for e in effs)
    body = "".join(
        f"<tr><td class='n'>{str(r['theta']).replace('.', ',')}</td><td class='n'>{num(r['cells'])}</td>"
        f"<td class='n'>{r['alpha_cell']:.1e}</td>"
        + "".join(
            f"<td class='n'>{num(r['trials'][e]) if r['trials'][e] else '&gt; ' + num(d['max_budget'])}</td>"
            for e in effs
        )
        + "</tr>"
        for r in d["rows"]
    )
    return (
        "<div class='tbl'><table><thead><tr><th>θ</th><th>Số ô chia α</th><th>α mỗi ô</th>"
        f"{head}</tr></thead><tbody>{body}</tbody></table></div>"
        f"<p>Số cặp trial mỗi ô để admit với power {int(d['power'] * 100)}%. "
        "<b>Đọc bảng:</b> số ô chỉ ảnh hưởng theo log(1/α), nên gộp scope giúp ít. Khoảng cách "
        "|STR| − θ mới quyết định chi phí: hạ θ từ 0,05 xuống 0,02 giảm khoảng 2 lần số trial với "
        "hiệu ứng nhỏ. Mỗi cặp trial là 2 lần chạy agent + test.</p>"
    )


def power_html(d: dict | None) -> str:
    if not d:
        return "<p class='muted'>Chưa có <code>results/endpoint_power.json</code>.</p>"
    body = "".join(
        f"<tr><td class='n'>{num(r['n_harmful'])}</td>"
        + "".join(
            f"<td class='n'>{pct(r[k])}</td>"
            for k in (
                "margin5_independent",
                "margin5_nested",
                "superiority_independent",
                "superiority_nested",
            )
        )
        + "</tr>"
        for r in d["rows"]
    )
    return (
        f"<p>Giả sử đúng như số dự kiến của paper: baseline {pct(d['p_baseline'])} → Gatekeeper "
        f"{pct(d['p_gatekeeper'])} (margin thật 6,4 điểm).</p>"
        "<div class='tbl'><table><thead><tr><th>Cặp harmful</th><th>Cận dưới &gt; 5 điểm<br>(độc lập)</th>"
        "<th>Cận dưới &gt; 5 điểm<br>(nested)</th><th>Ưu thế &gt; 0<br>(độc lập)</th>"
        f"<th>Ưu thế &gt; 0<br>(nested)</th></tr></thead><tbody>{body}</tbody></table></div>"
        "<p><b>R14.</b> Endpoint như paper đăng ký (cận dưới &gt; 5 điểm, 63 cặp harmful) gần như không "
        "thể đạt kể cả khi Gatekeeper đúng là tốt hơn 6,4 điểm. Đề xuất: giả thuyết ưu thế và 200–500 cặp "
        "harmful (<code>docs/preregistration.md</code>).</p>"
    )


def split_html(sp: dict | None) -> str:
    if not sp:
        return "<p class='muted'>Chưa có <code>data/splits/split_v0.json</code>.</p>"
    th = sp["scopes_with_at_least"]
    rh = sp["repos_with_at_least"]
    cells = "".join(
        f"<tr><td class='n'>≥ {esc(k)}</td><td class='n'>{v}</td><td class='n'>{rh.get(k, '—')}</td></tr>"
        for k, v in th.items()
    )
    top = list(sp["tasks_per_scope"].items())[:8]
    top_html = ", ".join(f"<code>{esc(k)}</code> {v}" for k, v in top)
    return (
        f"<p>Train: {len(sp['train_repos'])} repo SWE-Gym, {num(sp['n_train_tasks'])} task. "
        f"Test: {len(sp['test_repos'])} repo, {num(sp['n_test_tasks'])} task (SWE-bench ∪ Verified ∪ "
        f"SWE-bench-Live, bỏ {len(sp['repos_removed_from_test_for_overlap'])} repo trùng train: "
        f"{esc(', '.join(sp['repos_removed_from_test_for_overlap']))}). Hash split "
        f"<code>{esc(sp.get('sha256_16', ''))}</code>.</p>"
        "<div class='tbl'><table><thead><tr><th>Số task khác nhau</th><th>Scope (repo, version)</th>"
        f"<th>Repo</th></tr></thead><tbody>{cells}</tbody></table></div>"
        f"<p>Scope lớn nhất: {top_html}.</p>"
        "<p><b>Kết luận R2.</b> Không scope (repo, version) nào có đủ task khác nhau cho số trial mô phỏng "
        "yêu cầu (≥ 219 cho skill rất mạnh). Mỗi trial một task mới là không khả thi trên benchmark chuẩn; "
        "phải rút có hoàn lại từ pool (bound theo pool, chênh lệch vào ξ<sub>s</sub>) hoặc gộp scope "
        "theo repo/framework.</p>"
    )


def citations_html(c: dict | None) -> str:
    if not c:
        return "<p class='muted'>Chưa có <code>data/citations.json</code>.</p>"
    rows = []
    for r in c.get("arxiv", []):
        ok = r.get("exists_on_arxiv")
        authors = ", ".join(r.get("authors", [])[:3]) + (
            " …" if len(r.get("authors", [])) > 3 else ""
        )
        flag = (
            " <span class='warn'>(paper đang ghi tác giả giả)</span>"
            if r.get("draft_uses_placeholder_authors")
            else ""
        )
        sim = r.get("title_similarity")
        sim_td = (
            "<td>—</td>"
            if sim is None
            else f"<td class='{'ok' if sim >= 0.8 else 'bad'}'>{sim:.2f}"
            f"{'' if sim >= 0.8 else '<br>tiêu đề trong paper sai'}</td>"
        )
        rows.append(
            f"<tr><td>{esc(r['key'])}{flag}<br><span class='muted'>paper ghi: "
            f"{esc(r.get('draft_title') or '—')}</span></td><td><code>{esc(r['arxiv_id'])}</code></td>"
            f"<td class='{'ok' if ok else 'bad'}'>{'có' if ok else 'không thấy'}</td>{sim_td}"
            f"<td>{esc(r.get('title', ''))}<br><span class='muted'>{esc(authors)}"
            f" · {esc(r.get('published', ''))}</span></td></tr>"
        )
    drows = []
    for k, hits in c.get("dblp", {}).items():
        best = next(
            (h for h in hits if h.get("venue") and h.get("type") != "Informal Publications"), None
        )
        any_hit = hits[0] if hits else {}
        h = best or any_hit
        drows.append(
            f"<tr><td>{esc(k)}</td><td>{esc(h.get('venue', '—'))}</td><td>{esc(h.get('year', ''))}</td>"
            f"<td>{esc(h.get('type', h.get('error', '')))}</td></tr>"
        )
    return (
        "<div class='tbl'><table><thead><tr><th>Trích dẫn</th><th>arXiv</th><th>Tồn tại</th>"
        "<th>Khớp tiêu đề</th>"
        f"<th>Tiêu đề thật, tác giả, ngày</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
        "<p>Venue theo DBLP (ưu tiên bản đã peer review):</p>"
        "<div class='tbl'><table><thead><tr><th>Công trình</th><th>Venue</th><th>Năm</th><th>Loại</th>"
        f"</tr></thead><tbody>{''.join(drows)}</tbody></table></div>"
        f"<p class='muted'>Sinh lúc {esc(c.get('generated_utc', ''))}.</p>"
    )


CSS = """
:root{--bg:#fbfaf7;--fg:#1d1f23;--muted:#5d636e;--card:#ffffff;--line:#e3e1db;--accent:#2f5d9c;
--good:#2e7d4f;--bad:#b3261e;--warn:#9a6700;--code:#f2f0ea}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#15171a;--fg:#e7e5e0;
--muted:#a3a8b1;--card:#1d2024;--line:#30343a;--accent:#86aee6;--good:#6cc08f;--bad:#f08a80;
--warn:#e2b45a;--code:#24272c}}
:root[data-theme="dark"]{--bg:#15171a;--fg:#e7e5e0;--muted:#a3a8b1;--card:#1d2024;--line:#30343a;
--accent:#86aee6;--good:#6cc08f;--bad:#f08a80;--warn:#e2b45a;--code:#24272c}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,-apple-system,"Segoe UI",
Roboto,"Noto Sans",sans-serif}
main{max-width:900px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:1.9rem;line-height:1.25;margin:0 0 8px}h2{font-size:1.35rem;margin:40px 0 12px;
padding-top:8px;border-top:1px solid var(--line)}h3{font-size:1.08rem;margin:24px 0 8px}
p,li{max-width:72ch}.muted{color:var(--muted)}a{color:var(--accent)}
.banner{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--warn);
padding:12px 16px;border-radius:6px;margin:16px 0}
.math{font-family:"STIX Two Math","Cambria Math",Georgia,serif;background:var(--code);padding:10px 14px;
border-radius:6px;overflow-x:auto;white-space:nowrap;margin:8px 0}
code{background:var(--code);padding:1px 5px;border-radius:4px;font-size:.92em}
.tbl{overflow-x:auto;margin:12px 0}table{border-collapse:collapse;width:100%;font-size:.94rem}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-weight:600;color:var(--muted)}td.n{text-align:right;font-variant-numeric:tabular-nums}
.ok{color:var(--good);font-weight:600}.bad{color:var(--bad);font-weight:600}
.warn{color:var(--warn);font-weight:600}
.bar{height:8px;background:var(--line);border-radius:4px;overflow:hidden;min-width:80px}
.bar>span{display:block;height:100%;background:var(--accent)}
.chart svg{width:100%;height:auto;max-width:560px}.chart .gl{stroke:var(--line)}
.chart .line{fill:none;stroke:var(--accent);stroke-width:2.5}.chart .dot{fill:var(--accent)}
.chart .tick,.chart .axis{fill:var(--muted);font-size:12px}figcaption{color:var(--muted);font-size:.9rem}
.toc{columns:2;font-size:.95rem}@media (max-width:600px){.toc{columns:1}h1{font-size:1.5rem}}
footer{margin-top:48px;color:var(--muted);font-size:.85rem}
"""


def build() -> str:
    sim = load_json("results/simulation.json")
    cross = load_json("results/confseq_crosscheck.json")
    junit = junit_summary()
    phases = todo_progress()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    sha = os.environ.get("GITHUB_SHA", "")[:7] or "local"
    run_url = ""
    if os.environ.get("GITHUB_RUN_ID"):
        run_url = (
            f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/"
            f"{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
        )

    # ---- progress table
    prog_rows = []
    all_done = all_total = 0
    for name, d, t in phases:
        all_done += d
        all_total += t
        frac = d / t if t else 0
        prog_rows.append(
            f"<tr><td>{esc(name)}</td><td class='n'>{d}/{t}</td>"
            f"<td><div class='bar'><span style='width:{100 * frac:.0f}%'></span></div></td></tr>"
        )

    # ---- simulation table
    sim_html = "<p class='muted'>Chưa có <code>results/simulation.json</code>.</p>"
    t1_html = ""
    p9_html = ""
    chart = ""
    if sim:
        rows = []
        for r in sim["grid"]:
            a = "0,05" if r["alpha"] >= 0.01 else "3,1e-5"
            rows.append(
                f"<tr><td class='n'>{str(r['str_true']).replace('.', ',')}</td><td class='n'>{a}</td>"
                f"<td class='n'>{pct(r.get('review_v1_admit_rate'))} / {num(r.get('review_v1_median_trials'))}</td>"
                f"<td class='n'>{pct(r['admit_rate'])} / {num(r['median_trials_admitted'])}</td></tr>"
            )
        sim_html = (
            "<div class='tbl'><table><thead><tr><th>STR thật</th><th>α mỗi ô</th>"
            "<th>Review bản 1: % admit / trung vị trial</th><th>Code này: % admit / trung vị trial</th>"
            f"</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
            f"<p class='muted'>{sim['grid'][0]['reps']} lần lặp mỗi dòng, budget {sim['grid'][0]['budget']}, "
            f"chế độ <code>{esc(sim['mode'])}</code>, Python {esc(sim['python'])}, numpy {esc(sim['numpy'])}, "
            f"sinh lúc {esc(sim['generated_utc'])}.</p>"
        )
        chart = admit_chart(sim["grid"])
        t1 = sim["type_one_check"]
        ok = t1["admit_rate"] <= 0.05 + 3 * (0.05 * 0.95 / t1["reps"]) ** 0.5
        t1_html = (
            f"<p>Kiểm tra sai loại I tại biên H0 (STR = −θ, α = 0,05, {num(t1['reps'])} lần): tỉ lệ admit sai "
            f"<b>{pct(t1['admit_rate'])}</b> → <span class='{'ok' if ok else 'bad'}'>"
            f"{'hợp lệ (≤ α)' if ok else 'VƯỢT α'}</span>.</p>"
        )
        p9 = sim["prop9"]
        p9_html = (
            f"<p>Với σ<sub>T</sub>²/σ<sub>S</sub>² = {str(p9['sigma_T2_over_sigma_S2']).replace('.', ',')} (số dự kiến "
            f"của paper): paper ghi tiết kiệm {str(p9['paper_claim']).replace('.', ',')}×, công thức đúng cho "
            f"<b>{str(p9['corrected']).replace('.', ',')}×</b>.</p>"
        )

    # ---- tests
    test_html = "<p class='muted'>Chưa có kết quả pytest (<code>results/junit.xml</code>).</p>"
    if junit:
        failed = junit["failures"] + junit["errors"]
        cls = "ok" if failed == 0 else "bad"
        th7 = [c for c in junit["cases"] if "theorem7" in c[0]]
        th7_rows = "".join(
            f"<tr><td><code>{esc(n)}</code></td><td class='{'ok' if s == 'pass' else 'bad'}'>{s}</td></tr>"
            for _, n, s in th7
        )
        test_html = (
            f"<p><span class='{cls}'>{junit['tests'] - failed - junit['skipped']}/{junit['tests']} test pass</span>"
            f", {failed} lỗi, {junit['skipped']} bỏ qua.</p>"
            + (
                "<h3>Test phản ví dụ Theorem 7</h3><div class='tbl'><table><thead><tr><th>Test</th>"
                f"<th>Kết quả</th></tr></thead><tbody>{th7_rows}</tbody></table></div>"
                if th7_rows
                else ""
            )
        )

    cross_html = "<p class='muted'>Chưa có kết quả đối chiếu <code>confseq</code> (job CI riêng, cần Boost).</p>"
    if cross:
        rows = "".join(
            f"<tr><td>{esc(k)}</td><td class='n'>{str(v['str_true']).replace('.', ',')}</td>"
            f"<td class='n'>{pct(v['ours_admit_rate'])}</td><td class='n'>{pct(v['confseq_admit_rate'])}</td>"
            f"<td class='n'>{pct(v['agreement'])}</td></tr>"
            for k, v in cross.items()
            if isinstance(v, dict)
        )
        cross_html = (
            "<div class='tbl'><table><thead><tr><th>Tình huống</th><th>STR</th><th>Gatekeeper admit</th>"
            f"<th>confseq admit</th><th>Đồng ý</th></tr></thead><tbody>{rows}</tbody></table></div>"
        )

    paper_html = paper_checks_html()
    bench_html = benchmarks_html(load_json("data/benchmarks/summary.json"), sim)
    cite_html = citations_html(load_json("data/citations.json"))
    sp_html = split_html(load_json("data/splits/split_v0.json"))
    design = design_html(load_json("results/design_table.json"))
    power = power_html(load_json("results/endpoint_power.json"))

    build_line = f"Build {esc(sha)} · {esc(now)}"
    if run_url:
        build_line += f' · <a href="{esc(run_url)}">log GitHub Actions</a>'

    return f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gatekeeper Research Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<p class="muted">FSE-2027-13 · Gatekeeper · {build_line}</p>
<h1>Scope before Reuse: từ lý thuyết đến thực nghiệm</h1>
<p>Báo cáo sống của dự án Gatekeeper: kiểm soát rủi ro khi tái sử dụng skill đã học của coding agent.
Trang này tự sinh lại mỗi lần push, từ <code>TODO.md</code>, <code>results/</code> và kết quả test.</p>
<div class="banner"><b>Trạng thái.</b> Chưa chạy thí nghiệm nào với LLM. Số trong paper đều là <i>dự kiến</i>.
Phần "Thực nghiệm" dưới đây chỉ gồm mô phỏng thống kê và test của code lõi, chưa phải kết quả trên benchmark.</div>

<nav class="toc"><ol>
<li><a href="#tien-do">Tiến độ theo TODO.md</a></li>
<li><a href="#van-de">Vấn đề</a></li>
<li><a href="#ly-thuyet">Lý thuyết (đã sửa)</a></li>
<li><a href="#kiem-tra">Kiểm tra số liệu paper</a></li>
<li><a href="#thuc-nghiem">Thực nghiệm hiện có</a></li>
<li><a href="#benchmark">Benchmark chuẩn</a></li>
<li><a href="#code">Thành phần đã cài</a></li>
<li><a href="#chua-co">Thực nghiệm chưa chạy</a></li>
<li><a href="#tai-lieu">Tài liệu</a></li>
</ol></nav>

<h2 id="tien-do">1. Tiến độ theo TODO.md</h2>
<p>Tổng: <b>{all_done}/{all_total}</b> việc đã xong. Việc chỉ được tick khi có bằng chứng (commit, log CI, file).</p>
<div class="tbl"><table><thead><tr><th>Phase</th><th>Xong</th><th>Tiến độ</th></tr></thead>
<tbody>{"".join(prog_rows)}</tbody></table></div>

<h2 id="van-de">2. Vấn đề</h2>
<p>Một skill (quy trình sửa code agent đã học) có thể <b>hợp lệ về quyền</b>, <b>pass replay test</b> ở repo
gốc, mà vẫn sai ở repo mới. Ví dụ trong paper: skill bọc lệnh ghi DB bằng retry đúng với client at-least-once,
nhưng gây ghi trùng với client exactly-once. Hai skill tốt riêng lẻ cũng có thể hỏng khi ghép.</p>
<p>Gatekeeper trả lời câu "skill này có nên chạy <i>ở đây</i> không" bằng 4 bước: scope screen (cần nhưng
không đủ) → paired trial có/không skill trên chính repo đích → e-process tuần tự, admit khi đủ bằng chứng
skill <b>giúp</b> ít nhất θ → kiểm tra riêng các cặp skill có footprint giao nhau.</p>

<h2 id="ly-thuyet">3. Lý thuyết (bản đã sửa)</h2>
<h3>Selective transfer risk</h3>
<div class="math">STR(S, s) = E<sub>x∼P<sub>s</sub></sub>[ ℓ(x, π) − ℓ(x, ∅) ],&nbsp;&nbsp; admit nếu STR ≤ −θ,&nbsp;&nbsp; ℓ ∈ [0, 1]</div>
<p>P<sub>s</sub> là phân phối các task trong scope s mà điều kiện đầu vào I(x) của skill đúng.</p>
<h3>E-process (cài trong <code>src/gatekeeper/eprocess.py</code>)</h3>
<div class="math">E<sub>n</sub> = ∏<sub>i≤n</sub> (1 + λ<sub>i</sub>(−θ − Z<sub>i</sub>)),&nbsp;&nbsp;
0 ≤ λ<sub>i</sub> ≤ c/(1+θ),&nbsp;&nbsp; admit khi E<sub>n</sub> ≥ 1/α<sub>S,s</sub></div>
<p>λ<sub>i</sub> chỉ dùng dữ liệu trước trial i. Dưới H0: E[Z] ≥ −θ, E<sub>n</sub> là supermartingale
không âm, nên bất đẳng thức Ville cho Pr[∃n: E<sub>n</sub> ≥ 1/α] ≤ α, kể cả khi dừng sớm.</p>
<h3>Theorem 4 (đã sửa)</h3>
<div class="math">Pr[ ∃ (S,s) được admit: STR<sub>Q<sub>s</sub></sub>(S,s) &gt; −θ + 2ξ<sub>s</sub> ]
≤ Σ α<sub>S,s</sub> + Σ α<sub>S∘S′,s</sub> + α<sub>re</sub> ≤ α</div>
<p>Hệ số 2 vì Z ∈ [−1, 1]. Phần composite và re-admission chi tiêu α theo dãy α·6/(π²k²)
(<code>src/gatekeeper/alpha_ledger.py</code>). Mục tiêu "không admit skill có hại" chỉ đạt khi 2ξ<sub>s</sub> ≤ θ.</p>
<h3>Theorem 7 (đã sửa)</h3>
<p>Có S1, S2 với STR(S1) = STR(S2) = −θ mà STR(S1∘S2) = 1 − θ (cận chặt). Cặp S1′, S2 có cùng STR riêng lẻ
nhưng STR(S1′∘S2) = −θ, nên không tồn tại hàm g nào của rủi ro riêng lẻ chặn được rủi ro ghép. Cơ chế
chạy được: S2 chuyển lệnh ghi sang <code>async</code>, retry đồng bộ của S1 gọi mà không <code>await</code>,
nhận về coroutine, không raise, lệnh ghi không bao giờ chạy (<code>tests/test_composition_theorem7.py</code>).</p>
<h3>Prop. 9 (đã sửa)</h3>
<div class="math">n<sub>unpaired</sub> / n<sub>paired</sub> = 1 + 2σ<sub>T</sub>²/σ<sub>S</sub>²</div>
{p9_html}

<h2 id="kiem-tra">4. Kiểm tra số liệu paper</h2>
<p>Sinh tự động từ <code>src/gatekeeper/paper_checks.py</code> (test: <code>tests/test_paper_checks.py</code>).
Số của paper là số <i>dự kiến</i>; đây chỉ kiểm tra tính nhất quán nội bộ.</p>
{paper_html}

<h2 id="thuc-nghiem">5. Thực nghiệm hiện có</h2>
<h3>5.1 Test code lõi</h3>
{test_html}
<h3>5.2 Mô phỏng khả thi của e-process</h3>
<p>Z ∈ {{−1, 0, 1}}, θ = 0,05. Câu hỏi: cần bao nhiêu cặp trial để admit một skill, khi α được chia cho
khoảng 1.600 ô (94 skill × 17 scope)?</p>
{sim_html}
{chart}
{t1_html}
<p><b>Hệ quả.</b> Skill có hiệu ứng cỡ −0,05 đến −0,10 (thường gặp theo SWE-Skills-Bench) hầu như không được admit
trong 2.000 cặp trial. Mỗi ô cần hàng trăm task khác nhau, nhiều hơn số task mỗi repo của SWE-bench.
Đây là rủi ro lớn nhất, phải đo ở pilot (Phase 3).</p>
<h3>5.3 Bảng thiết kế: số trial theo số ô và θ</h3>
{design}
<h3>5.4 Power của endpoint chính</h3>
{power}
<h3>5.5 Đối chiếu với confseq</h3>
{cross_html}

<h2 id="benchmark">6. Benchmark chuẩn được dùng</h2>
<p>Task và test chỉ lấy từ benchmark có thật, được công nhận rộng. Test chính thức giữ nguyên; test
fault-injection tự thêm chỉ cho phân tích phụ.</p>
<div class="tbl"><table><thead><tr><th>Benchmark</th><th>Công nhận</th><th>Vai trò</th></tr></thead><tbody>
<tr><td>SWE-bench (2.294 task, 12 repo)</td><td>ICLR 2024</td><td>Task đích chính, regime A</td></tr>
<tr><td>SWE-bench Verified (500 task)</td><td>Tập con người duyệt, leaderboard chính</td><td>Pilot, tái hiện baseline, endpoint chính</td></tr>
<tr><td>SWE-Gym (2.438 task, 11 repo khác)</td><td>ICML 2025</td><td>Train split: induce skill</td></tr>
<tr><td>SWE-bench-Live</td><td>Microsoft, cập nhật hàng tháng</td><td>Regime B, task sau cutoff model</td></tr>
<tr><td>SWE-smith (tập đã công bố)</td><td>NeurIPS 2025 D&amp;B</td><td>Chỉ bổ sung khi thiếu task</td></tr>
<tr><td>BugsInPy (493 bug)</td><td>ESEC/FSE 2020</td><td>Kiểm tra độ bền</td></tr>
</tbody></table></div>
<p class="muted">Venue phải kiểm lại trên DBLP trước khi trích dẫn (mục 6.3).</p>
<h3>6.1 Số task thật trong các benchmark</h3>
{bench_html}
<h3>6.2 Split theo repo và số task mỗi scope</h3>
{sp_html}
<h3>6.3 Kiểm tra trích dẫn (arXiv, DBLP)</h3>
{cite_html}

<h2 id="code">7. Thành phần đã cài</h2>
<div class="tbl"><table><thead><tr><th>Module</th><th>Vai trò</th><th>Phase</th></tr></thead><tbody>
<tr><td><code>eprocess</code></td><td>Betting e-process, log-space, λ predictable</td><td>5a</td></tr>
<tr><td><code>alpha_ledger</code></td><td>Sổ α: ô, composite, re-admission (dãy 6/π²k²)</td><td>5a</td></tr>
<tr><td><code>skill</code>, <code>scope</code></td><td>Schema ⟨π, D, I, P, K⟩, fingerprint repo, predicate I, scope screen</td><td>5a/5b</td></tr>
<tr><td><code>footprint</code></td><td>Phân tích read/write AST, kiểm tra giao footprint</td><td>5a/5b</td></tr>
<tr><td><code>admission</code></td><td>Algorithm 1, hàng đợi composite, phân bổ theo độ bất định, retirement, certificate</td><td>5a/5b</td></tr>
<tr><td><code>loss</code></td><td>Loss chuẩn hoá (F + wR)/(1 + w) từ kết quả test SWE-bench</td><td>5b</td></tr>
<tr><td><code>baselines</code></td><td>B1, B2, B8, B9</td><td>2</td></tr>
<tr><td><code>runlog</code></td><td>Log trial chạy tiếp được khi lỗi, bắt buộc trường tái lập, theo dõi chi phí</td><td>2/6</td></tr>
<tr><td><code>analysis</code></td><td>σ<sub>T</sub>², σ<sub>S</sub>², số trial cần, power, cluster bootstrap, BH, đường harm–coverage, sweep w</td><td>3/7</td></tr>
<tr><td><code>paper_checks</code></td><td>Tính lại mọi con số của paper</td><td>1</td></tr>
</tbody></table></div>
<p>Chứng minh đã sửa: <a href="../docs/theory/corrections.md"><code>docs/theory/corrections.md</code></a>.</p>

<h2 id="chua-co">8. Thực nghiệm chưa chạy</h2>
<div class="tbl"><table><thead><tr><th>Câu hỏi</th><th>Cần</th><th>Trạng thái</th></tr></thead><tbody>
<tr><td>Pilot: σ<sub>S</sub>², hiệu ứng thật, số task mỗi scope</td><td>Phase 2–3, LLM + Docker</td><td class="warn">Chưa chạy</td></tr>
<tr><td>RQ1: Gatekeeper vs XRepoSkill, always-retest</td><td>Phase 6</td><td class="warn">Chưa chạy</td></tr>
<tr><td>RQ2: bắt cặp composition có hại</td><td>Phase 6</td><td class="warn">Chưa chạy</td></tr>
<tr><td>RQ3: theo regime A/B/C, vs budget-matched retries</td><td>Phase 6</td><td class="warn">Chưa chạy</td></tr>
<tr><td>RQ4: retirement, ablation, break-even</td><td>Phase 6</td><td class="warn">Chưa chạy</td></tr>
</tbody></table></div>

<h2 id="tai-lieu">9. Tài liệu</h2>
<ul>
<li><a href="../docs/01-FSE-2027-13-paper.pdf">Paper (bản nháp, số dự kiến)</a></li>
<li><a href="../docs/02-FSE-2027-13-reading-list.pdf">Reading list</a></li>
<li><a href="../docs/03-FSE-2027-13-summary.pdf">Summary</a></li>
<li><a href="../docs/theory/corrections.md">Lý thuyết đã sửa (Phase 1)</a></li>
<li><a href="../TODO.md">TODO.md: kim chỉ nam và nhật ký tiến độ</a></li>
</ul>
<footer>Sinh bởi <code>scripts/build_report.py</code>. Không sửa tay file này.</footer>
</main>
</body>
</html>
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "report" / "index.html"))
    args = ap.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
