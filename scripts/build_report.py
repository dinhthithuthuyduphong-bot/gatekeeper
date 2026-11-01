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
        )
        cross_html = (
            "<div class='tbl'><table><thead><tr><th>Tình huống</th><th>STR</th><th>Gatekeeper admit</th>"
            f"<th>confseq admit</th><th>Đồng ý</th></tr></thead><tbody>{rows}</tbody></table></div>"
        )

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
<div class="tbl"><table><thead><tr><th>Chỗ</th><th>Paper</th><th>Tính lại</th><th>Kết luận</th></tr></thead><tbody>
<tr><td>13 phép cộng, trừ, tỉ lệ (Table 1–3)</td><td>—</td><td>khớp</td><td class="ok">Đúng</td></tr>
<tr><td>B2 harmful acceptance</td><td class="n">22,7%</td><td>100% (B2 admit tất cả) hoặc 35,0%</td><td class="bad">Mâu thuẫn</td></tr>
<tr><td>CI margin [3,1; 9,8] "vượt 5 điểm"</td><td>vượt</td><td>cận dưới 3,1 &lt; 5</td><td class="bad">Sai diễn đạt</td></tr>
<tr><td>"At matched clean reuse"</td><td class="n">84,3 vs 86,0</td><td>không bằng nhau</td><td class="warn">Cần đường harm–coverage</td></tr>
<tr><td>d̄ partner</td><td class="n">0,34</td><td>≈ 10,6 nếu tính toàn library</td><td class="warn">Cần giải thích</td></tr>
<tr><td>Prop. 9 tiết kiệm</td><td class="n">3,1×</td><td>5,2×</td><td class="bad">Sai công thức</td></tr>
</tbody></table></div>

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
<h3>5.3 Đối chiếu với confseq</h3>
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
<p class="muted">Venue phải kiểm lại trên DBLP trước khi trích dẫn.</p>

<h2 id="chua-co">7. Thực nghiệm chưa chạy</h2>
<div class="tbl"><table><thead><tr><th>Câu hỏi</th><th>Cần</th><th>Trạng thái</th></tr></thead><tbody>
<tr><td>Pilot: σ<sub>S</sub>², hiệu ứng thật, số task mỗi scope</td><td>Phase 2–3, LLM + Docker</td><td class="warn">Chưa chạy</td></tr>
<tr><td>RQ1: Gatekeeper vs XRepoSkill, always-retest</td><td>Phase 6</td><td class="warn">Chưa chạy</td></tr>
<tr><td>RQ2: bắt cặp composition có hại</td><td>Phase 6</td><td class="warn">Chưa chạy</td></tr>
<tr><td>RQ3: theo regime A/B/C, vs budget-matched retries</td><td>Phase 6</td><td class="warn">Chưa chạy</td></tr>
<tr><td>RQ4: retirement, ablation, break-even</td><td>Phase 6</td><td class="warn">Chưa chạy</td></tr>
</tbody></table></div>

<h2 id="tai-lieu">8. Tài liệu</h2>
<ul>
<li><a href="../docs/01-FSE-2027-13-paper.pdf">Paper (bản nháp, số dự kiến)</a></li>
<li><a href="../docs/02-FSE-2027-13-reading-list.pdf">Reading list</a></li>
<li><a href="../docs/03-FSE-2027-13-summary.pdf">Summary</a></li>
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
