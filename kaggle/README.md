# Thư mục `kaggle/`: mọi việc của hướng Kaggle

**Quy tắc** (@thuthuy 14/11/2026: "Đưa các kế hoạch dưới dạng .md của kaggle lên 1 folder riêng ở nhánh default để dễ kiểm soát. Khi tất cả đều chạy ổn mới đưa lên main"):
- Mọi kế hoạch, bản đăng ký, mã, notebook và kết quả của hướng Kaggle nằm ở đây, trên nhánh mặc định `claude/gatekeeper-13-research-nxytoh`.
- **Chưa đưa lên `main`** cho tới khi toàn bộ chạy ổn trên Kaggle: giai đoạn 0 đạt mọi cổng trong Kaggle và các thí nghiệm được duyệt đã chạy xong, đã kiểm.
- Khi đưa lên `main`: bản đăng ký trở về `docs/preregistration_main.md` (giữ số mục §37 và ngày đăng ký), mã về `scripts/`, test về `tests/`, kết quả về `results/`.

## Nội dung

| File | Là gì |
| --- | --- |
| `plan.md` | Toàn bộ kế hoạch: tài nguyên, nút thắt, giai đoạn 0–3, việc không sửa được |
| `preregistration_s37.md` | Bản đăng ký trước của giai đoạn 0 (§37) và kết quả đến nay |
| `run_stage0.md` | Hướng dẫn chạy notebook trên Kaggle |
| `notebooks/kaggle_stage0.ipynb` | Notebook giai đoạn 0, phần A: K0a, K0b (notebook thường) |
| `notebooks/k0cd_benchmarks_cell.py` | Giai đoạn 0, phần B: K0c, K0d (một ô, dán vào notebook Benchmarks) |
| `scripts/udocker_shim.py` | Lớp thay thế Docker: mã chấm của SWE-smith chạy nguyên văn qua udocker |
| `scripts/k0_stage0.py` | Chạy K0a, K0b; ghi từng lượt chấm, chạy tiếp được khi bị ngắt |
| `tests/test_udocker_shim.py` | Test của lớp thay thế (chạy: `python -m pytest -q kaggle/tests`) |
| `results/k0b_local.jsonl` | K0b ở máy của phiên làm việc: 117/117 bản vá trùng điểm, gốc 20/20, không vá 0/20 |
| `review_r66.md` | Review trước khi chạy (R-66) |

## Trạng thái (14/11/2026)

| Giai đoạn | Trạng thái |
| --- | --- |
| 0, ở máy của phiên làm việc | Đạt K0a, K0b |
| 0, trong Kaggle | Đã có: không có Docker daemon; hạn mức AI 10 USD/ngày, 100 USD/tháng. Chờ chạy lại phần A bằng notebook mới, và phần B trong notebook Benchmarks |
| 1–3 | Chưa duyệt |

Chi phí đến nay: 0 USD.
