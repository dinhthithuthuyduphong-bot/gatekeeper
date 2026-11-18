# Việc của hướng Kaggle: đã làm, đang làm, đang chờ

**Cập nhật:** 18/11/2026. Tóm tắt mọi hướng (cả Vertex): `TODO.md` mục "★ Tình hình hiện tại".
**Hướng đang chọn:** `plan_v4.md`. Xong mục A (38-6 đến 38-9) và A′ (38-11). Cổng C5 và C6 đạt trên Kaggle (40-9). Đang chờ: C4′ (POOL B) và lượt chạy thử W7 (§45 ở `docs/preregistration_main.md`).
**Quy tắc của file này:** mỗi khi một việc đổi trạng thái hoặc hướng đi đổi, sửa file này trong cùng commit với thay đổi đó.

Hạn mức AI Kaggle đã dùng: P0 0,47; B 3,05; A cộng dồn 20,06 (Kaggle báo, 38-6); A′ 1,30; C3 0,01; C4 phiên 1 0,77; C6 0,0314 (USD hạn mức). Tiền thật: 0.

**Trần hạn mức Kaggle: ≤ 100 USD mỗi tháng** (@thuthuy 18/11: "Còn kaggle không quá 100 đô (theo hạn mức tháng)"). Tháng 11 đã dùng khoảng 25,69 USD (cộng các số trên). Mọi ô chạy mới phải nhận số đã dùng trong tháng (@thuthuy đọc ở Settings) và từ chối nếu số đó + trần của phiên > 100. Trần riêng của W7 bước học vẫn xin kèm số đo.

## Đang chờ @thuthuy

| # | Việc | Cần gì | Ghi chú |
| --- | --- | --- | --- |
| ~~T1~~ | **Xong 17/11 (38-6).** ~~Chạy phiên 3 của mục A~~ (seed 3, khoảng 7 USD) | Notebook mục A chỉ còn một ô `a38_run_cell.py`; gắn dataset `gatekeeper-a38-results`; dòng đầu log phải là `jobs 480, done 321` | Hướng dẫn: `run_s38_s39.md`. Gửi file `a38_results_*.jsonl` mới |
| ~~T2~~ | **Xong 18/11: C6 đạt (40-9).** ~~Chạy ô `c6_cell.py`~~ (thay cho ô C5 riêng; ghi chú 40-6) trên một notebook Benchmarks: lượt 1 với `DRY_RUN = True` (0 USD, khoảng 20–30 phút), gửi `c6.json` và `c6_results.zip`; lượt 2 với `DRY_RUN = False` (Haiku, ≤ 0,5 USD hạn mức) sau khi Claude đọc lượt 1 | Gửi hai file sau mỗi lượt | Ô tự chạy cổng C5 trước |
| T3 | Chép câu điều khoản Kaggle về việc dùng hạn mức AI | Treo từ giai đoạn 0 (K0e) | Nên có trước T6 (C4′ để agent gọi model liên tục nhiều giờ). Chưa có; @thuthuy quyết có chạy T6 trước khi có câu này không |
| T4 | **Không chạy lại ô `c4_cell.py`** | — | Kết quả phiên 1 không hợp lệ (K21); thay bằng `c4p_cell.py` (T6) |
| T6 | **Chạy C4′:** `notebooks/c4p_cell.py` (POOL B), mỗi ngày một phiên, trần 2,0 USD mỗi phiên, 12 USD mỗi model | Gửi `c4p.json` và `c4p_results.zip` sau mỗi phiên | Ghi chú 40-8 |
| T7 | **Chạy thử W7:** `notebooks/w7_run_cell.py` (COMMIT `0cb4874…`, `POOL = "A"`, `DRY_RUN = True`, 0 USD), notebook Benchmarks riêng | Gửi `w7_A.json` và `w7_A_run.zip` | §45; trần bước học chưa duyệt |
| T5 | ~~Chọn A hay B cho C4′~~ **Xong 17/11: B** (@thuthuy: "Oke chọn B"). 100 task test + 36 task của §35, khối riêng; power 1,00 (ghi chú 40-5) | — | `POOL = "B"` trong `kaggle/notebooks/c4p_cell.py` (ghi chú 40-8) |

## Đang làm (Claude)

| # | Việc | Trạng thái |
| --- | --- | --- |
| D2 | Nối bộ chạy agent với lớp `chroot` | **Xong 17/11** (ghi chú 40-6). Chạy thử trên Kaggle là lượt 1 của ô C6 |
| D3 | Ô C6 và ô C4′ | **Xong 17/11:** `notebooks/c6_cell.py`, `notebooks/c4p_cell.py` |

## Việc tiếp theo, theo thứ tự

| # | Việc | Điều kiện | Ai |
| --- | --- | --- | --- |
| ~~N1~~ | ~~Phân tích mục A; xác định kịch bản A1–A4~~ **Xong 17/11** (38-6 đến 38-9): không model khác hãng nào qua Holm; phạm vi thu hẹp về model của gskill | — | Claude |
| ~~N2~~ | ~~Chạy ô C5 trên Kaggle~~ **Xong:** gộp vào ô C6 (40-6) | — | — |
| ~~N3~~ | ~~C6: 6 task qua lớp cách ly~~ **Xong 18/11: đạt** (40-9) | — | — |
| N4 | **C4′:** ba agent, 4 nhánh, POOL B (100 + 36 task), chạy lại từ đầu | Đang chờ T6 | @thuthuy chạy, Claude phân tích (40-5, 40-8) |
| N4b | **W7:** chạy thử (T7), đo một khối 3 cặp, xin trần bước học, rồi chạy sau C4′ | Đang chờ T7 | cả hai (§45) |
| ~~N4c~~ | ~~§48 X1′-LF trên Kaggle~~ **Rút lại 18/11** (@thuthuy: "oke nâng trần lên 35 đô"; ghi chú 47-3): lượt học một commit chạy trên Vertex | — | — |
| N5 | Đề xuất C7 (Pygments), C8 (seed 2), C9 (agent hạng giữa), D (lượt học) | Có kết quả C4′ | Claude đề xuất, @thuthuy duyệt |
| N6 | Mục E (việc thuần văn bản), ví dụ E1: kiểm endpoint của §38 bằng đọc tay | Theo kết quả §38 (đã có) | Claude |
| N7 | Đưa §38, A′, B (và C4′, W7 nếu hợp lệ) vào paper và `report/`; chuyển `kaggle/` về `main` | @thuthuy đồng ý | Claude |

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
| 16/11 | Thăm dò quyền của notebook Benchmarks | Có `chroot`, `mknod`; không có không gian tên | `preregistration_s40.md` 40-4 |
| 16/11 | Lớp cách ly `chroot` và cổng C5 tại máy của phiên | Đạt cả 6 phép thử | `results/c5_gate_local.json` |
| 16/11 | C1 chạy lại qua lớp `chroot` | Đạt: 224/224, gốc 20/20, "không vá" 0/20 | `results/c1_chroot.jsonl` |

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
