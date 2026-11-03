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

@thuthuy duyệt 65 USD cho E1 cộng phần này. Đây là phép kiểm **trực tiếp** luận điểm chính của paper trên K = 7 ô, mỗi ô 40 trial sàng lọc.

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
- **Giới hạn phải nêu:** K = 7 ô, nên mỗi tỉ lệ (ví dụ harmful acceptance) chỉ nhận các giá trị k / (số ô đã xác lập); chỉ có các quy tắc quyết định, chưa có baseline bên thứ ba; nhãn thật dựa trên kiểm định với 80 trial mỗi ô, và xác suất xác lập theo δ có ở `docs/method_check.md` (C10).

Mã: `scripts/rq1_mini.py`; test: `tests/test_rq1_mini.py`.

**Bổ sung §6.1** (03/11/2026, E1 vừa chạy lô đầu, **chưa mở kết quả nào**; phản biện của thầy, `docs/advisor_qa.md` §5.2e):
- **Nhãn chính là nhãn 3 lớp theo kiểm định** trên hai seed giữ lại: *có hại đã xác lập* hoặc *có ích đã xác lập* nếu kiểm định đổi dấu chính xác một phía bác bỏ ở α mỗi ô = 0,05/7; còn lại là *chưa xác định*, được báo cáo riêng (số ô chưa xác định mà mỗi quy tắc đã admit).
- Nhãn theo dấu của ước lượng điểm chỉ là phân tích phụ.

**Ghi chú ngân sách** (03/11/2026, chưa mở kết quả nào): chi phí đo được là khoảng 0,20 USD mỗi task cho mỗi seed (250 bước), nên dự kiến E1 tốn 68–72 USD. @thuthuy duyệt thêm 10 USD, nâng ngân sách E1 lên **75 USD**; trần ghi nhận trong driver = 31,26 + 75 = **106,26 USD**. Thiết kế không đổi.

**Ghi chú thực thi 1** (03/11/2026, rà soát toàn bộ mã trước khi chạy tiếp; **chưa phân tích kết quả nào**; `docs/audit_pilot.md` A24–A35):
- **Lệnh phân tích §4** (họ Holm = **3 skill E1**; skill có hại thuộc §6, không thuộc họ này):
  `python scripts/analyze_g1_final.py verdict --label E1 --out results/e1_final.json --skills null-guard,type-guard,exception-handling --confirm g1-e1-s41 g1-e1-s51 g1-e1-s61` (A/A = hai run đầu: seed 41 so với 51).
- **Lệnh §6:** `python scripts/rq1_mini.py --e1 g1-e1-s41 g1-e1-s51 g1-e1-s61 --g1 g1-c-s11 g1-c-s21 g1-c-s31`. Thứ tự sàng lọc trong mã nay đúng là `random.Random("2027-order")` như §6; mọi quy tắc dùng cùng 40 trial đầu.
- **cost_limit (§2):** lập luận "chi phí tăng gần bình phương" là ngoại suy không có nguồn. Thay bằng số đo: lần chạy đắt nhất trong 80 lần đầu là 0,53 USD, không lần nào chạm 1,00 USD. Giới hạn này vẫn không ràng buộc.
- **§3:** trạng thái kết thúc của từng lần chạy nay được lưu, gồm cả 7 lô đầu (bổ sung từ trajectory), nên tỉ lệ bị cắt và phân tích *hypothetical* làm được.
- **Giới hạn đã biết trước khi phân tích:** S2 với G = 8–9 repo có p nhỏ nhất 2⁻ᴳ (0,0039 hoặc 0,0020). Con số này được báo cáo cạnh kết quả (`docs/audit_pilot.md` C7).

**Ghi chú thực thi 2** (03/11/2026, chưa phân tích kết quả nào; `docs/audit_pilot.md` A37):
- Bản vá của agent không áp được là **đầu ra của agent**, nên tính là không resolved (treatment policy, §3).
- Trường hợp này **không** thuộc dòng "lỗi hạ tầng → chạy lại" của §3. Cơ sở: SWE-bench (Jimenez et al. 2024, Table 5) tính % Resolved trên mọi task, cạnh % Apply.
- Các lô E1 tới nay có 0 ca như vậy.

