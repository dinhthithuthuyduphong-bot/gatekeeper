# Phán quyết G1 (03/11/2026)

Áp máy móc quy tắc đã đăng ký trước: `docs/preregistration_g1_v2.md` Bổ sung 3 (cùng hai bản sửa), Bổ sung 5 và Bổ sung 4. Mã: `scripts/analyze_g1_final.py`. Kết quả: `results/g1_final.json`, `results/g1_next_feasibility.json`.

## 1. Phán quyết: **G1 FAIL**

Skill được xác nhận: `validation-error`, 32 task × 3 seed (11, 21, 31), endpoint resolved.

| Yếu tố | Kết quả |
| --- | --- |
| Ẑ (resolved) | **+0,031**, tức hơi về phía *hại*: giúp 4 task, hại 7 task (theo trung bình theo task) |
| CI 95% (khoảng t) | [−0,057; +0,120] |
| Kiểm định chính (đổi dấu chính xác, một phía) | p = 0,830 → không bác bỏ (mức Holm 0,025) |
| S1: kiểm định t ghép cặp | p = 0,762 → không bác bỏ |
| S2: đổi dấu theo cụm repo (10 cụm) | p = 0,688 → không bác bỏ |
| A/A (nhánh không skill, seed 11 so với 21) | chênh lệch 0,000; p hai phía = 1,00; độ lệch ước lượng [−0,09; +0,09] → **không phát hiện lệch** (theo ICH E9, không được kết luận là "sạch") |
| Hiệu ứng tới hạn | 0,094: chỉ hiệu ứng có ích ≥ 9,4 điểm % mới tuyên bố được với dữ liệu này |
| Endpoint phụ (loss) | +0,018 (cùng chiều) |
| Lượng tính toán (bước xác nhận) | 192 lần chạy agent; 122,5M token input (86,8% được cache), 1,15M token output; trung bình mỗi lần chạy 638k input / 6,0k output (`results/token_usage.json`) |

**Diễn giải:**
- Tín hiệu ở C (−0,062, chọn ra từ 4 skill) **không lặp lại** trên dữ liệu mới. Đây đúng là điều mà tách dữ liệu (Cox 1975) được thiết kế để phát hiện: "lời nguyền người thắng".
- CI 95% **loại trừ** hiệu ứng có ích lớn hơn 5,7 điểm %.
- **Phạm vi:** 32 task SWE-bench Verified mà I(x) của skill đúng; Gemini 3.1 Flash-Lite (`reasoning_effort` low); step_limit 100. Không suy rộng ra model hay benchmark khác.

## 2. Chọn phương án tiếp theo (quy tắc Bổ sung 4, áp máy móc)

**Công thức:** n_cần = (z₁₋α′ + z₁₋β)² · V / δ² (Cohen 1988; Lakens 2022), với α′ = 0,025.
- **V đo từ dữ liệu xác nhận:** 0,060 (trung bình 3 seed theo task); 0,157 (một lần chạy).
- **Lượng tính toán đo được mỗi lần chạy** (bước xác nhận): 638k token input (86,8% cache), 6,0k token output.
- **δ lấy từ phân phối đã công bố** (SWE-Skills-Bench, 392 ô skill × cấu hình; `results/sskb_analysis.json`):
  - δ = 0,02: tại phân vị 25%;
  - δ = 0,05: 15% số ô đạt mức này;
  - δ = 0,109: phân vị 5%; 6,6% số ô có hiệu ứng ≤ −0,1.
- **n_có:** số task I(x) đúng trên tập test, nhân tỉ lệ dùng được 86/89. exception-handling 200, null-guard 122, type-guard 309, validation-error 403.

| δ | power | n_cần (3 seed) | lần chạy / skill (n × 2 nhánh × 3 seed) | token / skill (input; output) | Khả thi với n_có? |
| --- | --- | --- | --- | --- | --- |
| 0,02 | 50% / 80% | 576 / 1.176 | 3.456 / 7.056 | 2,2B; 21M / 4,5B; 42M | ❌ vượt mọi n_có (tối đa 403) |
| 0,05 | 50% / 80% | 93 / 189 | 558 / 1.134 | 356M; 3,3M / 723M; 6,8M | ⚠️ ở power 80% chỉ type-guard (309) và exception-handling (200) |
| 0,109 | 50% / 80% | 20 / 40 | 120 / 240 | 77M; 0,7M / 153M; 1,4M | ✅ mọi skill |

