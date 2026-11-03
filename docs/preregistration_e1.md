# Đăng ký trước: thí nghiệm E1 (xác nhận skill, gộp scope)

Ghi và commit ngày 03/11/2026, **trước khi có bất kỳ dữ liệu E1 nào** (pool chưa được chọn xong, chưa có lần chạy agent nào). Căn cứ: `docs/g1_verdict.md` §2 (quy tắc Bổ sung 4 chọn thiết kế này) và §4 (A22: sửa trần bước). @thuthuy: "làm điều tốt nhất cho paper".

## 1. Câu hỏi

Mỗi skill trong ba skill theo họ mẫu sửa (`null-guard`, `type-guard`, `exception-handling`) có làm thay đổi tỉ lệ resolved của agent trên các task mà nó được kích hoạt hay không: giúp (giả thuyết chính) hoặc hại (giả thuyết phụ, an toàn)?

- **Không chọn skill dựa trên dữ liệu C.** Cả ba skill đều được kiểm, nên không có "lời nguyền người thắng" ở bước chọn.
- `validation-error` không nằm trong E1, vì G1 đã loại trừ hiệu ứng có ích > 0,057.

## 2. Thiết kế

| Mục | Giá trị | Cơ sở |
| --- | --- | --- |
| Tổng thể | Mọi task trong tập test SWE-bench đầy đủ (Jimenez et al. 2024), trừ các repo của SWE-Gym train, mà I(x) của skill đúng | R13; tách theo repo |
| Lấy mẫu | **Ngẫu nhiên đơn giản không hoàn lại**: thứ tự ngẫu nhiên theo `random.Random("2027-<skill>")`, kiểm định pool theo thứ tự đó, lấy **40 task dùng được đầu tiên** | Lấy mẫu ngẫu nhiên cho phép suy rộng ra tổng thể (S1); không cần biên dự phòng |
| n = 40 / skill | Công thức cỡ mẫu với δ = 0,109 (phân vị 5% của SWE-Skills-Bench), power 80%, 3 seed, V đo từ G1 | `docs/g1_verdict.md` §2 (Cohen 1988; Lakens 2022) |
| Task dùng được | Gold resolve 2 lần, no-op cho F = 1 và R = 0 (`scripts/validate_pool.py`) | Như G1 |
| Nhánh | `none` và skill. Nhánh `none` chạy một lần trên hợp các task của 3 skill, dùng chung | Như G1 |
| Seed | **41, 51, 61** | Phải khác mọi seed đã dùng (1, 2, 11, 21, 31) và khác seed + 1 của đối chứng nhiễu; bước 10 như G1 |
| Model | `gemini-3.1-flash-lite`, `reasoning_effort` low (Vertex AI, `global`) | Giữ như pilot để so sánh được |
| **step_limit** | **250** | **Mặc định của harness** (`mini-swe-agent` 2.4.6, `swebench.yaml`); sửa A22 |
| cost_limit | 1,00 USD / lần chạy | Tham số bảo vệ, không ràng buộc. Lần chạy đắt nhất ở 100 bước là 0,129 USD; chi phí tăng gần bình phương theo số bước, nên 250 bước cho khoảng (2,5)² × 0,129 ≈ 0,81 < 1,00. Lần chạy nào chạm giới hạn này được ghi là bị cắt |
| Endpoint chính | Resolved của SWE-bench (mã harness `get_resolution_status`) | Đã đối chiếu: khớp 100% |

## 3. Biến cố xen giữa (ICH E9(R1))

| Biến cố | Chiến lược | Lý do |
| --- | --- | --- |
| Agent chạm trần 250 bước hoặc cost_limit (không nộp bản sửa) | **Treatment policy** (chính): tính là không resolved. Đây là kết quả của chính chính sách "agent + skill + ngân sách này" | Là điều người dùng thật gặp phải |
| Như trên | **Hypothetical** (phân tích độ nhạy): bỏ các cặp có một nhánh bị cắt | Ước lượng hiệu ứng "nếu không bị cắt"; có thể lệch vì việc bỏ cặp phụ thuộc biến xảy ra sau khi áp skill. Chỉ báo cáo |
| Lỗi hạ tầng (container, harness) | Chạy lại; nếu vẫn lỗi thì loại khỏi ghép cặp | Không phải hành vi của agent |

## 4. Phân tích (áp máy móc: `scripts/analyze_g1_final.py`, cùng mã đã khóa ở G1)

Với mỗi skill s, Z_ik = R(none) − R(skill) ∈ {−1, 0, 1}; Z̄_i là trung bình qua 3 seed.

1. **Kiểm định chính:** đổi dấu chính xác, một phía (giúp), H₀: hai nhánh hoán đổi được (Hemerik & Goeman 2018).
2. **Holm** trên 3 skill, α nhóm một phía = 0,025 (ICH E9).
3. **S1:** kiểm định t ghép cặp một phía (Student 1908). Nhờ lấy mẫu ngẫu nhiên, S1 cho suy luận về **tổng thể** các task được kích hoạt.
4. **S2:** đổi dấu chính xác theo cụm repo (Canay, Romano & Shaikh 2017).
5. **A/A:** nhánh `none` seed 41 so với seed 51, đổi dấu chính xác hai phía, mức 0,05 (Kohavi et al.).
6. **Phán quyết cho mỗi skill:**
   - **có ích** nếu kiểm định chính, S1 và S2 cùng bác bỏ ở mức Holm của skill đó, và A/A không bác bỏ;
   - "chưa kết luận" nếu chỉ kiểm định chính bác bỏ;
   - còn lại: không phát hiện hiệu ứng có ích (kèm hiệu ứng tới hạn và CI 95%).
7. **Giả thuyết phụ (an toàn), chỉ báo cáo:** cùng các kiểm định ở chiều *hại* (một phía ngược lại), Holm trên 3 skill, α = 0,025.
8. **Báo cáo kèm:**
   - tỉ lệ bị cắt theo nhánh;
   - endpoint loss;
   - token (input, cache, output) theo nhánh;
   - so sánh với kết quả sàng lọc 1 seed ở C. Đây là "lời nguyền người thắng" như một kết quả của paper.

## 5. Ngân sách và dừng

- Trần riêng của E1: **40 USD** theo số ghi nhận. Trần cộng dồn trong driver = 31,26 (pilot đã ghi) + 40 = **71,26 USD**. Chạm trần → dừng, báo @thuthuy, và phán quyết "chưa kết luận" cho skill thiếu dữ liệu.
- Không dừng sớm vì kết quả: không có phân tích giữa chừng.
- Không thêm skill, seed hay task sau khi thấy dữ liệu.
