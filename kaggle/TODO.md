# Việc của hướng Kaggle: đã làm, đang làm, đang chờ

**Cập nhật:** 16/11/2026, sau phiên 1 của C4.
**Hướng đang chọn:** `plan_v4.md`. Xong mục A (chờ seed 3), rồi dựng lớp cách ly (C5) trước khi chạy lại agent khác hãng (C4′).
**Quy tắc của file này:** mỗi khi một việc đổi trạng thái hoặc hướng đi đổi, sửa file này trong cùng commit với thay đổi đó.

Hạn mức AI Kaggle đã dùng trong tháng: **khoảng 18,0 trên 100 USD** (P0 0,47; B 3,05; A 13,73; C3 0,01; C4 phiên 1 0,77). Tiền thật: 0.

## Đang chờ @thuthuy

| # | Việc | Cần gì | Ghi chú |
| --- | --- | --- | --- |
| T1 | **Chạy phiên 3 của mục A** (seed 3, khoảng 7 USD) | Notebook mục A chỉ còn một ô `a38_run_cell.py`; gắn dataset `gatekeeper-a38-results`; dòng đầu log phải là `jobs 480, done 321` | Hướng dẫn: `run_s38_s39.md`. Gửi file `a38_results_*.jsonl` mới |
| T2 | Trả lời Q1 của `plan_v4.md` §12: tiếp tục mục C bằng lớp cách ly? | Một chữ: có / không | Phần 0 USD tôi làm trước trong lúc chờ |
| T3 | Chép câu điều khoản Kaggle về việc dùng hạn mức AI | Treo từ giai đoạn 0 (K0e) | Cần trước C4′ |
| T4 | **Không chạy lại ô `c4_cell.py`** | — | Kết quả phiên 1 không hợp lệ (K21); ô này sẽ được thay |

## Đang làm (Claude)

| # | Việc | Trạng thái |
| --- | --- | --- |
| D1 | Lớp cách ly cho agent: thử S1 (`unshare`), S2 (`proot`), S3 (người dùng thường) tại máy của phiên | Bắt đầu sau commit này |
| D2 | Ô thử C5 cho notebook Benchmarks (0 USD) | Sau D1 |

## Việc tiếp theo, theo thứ tự

| # | Việc | Điều kiện | Ai |
| --- | --- | --- | --- |
| N1 | Phân tích mục A theo bản đăng ký; xác định kịch bản A1–A4 | T1 xong | Claude |
| N2 | Chạy ô C5 trên Kaggle | D2 xong | @thuthuy |
| N3 | C6: 6 task (3 không mô tả) qua lớp cách ly, trần 0,5 USD | C5 đạt | cả hai |
| N4 | C4′: ba agent, 4 nhánh, 100 task, chạy lại từ đầu | C6 đạt | @thuthuy chạy, Claude phân tích |
| N5 | Đề xuất C7 (Pygments), C8 (seed 2), C9 (agent hạng giữa), D (lượt học) | Có kết quả C4′ | Claude đề xuất, @thuthuy duyệt |
| N6 | Mục E (việc thuần văn bản) | Theo kịch bản của A, hoặc khi mục C dừng | Claude |
| N7 | Đưa A, B (và C nếu hợp lệ) vào paper và `report/`; chuyển `kaggle/` về `main` | Mọi mục xong, @thuthuy đồng ý | Claude |

## Đã xong

| Ngày | Việc | Kết quả | File |
| --- | --- | --- | --- |
| 14–15/11 | Giai đoạn 0: container trên Kaggle | Không khả thi (hỏng 9/15 lần); đã dừng | `preregistration_s37.md`, `audit.md` K1–K14 |
| 15/11 | P0, P0b: đo chi phí | Giá token chính xác của 4 model | `preregistration_s38.md` 38-2, 38-3 |
| 15–16/11 | **Mục B (§39)** | Xong: skill giả bị quy lỗi ở cả 4 auditor khác hãng; cận dưới > 0 ở 1 auditor | `preregistration_s39.md` §6 |
| 15–16/11 | Mục A (§38), seed 1 và 2 | 321 câu trả lời; chưa phân tích | `results/a38_results_*.jsonl` |
| 16/11 | C0: đọc cách SWE-smith dựng môi trường | Đạt | `preregistration_s40.md` §2 |
| 16/11 | C1: bộ chấm không-container so với điểm Docker | Đạt hai lần: 224/224, gốc 20/20, "không vá" 0/20 | `results/c1_local*.jsonl` |
| 16/11 | C2: bộ chấm trên Kaggle | Đạt (5/5, 0/5), cả trên notebook Benchmarks | `preregistration_s40.md` §5 |
| 16/11 | C3: 3 task với agent thật | Đạt; 0,011 USD | `results/c3/` |
| 16/11 | Kế hoạch bản 4 và file này | — | `plan_v4.md` |

## Đã dừng hoặc không tính

| Việc | Lý do | Ghi ở |
| --- | --- | --- |
| Chạy container (udocker) trên Kaggle | Phiên bị khởi động lại hoặc bị hủy | `audit.md` K14 |
| **C4 phiên 1** (189 lượt Haiku, 0,77 USD) | Agent đi ra ngoài `/testbed` ở 27/189 lượt; môi trường không cách ly. Không số nào được dùng | `audit.md` K21, `preregistration_s40.md` 40-3 |
| Chạy model mở trên GPU Kaggle | Không sửa điểm yếu nào còn lại | trao đổi 15/11 |

## Không làm được bằng Kaggle (ở lại phần giới hạn của paper)

- Task thật thay cho task tổng hợp (cần image Docker riêng cho từng task).
- Bộ học thứ hai ngoài gskill.

## Cần @thuthuy quyết khi tới lúc

| Câu hỏi | Khi nào |
| --- | --- |
| Q2: chấp nhận cách ly yếu (S3) nếu S1, S2 không chạy được? | Sau N2 |
| Q3: duyệt C7, C8, C9, D? | Sau N4 |
| Đồng ý cập nhật paper và `report/`? | Trước N7 |
