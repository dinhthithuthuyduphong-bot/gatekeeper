# Rà soát sau giai đoạn B: lỗi thật nằm ở đâu? (02/11/2026)

Dữ liệu: `results/pilot/invalid/g1-b/g1-b.json` (B1), `results/pilot/g1-b2.json` (B2), 37 task chung, 6 nhánh = 222 lần chạy agent. Mỗi kết luận dưới đây kèm phép kiểm trên dữ liệu thật.

## 1. Lý thuyết và công thức — **không có lỗi mới**

| Kiểm tra | Kết quả |
| --- | --- |
| Loss ℓ = (F + wR)/(1 + w), w = 0,5 | Giá trị đo khớp công thức: không giải = 1/1,5 = 0,6667; giải nhưng hỏng 1/28 test P2P = 0,0119 ✅ |
| Z = ℓ_có − ℓ_không, ghép cặp theo task | Đúng; cùng hàng dataset, cùng image ✅ |
| CI 90% bootstrap (`mean_ci`) | Khớp CI t giải tích: B1 [−0,19; −0,02] so với [−0,20; −0,01]; B2 [−0,11; +0,08] so với [−0,12; +0,08] ✅ |
| Theorem 4′, 7′, Prop. 9, e-process, sổ α | Đã sửa và kiểm số trong Phase 1 (`docs/theory/corrections.md`, `tests/test_theory.py`); pilot không dùng đến (pilot là sàng lọc, không phải kiểm định anytime-valid) |

## 2. Lỗi **thiết kế thống kê** (lỗi của mình, có thật)

| # | Lỗi | Bằng chứng | Hệ quả |
| --- | --- | --- | --- |
| D1 | Quy tắc đối chứng dương "chỉ xét task nhánh gốc thất bại" (A11) bị **hồi quy về trung bình**: lọc task theo chính lần chạy gốc thì mọi nhánh chạy lại đều trông như "giúp" | Đối chứng *nhiễu* (không có gì giúp) đạt Z = −0,17 trên đúng 20 task đó; đối chứng dương chỉ −0,066 | Quy tắc vô hiệu: có thể đạt oan với một skill vô dụng. Kết quả STOP của B2 vì vậy **không nói được** "phép đo kém nhạy" |
| D2 | Đối chứng dương quá yếu: gợi ý *tên file* không giúp vì agent đã tự tìm đúng file | Ở B2, mọi bản sửa đã nộp đều chạm ít nhất một file gold (sai file: 0/0/0 ở 3 nhánh). Gợi ý chỉ giảm số lần không nộp (12 → 8), các bản nộp thêm đều sai | Cần đối chứng dương nhắm đúng chỗ khó: nội dung sửa / test cần qua, không phải vị trí file |
| D3 | Quy tắc "CI 90% của nhiễu phải chứa 0" có **10% báo động giả** mỗi lần kiểm, và B1 có khả năng là một lần như vậy | Sign test B1: 8 vs 2 cặp lật, p = 0,11. Nhánh gốc B1 (seed 0) giải 14/37; ba nhánh khác không có gợi ý giải 18, 18, 18; chênh 4 task ≈ 1,4 SD | Trước đây mình quy STOP của B1 cho lỗi seed (A14). **Đính chính:** lỗi seed có thật, nhưng chưa chứng minh được nó *gây ra* STOP; may rủi là giải thích đủ |
| D4 | Hiệu ứng ngưỡng 0,10 (≈ 15 điểm % tỉ lệ giải) so với nhiễu | SD của Z mỗi cặp = 0,36; 29% cặp lật chỉ vì đổi seed; 22/37 task luôn giải hoặc không bao giờ giải (không mang thông tin) | Cần ~35 task/skill (1 seed) để CI ± 0,10; pool C có 25–30 task/skill → **thiếu power** nếu chỉ 1 seed |
| D5 | Trần 60 bước | 29–32% lần chạy chạm trần, **không nộp gì** | Nguồn nhiễu lớn nhất và là trần cho mọi skill (C1) |

## 3. Lỗi **cài đặt** (code của mình, có thật, đã sửa)

