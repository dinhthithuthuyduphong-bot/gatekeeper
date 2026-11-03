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

## 6. RQ1 thu nhỏ: Gatekeeper so với quy tắc nhận ngây thơ (bổ sung 03/11/2026, **trước khi có dữ liệu E1**)

@thuthuy duyệt 65 USD cho E1 cộng phần này. Đây là phép kiểm **trực tiếp** luận điểm chính của paper ở quy mô nhỏ.

**Skill có hại theo thiết kế** (`configs/skills/harm-*.json`): các hướng dẫn trông hợp lý nhưng sai.
- `harm-swallow-exceptions`: nuốt exception thay vì sửa logic.
- `harm-minimal-edit`: chỉ được sửa 1 dòng.
- `harm-skip-verification`: không chạy test.

Nhãn "có hại" **không được giả định** mà được kiểm trên seed giữ lại.

- **Tập task:** 40 task đầu tiên của hợp các task E1, theo thứ tự ngẫu nhiên `random.Random("2027-harm")`. Tập này chung cho 3 skill có hại; tập của các skill E1 là 40 task dùng được đầu tiên của mỗi skill. Cả hai được ghi vào `configs/pools/e1_task_sets.json` (`scripts/make_e1_selection.py`) trước mọi lần chạy, và truyền vào bằng `--task-sets`.
- **Chạy:** cùng lượt với E1 (cùng seed 41/51/61, cùng 250 bước), dùng chung nhánh `none`.
- **Ô (cell):** 3 skill E1 + 3 skill có hại + `validation-error` (dữ liệu G1: sàng lọc bằng seed 11, giữ lại seed 21 và 31). Tổng K = 7.
- **Dữ liệu quyết định (sàng lọc):** seed đầu tiên (41; với validation-error là 11), mỗi task 1 trial, theo thứ tự task ngẫu nhiên `random.Random("2027-order")`.
- **Nhãn thật (giữ lại, độc lập):** hai seed còn lại. STR_thật = trung bình theo task.
  - có hại nếu > 0;
  - có ích nếu < 0 (θ = 0);
  - trung tính nếu = 0.
  - Kèm kiểm định đổi dấu chính xác theo cả hai chiều.
- **Các quy tắc so sánh:**
  - **Gatekeeper:** e-process aGRAPA (c = 0,5; prior (0; 1; 1); Waudby-Smith & Ramdas), H₀: E[Z] ≥ 0, α mỗi ô = 0,05 / 7 (`AlphaLedger.from_plan`), admit khi E ≥ 1/α trong ngân sách 40 trial.
  - **Nhận ngây thơ (plug-in):** admit nếu trung bình Z trên dữ liệu sàng lọc < 0. Đây là quy tắc sàng lọc của C ở G1.
  - **B1:** không bao giờ admit. **B2:** luôn admit.
  - Không tự cài lại XRepoSkill, MemGovern hay gskill (`baselines.py`: baseline bên thứ ba phải chạy từ code gốc).
- **Đại lượng:** harmful acceptance = số ô có hại được admit / số ô có hại; clean-reuse coverage = số ô có ích được admit / số ô có ích; STR_thật trung bình của các ô được admit.
- **Kiểm chéo bên ngoài:** cùng các quy tắc trên 392 ô SWE-Skills-Bench; sàng lọc trên requirement 1–5, nhãn trên 6–10 và ngược lại; α mỗi ô = 0,05 / 392. Phân tích thăm dò, vì dữ liệu đã được xem trước.
- **Giới hạn phải nêu:** 7 ô là quy mô nhỏ; chỉ có các quy tắc quyết định, chưa có baseline bên thứ ba; nhãn thật dựa trên 80 trial mỗi ô nên vẫn có nhiễu.

Mã: `scripts/rq1_mini.py`; test: `tests/test_rq1_mini.py`.

**Bổ sung §6.1** (03/11/2026, E1 vừa chạy lô đầu, **chưa mở kết quả nào**; phản biện của thầy, `docs/advisor_qa.md` §5.2e):
- **Nhãn chính là nhãn 3 lớp theo kiểm định** trên hai seed giữ lại: *có hại đã xác lập* hoặc *có ích đã xác lập* nếu kiểm định đổi dấu chính xác một phía bác bỏ ở α mỗi ô = 0,05/7; còn lại là *chưa xác định*, được báo cáo riêng (số ô chưa xác định mà mỗi quy tắc đã admit).
- Nhãn theo dấu của ước lượng điểm chỉ là phân tích phụ.

**Ghi chú ngân sách** (03/11/2026, chưa mở kết quả nào): chi phí đo được là khoảng 0,20 USD mỗi task cho mỗi seed (250 bước), nên dự kiến E1 tốn 68–72 USD. @thuthuy duyệt thêm 10 USD, nâng ngân sách E1 lên **75 USD**; trần ghi nhận trong driver = 31,26 + 75 = **106,26 USD**. Thiết kế không đổi.
