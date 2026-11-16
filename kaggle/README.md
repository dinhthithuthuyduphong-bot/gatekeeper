# Thư mục `kaggle/`: mọi việc của hướng Kaggle

**Quy tắc** (@thuthuy 14/11/2026: "Đưa các kế hoạch dưới dạng .md của kaggle lên 1 folder riêng ở nhánh default để dễ kiểm soát. Khi tất cả đều chạy ổn mới đưa lên main"):
- Mọi kế hoạch, bản đăng ký, mã, notebook và kết quả của hướng Kaggle nằm ở đây, trên nhánh mặc định `claude/gatekeeper-13-research-nxytoh`.
- **Chưa đưa lên `main`** cho tới khi toàn bộ chạy ổn trên Kaggle: giai đoạn 0 đạt mọi cổng trong Kaggle và các thí nghiệm được duyệt đã chạy xong, đã kiểm.
- Khi đưa lên `main`: bản đăng ký trở về `docs/preregistration_main.md` (giữ số mục §37 và ngày đăng ký), mã về `scripts/`, test về `tests/`, kết quả về `results/`.

## Nội dung

| File | Là gì |
| --- | --- |
| `plan_v3.md` | **Kế hoạch hiện hành (16/11):** việc sau A và B; mục C (agent khác hãng, không container) chờ duyệt |
| `plan_v2.md` | Kế hoạch bản 2 (15/11): dùng hạn mức AI cho việc thuần văn bản; @thuthuy duyệt A và B ngày 15/11 |
| `preregistration_s38.md` | §38 (mục A): model viết skill khác hãng trên 32 prompt gskill đã lưu |
| `notebooks/a38_p0_cell.py` | P0: đo chi phí, kiểm `temperature=None` (một ô, notebook Benchmarks) |
| `notebooks/a38_run_cell.py` | Chạy chính §38 (một ô; chạy mỗi ngày đến khi in "all done") |
| `data/a38_prompts.jsonl.gz` | 33 dòng prompt của §38 (dựng bằng `scripts/a38_build.py`) |
| `scripts/a38_analyse.py`, `scripts/a38_power.py` | Phân tích đã đăng ký; mô phỏng power |
| `review_r67.md` | Review trước khi chạy §38 và §39 (R-67) |
| `preregistration_s39.md` | §39 (mục B): auditor khác hãng trên 102 prompt sham-audit |
| `notebooks/b39_run_cell.py` | Chạy §39 (giống ô §38 ngoài khối cấu hình; dữ liệu là dataset riêng tư) |
| `scripts/b39_build.py`, `scripts/b39_analyse.py` | Dựng lại prompt từ dữ liệu gốc E1; phân tích đã đăng ký |
| `plan.md` | Kế hoạch bản 1 (giai đoạn 1–3 của bản này không còn khả thi) |
| `preregistration_s37.md` | Bản đăng ký trước của giai đoạn 0 (§37) và kết quả đến nay |
| `run_stage0.md` | Hướng dẫn chạy notebook trên Kaggle (giai đoạn 0) |
| `run_s38_s39.md` | Hướng dẫn chạy §38 và §39 mỗi ngày |
| `notebooks/a38_p0b_cell.py` | P0b: đo chi phí từng model trên tin nhắn trả lời |
| `notebooks/kaggle_stage0_batch.ipynb` | Giai đoạn 0, phần A, **chạy theo lô** (Save & Run All): cách chạy chính từ 15/11 |
| `notebooks/kaggle_stage0.ipynb` | Notebook giai đoạn 0, phần A: K0a, K0b (notebook thường) |
| `notebooks/k0cd_benchmarks_cell.py` | Giai đoạn 0, phần B: K0c, K0d (một ô, dán vào notebook Benchmarks) |
| `scripts/udocker_shim.py` | Lớp thay thế Docker: mã chấm của SWE-smith chạy nguyên văn qua udocker |
| `scripts/k0a_probe.py` | K0a: kéo image, thử các cách chạy của udocker, ghi `k0a.json` và `k0a_mode.txt` |
| `scripts/k0_stage0.py` | Chạy K0a, K0b; ghi từng lượt chấm, chạy tiếp được khi bị ngắt |
| `tests/test_udocker_shim.py` | Test của lớp thay thế (chạy: `python -m pytest -q kaggle/tests`) |
| `results/k0b_local.jsonl` | K0b ở máy của phiên làm việc: 117/117 bản vá trùng điểm, gốc 20/20, không vá 0/20 |
| `review_r66.md` | Review trước khi chạy (R-66) |
| `audit.md` | Lỗi của hướng Kaggle (K1–K3) |

## Trạng thái (14/11/2026)

| Giai đoạn | Trạng thái |
| --- | --- |
| 0, ở máy của phiên làm việc | Đạt K0a, K0b |
| 0, trong Kaggle (cập nhật 15/11) | K0a đạt một lần; K0b không hoàn thành (Kaggle ngắt phiên nhiều lần); **dừng việc chạy container trên Kaggle** (K14). K0c, K0d chờ quyết |
| 0, trong Kaggle (cũ) | Đã có: không có Docker daemon; hạn mức AI 10 USD/ngày, 100 USD/tháng. Chờ chạy lại phần A bằng notebook mới, và phần B trong notebook Benchmarks |
| 1–3 (container) | Không khả thi trên Kaggle |
| §38 (mục A) | P0 và P0b xong (0,47 USD hạn mức); đã chọn model (ghi chú 38-3); chờ chạy (`run_s38_s39.md`) |
| §39 (mục B) | **Xong 16/11:** 408/408 lần gọi, 3,05 USD hạn mức; kết quả ở `preregistration_s39.md` §6 |

Chi phí đến nay: 0 USD.