**Ghi chú thực thi 3** (03/11/2026, chưa phân tích kết quả nào; `docs/method_check.md`, A38):
- Power ở §2 tính với α′ = 0,025, chưa tính Holm trên 3 skill và điều kiện S2. Đúng theo công thức là n ≈ 53 ở mức Holm đầu.
- Thiết kế **không đổi** (R5). Power đã sửa (plasmode) được báo cáo cạnh kết quả.

**Sai lệch D1** (03/11/2026, trước khi phân tích; `docs/audit_pilot.md` A39):
- **Kết luận chính** (có ích hoặc có hại) = kiểm định chính xác ở mức Holm, theo ICH E9(R1): phép ước lượng chính quyết định, phân tích độ nhạy "explore the robustness of inferences from the main estimator".
- S1 và S2 được báo cáo như phân tích độ nhạy, kèm p nhỏ nhất đạt được của S2.
- Quy tắc đã đăng ký (cả ba cùng bác bỏ) **vẫn được tính và báo cáo** cạnh kết quả (Nosek et al. 2018: sai lệch phải được công khai).
- Lý do: mô phỏng trên dữ liệu G1 cho thấy điều kiện S2 làm power gần 0 với 8 repo, trong khi không làm tỉ lệ sai tốt hơn chuẩn.

**Ghi chú thực thi 4** (03/11/2026; @thuthuy duyệt ngân sách E1 = 80 USD; chưa phân tích kết quả nào; A38, A40):
- **Cỡ mẫu:** n = **53** task mỗi skill E1 = (z₁₋₀,₀₂₅/₃ + z₀,₈)² · 0,060 / 0,109² ≈ 52,9 (công thức §2, ở mức Holm đúng).
- **Cách lấy task:** task 41–53 theo đúng thứ tự ngẫu nhiên đã cố định (`scripts/make_e1_extension.py`). Đã kiểm 40 task đầu trùng với tập đang chạy.
- **Cách chạy:** giai đoạn riêng `g1-e1x-s41/51/61`, cùng seed, model, step_limit và cost_limit.
- **Không đổi:** skill có hại và RQ1 thu nhỏ (§6) giữ 40 task đã đăng ký và chỉ dùng giai đoạn gốc.
- **Trần:** 31,26 + 80 = 111,26 USD.
- **Lệnh phân tích §4** thay cho ghi chú thực thi 1:
  - `python scripts/combine_runs.py g1-e1all-s<seed> g1-e1-s<seed> g1-e1x-s<seed>` cho từng seed 41, 51, 61;
  - rồi `python scripts/analyze_g1_final.py verdict --label E1 --out results/e1_final.json --skills null-guard,type-guard,exception-handling --confirm g1-e1all-s41 g1-e1all-s51 g1-e1all-s61`.
  - Kết luận chính: `verdict_ich_e9_r1` (sai lệch D1). Quy tắc đã đăng ký: `verdict`.

**Sai lệch D2** (03/11/2026, trước khi phân tích; `docs/audit_pilot.md` A41):
- **α của RQ1** (Gatekeeper và nhãn đã xác lập) = **0,025 một phía**, theo ICH E9, thay cho 0,05. Lý do: admit là khẳng định một phía, và 0,05 trước đây bị gắn nhầm là "quy ước hai phía".
- θ của Gatekeeper = 0 (trước đây là 1e-9 để lách một ràng buộc không có cơ sở trong mã).
- Quyết định ở α = 0,05 đã đăng ký vẫn được báo cáo (`Gatekeeper (registered alpha, D2)`).
- **Ký hiệu:** "R(none) − R(skill)" ở §4 nghĩa là 1[resolved | none] − 1[resolved | skill] = Z_resolved (`docs/glossary.md` §7).