(Token = số lần chạy × lượng đo được mỗi lần chạy ở bước xác nhận. Để so sánh: toàn bộ pilot G1 đã dùng 756 lần chạy, khoảng 405M token input và 4,4M token output.)

**Áp từng bước:**
1. **P2 (skill mạnh hơn):** không có phân phối hiệu ứng **đã công bố** cho skill dạng chương trình sửa code, nên không tính được n_cần theo tiêu chí. **Không đủ điều kiện** chọn.
2. **P1 trên `validation-error`:** dữ liệu đã loại trừ hiệu ứng có ích > 0,057 (CI 95%). **Bị loại.**
3. **δ lớn nhất mà phân phối công bố cho là có thật:** 0,109 (phân vị 5%). Ở δ này, **P1 trên 3 skill còn lại** và **P3 (gộp scope theo skill, bỏ thiết kế từng (skill, repo))** cho cùng một phép tính: n = 40 task × 3 seed, tức 240 lần chạy, khoảng 153M token input và 1,4M token output mỗi skill. Hai phương án này là cùng một thiết kế: kiểm từng skill gộp qua mọi repo. Chọn phương án rẻ nhất, tức **P1 thực hiện theo thiết kế gộp scope (P3)**.
4. **Quy tắc 4:** 3 skill × 240 lần chạy (khoảng 460M token input) sẽ vượt trần ngân sách của pilot, nên **cần @thuthuy duyệt** trước khi chạy.

**Thông tin để quyết định, cũng từ phân phối đã công bố:**
- Xác suất một skill có hiệu ứng ≤ −0,1 là khoảng 6,6%.
- Với 3 skill, xác suất ít nhất một skill có là 1 − 0,934³ ≈ **18%**.
- Kiểm định lần nữa vì vậy **nhiều khả năng sẽ không tìm ra skill có ích**.

**P4** (paper về phương pháp đo) không tốn thêm tiền, nhưng không giữ được claim cốt lõi. Theo quy tắc 2, P4 chỉ được chọn khi không phương án giữ claim nào khả thi.

## 3. Kết luận cho paper (không phụ thuộc vào lựa chọn trên)

- **Thiết kế gốc (chứng nhận từng (skill, scope) với θ nhỏ) không khả thi** với hiệu ứng thực tế:
  - δ = 0,02 cần ≥ 576 task cho mỗi ô;
  - δ = 0,05 cần ≥ 93–189 task;
  - trong khi scope lớn nhất của SWE-bench chỉ có 157 task (R2), và số task mà I(x) đúng trong mỗi scope còn ít hơn nhiều.
- **Chứng nhận khả thi** khi (a) gộp scope theo skill và (b) chỉ nhắm hiệu ứng lớn (δ ≈ 0,1), hoặc (c) chấp nhận khoảng 1.134 lần chạy (khoảng 723M token input) mỗi skill cho δ = 0,05, trên skill có ≥ 189 task.
- **Đóng góp đã có, có số liệu:**
  - nhiễu của agent: 16–29% cặp lật kết quả chỉ vì đổi seed;
  - phương sai đo được;
  - hiệu ứng "lời nguyền người thắng" được phát hiện nhờ tách dữ liệu;
  - type-guard có tín hiệu gây hại (C: +0,094; chưa kiểm định xác nhận).

## Lượng tính toán theo giai đoạn (`results/token_usage.json`)

| Giai đoạn | Lần chạy agent | Token input (tỉ lệ cache) | Token output | Mỗi lần chạy (input / output) |
| --- | --- | --- | --- | --- |
| A (chọn model; Flash và Flash-Lite) | 16 | 8,4M (79%) | 0,17M | 527k / 10,5k |
| B1 (không hợp lệ, seed 0) | 113 | 51,8M (85%) | 0,59M | 459k / 5,3k |
| B2 | 114 | 51,3M (85%) | 0,59M | 450k / 5,1k |
| B3 (100 bước) | 117 | 73,6M (87%) | 0,76M | 629k / 6,5k |
| C (sàng lọc) | 204 | 97,2M (85%) | 1,10M | 476k / 5,4k |
| Xác nhận (3 seed) | 192 | 122,5M (87%) | 1,15M | 638k / 6,0k |
| **Tổng** | **756** | **~405M (~86%)** | **~4,4M** | |

Ghi chú: USD chỉ dùng để kiểm soát ngân sách trong lúc chạy (`docs/budget_200.md`); báo cáo dùng token để so sánh được giữa các giai đoạn, nhánh và model, không phụ thuộc bảng giá.
