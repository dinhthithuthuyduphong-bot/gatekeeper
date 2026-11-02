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

## Bổ sung 2 (02/11/2026, khi C mới chạy lô đầu, **trước khi** có bất kỳ kết quả C nào): phán quyết và kiểm chứng mở rộng

@thuthuy: "phán quyết trong sáng, không khiên cưỡng"; được mở rộng kiểm chứng nếu chưa đủ thuyết phục, tổng pilot **< 35 USD**. Trần ghi nhận: **34 USD**.

**Bước 1: sàng lọc C (1 seed).** Mỗi skill s: Z = loss(s) − loss(none) trên task mà I(x) đúng. Phân loại:
- *hứa hẹn*: Z trung bình ≤ −0,10 và cận trên CI 90% < 0 (quy tắc G1);
- *mơ hồ*: Z trung bình ≤ −0,05 nhưng chưa hứa hẹn;
- *không có tín hiệu*: còn lại.

**Bước 2: kiểm chứng (chỉ cho skill hứa hẹn hoặc mơ hồ; tối đa 2 skill có Z thấp nhất).** Chạy lại skill **và** nhánh `none` trên đúng các task đó với 2 seed mới (11 và 21), không đổi gì khác. Gộp 3 seed: Z theo task = trung bình qua seed; CI 90% bootstrap theo task.

**Phán quyết cuối (áp máy móc):**
- **G1 PASS** cho skill s nếu, trên dữ liệu gộp 3 seed: Z trung bình ≤ −0,10 **và** cận trên CI **96,25%** < 0. Đây là hiệu chỉnh Bonferroni cho 4 skill: 1 − 0,15/4 ≈ 0,9625 tương đương hai phía α = 0,15/4 cho mỗi skill.
- Có tín hiệu ở 1 seed nhưng không giữ được khi gộp 3 seed → **không đạt** (ghi là "tín hiệu không lặp lại").
- Không skill nào hứa hẹn hay mơ hồ ở bước 1 → **G1 FAIL**, không chạy thêm skill khác (tránh "câu cá").
- Hết ngân sách giữa chừng → báo "chưa kết luận", không suy diễn.

**Báo cáo kèm, không quyết định:** Z theo repo, tỉ lệ task chuyển từ không giải → giải và ngược lại (có hại?), chi phí.

## Bổ sung 3 (02/11/2026; C đang chạy, 32/86 task, **chưa mở bất kỳ kết quả C nào**): thay thế Bổ sung 2

@thuthuy giao: tự đánh giá G1, tự chạy, dừng nếu tổng > 35 USD. Bổ sung 2 **bị thay thế** vì có nhiều ngưỡng cảm tính (`docs/review_thresholds.md` §3). Mọi thành phần dưới đây là phương pháp đã công bố. Chỗ nào là lựa chọn giá trị thì ghi rõ.

1. **Endpoint chính: resolved của SWE-bench** (Jimenez et al. 2024). Z = 1[không resolved | skill] − 1[không resolved | không skill] ∈ {−1, 0, 1}. Endpoint phụ: loss (w = 0,5), chỉ báo cáo.
2. **Chọn (dữ liệu C, seed 1):** chọn skill có Z trung bình **< 0**, tức chỉ cần đúng hướng có ích. Không có ngưỡng độ lớn.
3. **Xác nhận trên dữ liệu mới** (tách dữ liệu, Cox 1975): chạy lại mỗi skill được chọn và nhánh `none` trên đúng các task mà I(x) đúng, với seed 11, 21, 31, … (bước 10, để không trùng seed + 1 của đối chứng nhiễu).
   - **Số seed m** = phần nguyên của (34 − chi phí đã ghi sau C) / (chi phí một seed cho mọi skill được chọn). Chi phí một seed = số lần chạy × chi phí trung bình/lần **đo ở C**.
   - Nếu m < 1: bỏ skill có Z (ở C) cao nhất rồi tính lại.
   - Không có trần m tự đặt.
4. **Kiểm định:** một phía, H₀: skill không giúp.
   - Thống kê: trung bình theo task của Z qua m seed.
   - **Kiểm định hoán vị đổi dấu** (Fisher 1935; Pitman 1937): liệt kê hết 2ⁿ cách nếu n ≤ 16, nếu không thì Monte Carlo 200.000 lần với seed cố định.
   - **Holm (1979)**, α nhóm một phía = **0,025** (tương đương hai phía 0,05), trên số skill được xác nhận.
   - Chỉ dùng dữ liệu xác nhận.