| # | Lỗi | Có làm sai Z không? |
| --- | --- | --- |
| A2/A3 | Lỗi hạ tầng bị chấm là "không giải" | Có, ở lượt A1 đầu (đã cách ly) |
| A15 | Trần tích luỹ đếm trùng file phân tích | Không (chỉ ảnh hưởng điểm dừng ngân sách) |
| A16 | File gộp ghi `solved` = 0 | Không (chỉ bảng chi phí) |
| A18 + bộ đếm thử lại | Chạy tiếp coi task lỗi hạ tầng là "xong"; bộ đếm thử lại không reset | Không, trong mọi lượt đã chạy (0 lỗi hạ tầng ở B2) |

Kiểm thêm, **không có lỗi**: gợi ý tới agent ở 38/38 lần (không có `(unknown)`); harness chấm theo đúng định nghĩa resolved của SWE-bench; các loss lẻ (0,0038 / 0,0119) là agent làm hỏng 1 test P2P, ổn định ở mọi nhánh, không phải test chập chờn.

## 4. Do **môi trường / API** (không phải logic của mình)

| # | Hiện tượng | Ghi chú |
| --- | --- | --- |
| A14 | Vertex coi `seed=0` là không đặt seed | Có thật (6 lệnh gọi thử); đã chặn seed 0 |
| E1 | Seed **không** làm cả quỹ đạo tất định | Cấu hình *giống hệt* (seed 1, không skill) ở B1 và B2 cho kết quả khác nhau ở **8/37 task**. Seed chỉ tất định cho một lệnh gọi; quỹ đạo dài 40 bước vẫn phân kỳ (nguyên nhân có thể: thời gian chạy lệnh, timeout, thứ tự output, phía server; chưa tách được). Giả định trong A12 chỉ đúng một phần → các lần lặp coi như **độc lập**, cũng là điều thiết kế cần |
| A17 | Docker Hub 429 (pull ẩn danh) | Làm chậm, không làm sai số liệu |
| A6, A8, A9 | Vertex `global`, gói `mcp`, đĩa | Đã xử lý |
| E2 | Tiến trình nền tối đa 2 giờ / container phiên bị khởi động lại | Làm chậm; driver chạy tiếp theo task |

## 5. Kết luận

- **Pipeline đo (ghép cặp, chấm điểm, loss, CI) đúng.** Đối chứng nhiễu B2 ≈ 0.
- Hai lần STOP đến từ **thiết kế kiểm tra**: D3 cho B1, D1 + D2 cho B2, chứ không phải lỗi tính toán.
- Vấn đề thực chất cho G1 là **nhiễu lớn so với hiệu ứng cần thấy** (D4, D5). Cần sửa trước khi chạy C, nếu không kết quả C sẽ không diễn giải được.

## 6. Đề xuất sửa (chờ @thuthuy quyết)

1. **Quy tắc đối chứng dương mới** (đặt trước khi chạy): chọn task "khó" bằng một lần chạy *độc lập* (seed riêng). Trên các task đó, so đối chứng dương với một lần chạy không skill *khác*. Hoặc đơn giản hơn: so trực tiếp đối chứng dương với đối chứng nhiễu trên mọi task, yêu cầu Z ≤ −0,10 và cận trên CI < 0.
2. **Đối chứng dương mạnh hơn**: cho tên test FAIL_TO_PASS cần qua cộng hàm cần sửa (lấy từ gold patch), thay vì chỉ tên file.
3. **step_limit 100** (giảm 30% lần chạy không nộp); Flash-Lite vẫn rẻ.
4. **3 seed mỗi cặp** (1, 11, 21) cho đối chứng và cho C; phân tích trung bình theo task.

Ước tính: bước 1–3 trên 38 task × 3 nhánh, khoảng 4–6 USD (100 bước tốn hơn 60 bước). C với 3 seed khoảng 20–25 USD → tổng pilot sẽ **vượt 20 USD** nên cần @thuthuy duyệt. Phương án rẻ hơn: C với 1 seed (~8 USD), chấp nhận chỉ phát hiện được hiệu ứng ≥ 0,15.
