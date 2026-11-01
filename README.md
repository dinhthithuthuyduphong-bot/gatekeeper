# Gatekeeper — Scope before Reuse (FSE-2027-13)

[![CI](https://github.com/dinhthithuthuyduphong-bot/gatekeeper/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/dinhthithuthuyduphong-bot/gatekeeper/actions/workflows/ci.yml)

Dự án nghiên cứu **kiểm soát rủi ro khi tái sử dụng skill đã học của coding agent**. Một skill có thể hợp lệ về quyền, pass mọi replay test ở repo gốc, mà vẫn là quy trình sai cho repo đích. Gatekeeper chỉ cho skill chạy (admit) khi có bằng chứng thống kê, thu từ paired trial *trên chính repo đích*, rằng skill thực sự giúp ích.

> **Trạng thái (01/11/2026):** mới có lõi thống kê (e-process, sổ α), test phản ví dụ Theorem 7 và mô phỏng khả thi. **Chưa chạy thí nghiệm nào với LLM.** Mọi số trong paper là số *dự kiến*.
>
> **Venue:** hạn Research Track FSE 2027 (02/10/2026) đã qua. Mục tiêu mới đang chờ chốt (xem `TODO.md`, mục 0.1).

## Bắt đầu từ đâu

| File | Dùng để |
| --- | --- |
| [`TODO.md`](TODO.md) | **Kim chỉ nam.** Review, các lỗi cần sửa, todo theo phase, nhật ký tiến độ. Mọi việc đều theo file này. |
| [`report/index.html`](report/index.html) | Báo cáo từ lý thuyết đến thực nghiệm, tự sinh lại từ `TODO.md` + `results/` + kết quả test. |
| [`docs/`](docs/) | Tài liệu gốc: paper, reading list, summary. |

## Cấu trúc repo

```
docs/                       Tài liệu gốc (PDF)
  01-FSE-2027-13-paper.pdf
  02-FSE-2027-13-reading-list.pdf
  03-FSE-2027-13-summary.pdf
src/gatekeeper/             Code lõi, không cần LLM (Phase 5a)
  eprocess.py               Betting e-process cho H0: STR(S, s) > -θ, tính trong log-space
  alpha_ledger.py           Sổ phân bổ α: ô (skill, scope), composite, re-admission
  simulate.py               Mô phỏng Monte-Carlo: tỉ lệ admit, số trial, sai loại I
  composition_example.py    Phản ví dụ chạy được cho Theorem 7 (retry đồng bộ + async không await)
tests/                      pytest (chạy trong GitHub Actions)
scripts/
  run_simulations.py        Sinh results/simulation.json
  confseq_crosscheck.py     Đối chiếu với thư viện confseq
  build_report.py           Sinh report/index.html
results/                    Kết quả máy sinh ra (JSON); CI phân tích các file này
report/index.html           Báo cáo HTML (không sửa tay)
.github/workflows/ci.yml    Lint + test + mô phỏng + đối chiếu confseq + build report
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
