# Đăng ký trước: kiểm tra phép đo G1, phiên bản 2 (giai đoạn B3)

**Ghi và commit ngày 02/11/2026, trước khi chạy `g1-b3`.** @thuthuy duyệt phương án 1 trong `docs/review_pilot_b.md`. Không đổi quy tắc này sau khi thấy kết quả B3.

## Vì sao có v2

Quy tắc v1 (`docs/budget_200.md` §2) có hai lỗi thiết kế, được phát hiện ở `g1-b2` (`docs/review_pilot_b.md` D1, D2):

- **D1:** đối chứng dương chỉ được tính trên task mà lần chạy gốc thất bại → hồi quy về trung bình. Ngay cả đối chứng nhiễu cũng đạt Z = −0,17 trên các task đó.
- **D2:** gợi ý tên file là thừa. Agent đã chạm đúng file gold trong mọi bản nộp.

## Thiết kế B3

| Mục | Giá trị |
| --- | --- |
| Tên lượt | `g1-b3` |
| Task | 38 task của pool `default` (`results/pool_validation/default/summary.json`), không lọc |
| Model | `gemini-flash-lite` (Vertex AI, `global`) |
| Nhánh | `none` (seed 1); `control-none-seed1` (đối chứng nhiễu, seed 2); `control-oracle-tests` (đối chứng dương mạnh, seed 1) |
| Đối chứng dương mạnh | lộ file + hàm cần sửa (từ gold patch) + tên test FAIL_TO_PASS + `test_patch` (≤ 4000 ký tự). Chỉ dùng làm đối chứng, không bao giờ là skill được đánh giá |
| step_limit | **100** (trước là 60; 30% lần chạy chạm trần, D5) |
| cost_limit | 0,20 USD / lần chạy |
| Chấm điểm | harness SWE-bench 5.0.2; phần sửa vào file mà `test_patch` ghi được bỏ khỏi bản nộp của **mọi** nhánh trước khi chấm (lúc chấm các file đó cũng bị ghi đè) |
| Trần ngân sách | tổng pilot ≤ 19 USD (còn ~1 USD dự phòng cho lô B2 bị ngắt chưa ghi chi phí; tổng thật ≤ 20 USD) |

## Quy tắc (áp máy móc: `scripts/analyze_g1.py --stage-b g1-b3 --rule v2`)

1. **Kiểm tra pipeline:** Z_nhiễu = loss(`control-none-seed1`) − loss(`none`) trên mọi task. CI 90% bootstrap phải chứa 0. Nếu không → STOP.
2. **Kiểm tra độ nhạy:** Z_dương = loss(`control-oracle-tests`) − loss(`control-none-seed1`) trên **mọi** task chạy được ở cả hai nhánh. Hai nhánh này chạy độc lập, nên không có chọn lọc theo kết quả. **Đạt** nếu trung bình ≤ −0,10 **và** cận trên CI 90% < 0, với ít nhất 5 task.
3. Đạt cả hai → được chạy giai đoạn C (cần @thuthuy duyệt nếu tổng vượt 20 USD). Trượt 2 → báo lại; đề xuất kế tiếp: model mạnh hơn (Flash) hoặc đổi họ skill.

## Báo cáo kèm (thăm dò, không quyết định)

Tỉ lệ `LimitsExceeded` theo nhánh; tỉ lệ bản nộp chạm file gold; SD của Z_nhiễu (cập nhật số task/seed cần cho C); số task đổi kết quả giữa hai nhánh không skill.

## Bổ sung (02/11/2026, trong lúc B3 đang chạy, **trước khi** có kết quả B3): giai đoạn C

@thuthuy nâng trần tổng pilot lên **30 USD**; đến đó thì dừng chờ quyết định.

| Mục | Giá trị |
| --- | --- |
| Điều kiện chạy | B3 đạt cả hai kiểm tra của v2 (verdict `controls OK; run stage C`) |
| Tên lượt | `g1-c` |
| Task | pool `g1` (86 task); mỗi skill chỉ chạy trên task mà I(x) đúng; nhánh `none` chạy một lần trên hợp các task đó |
| Skill | `null-guard`, `type-guard`, `exception-handling`, `validation-error` |
| Model, seed, bước | `gemini-flash-lite`, seed 1, step_limit 100, cost_limit 0,20 USD |
| Số seed | **1** (3 seed ≈ 30 USD, vượt trần). Hệ quả: CI rộng hơn, chỉ phát hiện chắc chắn hiệu ứng lớn |
| Trần | tổng pilot ≤ 29 USD theo số ghi nhận (~1 USD dự phòng cho lô bị ngắt chưa ghi) |
| Quy tắc G1 | không đổi: skill đạt nếu Z trung bình ≤ −0,10 **và** cận trên CI 90% < 0 (`g1_decision`) |
| Phân tích | `scripts/analyze_g1.py --stage-b g1-b3 --stage-c g1-c --rule v2` |