5. **A/A trên dữ liệu mới:** nhánh `none` seed 11 so với seed 21 (nếu m ≥ 2). **TOST** (Lakens et al. 2018), α = 0,05, biên = MDE ở mục 6. Nếu TOST không kết luận tương đương thì phán quyết là "**chưa kết luận: pipeline đáng ngờ**". Nếu m = 1 thì báo là không kiểm được.
6. **MDE theo nguồn lực** (Lakens et al. 2018): MDE = (z₁₋α′ + z₀,₈) · √(V_UCL / n), trong đó:
   - V_UCL = cận trên 90% (χ², Browne 1995) của phương sai Z theo task, đo trên dữ liệu xác nhận;
   - α′ = 0,025 / (số skill được xác nhận);
   - n = số task.
   MDE dùng để diễn giải, không dùng làm ngưỡng phán quyết.
7. **Phán quyết:**
   - **G1 PASS** nếu ≥ 1 skill bị bác bỏ H₀ theo Holm **và** A/A không báo pipeline đáng ngờ.
   - **G1 FAIL** nếu không skill nào được chọn, hoặc không skill nào bị bác bỏ. Câu phán quyết phải kèm "không có hiệu ứng ≥ MDE".
   - Mỗi skill báo: ước lượng Z, CI 95% (bootstrap theo task), p đã hiệu chỉnh Holm, MDE, kèm endpoint phụ là loss.
8. **Không thử thêm skill nào khác.** Hết ngân sách giữa chừng thì phán quyết là "chưa kết luận".
9. **Giới hạn bắt buộc phải nêu:** 1 model (Flash-Lite, `reasoning_effort` low); step_limit 100 so với mặc định 250 của mini-swe-agent; 1 benchmark (SWE-bench Verified); I(x) có lift thấp (R16).

Code: `scripts/analyze_g1_final.py`; test: `tests/test_g1_final.py`.

**Ghi chú thực thi (02/11/2026, sau bước chọn, trước khi có dữ liệu xác nhận):**
- Lượt xác nhận chỉ nạp 32 task mà I(x) của `validation-error` đúng (`results/pool_validation/g1_validation_error.json`). Task, nhánh và seed không đổi, chỉ bớt việc tải image cho các task không được chạy.
- Một lô bị dừng giữa chừng chưa ghi chi phí, tối đa khoảng 0,4 USD. Vì vậy trần ghi nhận hạ xuống 33,5 USD để tổng thật vẫn < 35 USD.
- Số seed vẫn là 4: (33,5 − 22,84) / 2,28 = 4,7, phần nguyên là 4.

**Ghi chú thực thi 2** (02/11/2026, sau seed 11, **chưa mở kết quả xác nhận nào**, chỉ biết chi phí):
- Seed 11 tốn 2,79 USD, so với ước tính 2,28 USD (ước tính dùng chi phí trung bình của C, nơi có nhiều task dễ hơn).
- Áp lại đúng công thức của mục 3 với chi phí **đo được**: m = ⌊(33,5 − 22,84) / 2,79⌋ = **3**. Seed xác nhận là **11, 21, 31**; bỏ seed 41.
- Đây không phải thay đổi theo kết quả: công thức không đổi, chỉ thay ước tính chi phí bằng số đo thật. Nếu chạy seed 41, nó sẽ bị dừng giữa chừng vì trần và dữ liệu bị bỏ phí.

## Bổ sung 3, bản sửa (02/11/2026; seed 21 đang chạy, **chưa mở bất kỳ kết quả xác nhận nào**)

@thuthuy: không chấp nhận con số không có cơ sở. Các thay đổi so với Bổ sung 3 (chi tiết và lý do ở `docs/number_provenance.md` §1):

1. Kiểm định đổi dấu được tính **chính xác** bằng tích chập. Bỏ Monte Carlo 200.000 lần và ngưỡng n ≤ 16.
2. Khoảng tin cậy: **khoảng t**, mức 1 − 2α = 95%. Bỏ bootstrap 10.000 lần.
3. **Bỏ MDE, power 80% và độ phủ Browne 90%** khỏi phán quyết. Thay bằng **hiệu ứng tới hạn** t₁₋α′ · SE, chỉ phụ thuộc α.
4. **A/A: bỏ TOST và biên MDE.** Thay bằng kiểm định đổi dấu chính xác hai phía ở mức 2α = 0,05 trên hai nhánh không skill mới. Bác bỏ → "chưa kết luận: pipeline đáng ngờ".
5. Trần ghi nhận **33,4 USD** = 35 − 1,6 (chi phí tối đa của hai lô bị ngắt chưa ghi). Tiến trình đang chạy dùng 33,5. Với tổng chi dự kiến khoảng 31 USD, trần này không bao giờ chạm, nên không ảnh hưởng. Lần chạy lại sẽ dùng 33,4.
6. Không đổi: endpoint resolved; chọn "Z < 0"; tách dữ liệu; m = 3 seed (11, 21, 31); Holm với α một phía 0,025; quy tắc phán quyết PASS / FAIL / chưa kết luận.

Đầu vào giá trị duy nhất còn lại: **α = 0,025 một phía** (chuẩn ICH E9).
