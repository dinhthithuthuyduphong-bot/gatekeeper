# Gatekeeper — Scope before Reuse (FSE-2027-13)

[![CI](https://github.com/dinhthithuthuyduphong-bot/gatekeeper/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/dinhthithuthuyduphong-bot/gatekeeper/actions/workflows/ci.yml)

Dự án nghiên cứu **kiểm soát rủi ro khi tái sử dụng skill đã học của coding agent**. Một skill có thể hợp lệ về quyền, pass mọi replay test ở repo gốc, mà vẫn là quy trình sai cho repo đích. Gatekeeper chỉ cho skill chạy (admit) khi có bằng chứng thống kê, thu từ paired trial *trên chính repo đích*, rằng skill thực sự giúp ích.

> **Trạng thái (01/11/2026):** đã có toàn bộ phần không cần LLM: lõi thống kê, Algorithm 1 với composite/retirement/certificate, lý thuyết đã sửa kèm test số, công cụ phân tích. **Chưa chạy thí nghiệm nào với LLM.** Mọi số trong paper là số *dự kiến*.
>
> **Venue:** **ASE 2027** (hạn dự kiến cuối 05/2027, chờ CfP). **LLM:** Gemini qua Vertex AI, harness mini-swe-agent. Thiết lập: [`docs/vertex_setup.md`](docs/vertex_setup.md).

## Bắt đầu từ đâu

| File | Dùng để |
| --- | --- |
| [`TODO.md`](TODO.md) | **Kim chỉ nam.** Review, các lỗi cần sửa, todo theo phase, nhật ký tiến độ. Mọi việc đều theo file này. |
| [`report/index.html`](report/index.html) | Báo cáo từ lý thuyết đến thực nghiệm, tự sinh lại từ `TODO.md` + `results/` + kết quả test. |
| [`docs/`](docs/) | Tài liệu gốc: paper, reading list, summary. |

## Cấu trúc repo

```
docs/                       Tài liệu gốc (PDF) + tài liệu dự án
  theory/corrections.md     Lý thuyết đã sửa: Theorem 4′, 7′, Prop. 9, định nghĩa, metric
  baselines.md              Baseline: giữ / loại / cách chạy
  preregistration.md        Bản nháp pre-registration (✅ đề xuất / ❓ cần quyết / ⏳ chờ pilot)
src/gatekeeper/             Code lõi, không cần LLM
  eprocess.py               Betting e-process cho H0: STR(S, s) > -θ, tính trong log-space
  alpha_ledger.py           Sổ phân bổ α: ô (skill, scope), composite, re-admission
  skill.py                  Schema skill ⟨π, D, I, P, K⟩ (JSON)
  scope.py                  Fingerprint repo (D), predicate (I), scope screen
  footprint.py              Footprint K bằng phân tích read/write AST, kiểm tra giao nhau
  admission.py              Algorithm 1, composite, phân bổ trial, retirement, certificate
  loss.py                   Loss chuẩn hoá (F + wR)/(1 + w)
  baselines.py              B1, B2, B8, B9
  runlog.py                 Log trial chạy tiếp được khi lỗi + theo dõi chi phí
  analysis.py               σ_T², σ_S², số trial, power, cluster bootstrap, BH, harm–coverage
  simulate.py               Mô phỏng Monte-Carlo
  composition_example.py    Phản ví dụ chạy được cho Theorem 7
  splits.py                 Split theo repo, đếm task mỗi scope
  paper_checks.py           Tính lại mọi con số trong paper
tests/                      pytest (chạy trong GitHub Actions)
scripts/
  run_simulations.py        → results/simulation.json
  confseq_crosscheck.py     Đối chiếu với confseq
  build_report.py           → report/index.html
  fetch_benchmarks.py       Metadata SWE-bench, Verified, SWE-Gym, SWE-bench-Live, SWE-smith (chạy trong CI)
  check_citations.py        Tra arXiv + DBLP cho mọi trích dẫn (chạy trong CI)
  check_anonymity.py        Quét rò rỉ danh tính trước khi nộp
  make_split.py             Split train/test theo repo → data/splits/
  design_table.py           Số trial theo số ô và θ → results/design_table.json
  power_table.py            Power của endpoint chính → results/endpoint_power.json
  analyze_sskb.py           Pilot ngoài trên SWE-Skills-Bench → results/sskb_analysis.json
  harness_smoke.py          Paired trial gold/empty qua harness SWE-bench chính thức (chạy trong CI)
data/                       Snapshot từ workflow Data snapshots (benchmarks/, splits/, citations.json)
  external/swe-skills-bench/ Dữ liệu paired thật (MIT) dùng làm pilot ngoài, xem SOURCE.md
results/                    Kết quả máy sinh ra (JSON)
report/index.html           Báo cáo HTML (không sửa tay)
.github/workflows/
  ci.yml                    Lint + test + mô phỏng + confseq + report
  data.yml                  Tải metadata benchmark + trích dẫn → nhánh data-snapshots
  harness.yml               SWE-bench harness trên 5 task Verified → nhánh harness-snapshots
```

## Chạy trên máy

Cần Python ≥ 3.10 (khuyến nghị 3.11).

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"

ruff check . && ruff format --check .            # lint
pytest --cov=gatekeeper --junitxml=results/junit.xml
python scripts/run_simulations.py                 # -> results/simulation.json
python scripts/build_report.py                    # -> report/index.html
```

Đối chiếu với `confseq` (tuỳ chọn): bản PyPI cần thư viện C++ Boost và chỉ build được trên Python ≤ 3.10.

```bash
sudo apt-get install libboost-dev
pip install confseq && python scripts/confseq_crosscheck.py
```

## GitHub Actions

Mỗi lần push hoặc mở PR, workflow `ci.yml` sẽ:

1. **test** (Python 3.11 và 3.12): ruff, pytest với coverage ≥ 80%, mô phỏng đầy đủ (kiểm tra sai loại I ≤ α).
2. **confseq-crosscheck** (Python 3.10 + Boost): đối chiếu quyết định admit với `confseq`.
3. **report**: gom kết quả, sinh `report/index.html`, đính kèm làm artifact `gatekeeper-report` của lần chạy.

CI **không** chạy agent LLM hay hàng nghìn trial Docker: những việc đó chạy trên máy riêng, kết quả JSON commit vào `results/` để CI phân tích.

## Quy trình làm việc

1. Lấy việc tiếp theo trong `TODO.md`, theo thứ tự phase.
2. Làm, push, đọc log GitHub Actions, sửa đến khi xanh.
3. Tick `[x]` trong `TODO.md` và ghi bằng chứng (commit, link log CI, file) vào **Nhật ký tiến độ**.
4. Sinh lại report. Thông báo đã xong, rồi sang việc tiếp theo.

## Benchmark

Task và test chỉ lấy từ benchmark có thật, được công nhận rộng: SWE-bench, SWE-bench Verified, SWE-Gym, SWE-bench-Live, SWE-smith (tập đã công bố), BugsInPy. Test chính thức giữ nguyên. Chi tiết ở `TODO.md`, mục 6.1.

## Người thực hiện

@thuthuy · Dự án FSE-2027-13 (proposal P14).
