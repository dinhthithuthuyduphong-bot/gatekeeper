# Đăng ký trước: thí nghiệm E2 (skill của bên thứ ba trên repo mới)

Ghi và commit ngày 03/11/2026, **trước khi có bất kỳ dữ liệu E2 nào**: chưa chạy bước chọn rule, chưa có lần chạy agent nào, và kết quả kiểm định pool chưa về. @thuthuy duyệt ngân sách **45 USD** ("chạy luôn"). Căn cứ: `docs/advisor_qa.md` §5.2–§5.3 (phản biện của thầy: skill tự sinh có minh bạch không, skill có hại thật hay chỉ là "người rơm").

## 1. Câu hỏi

Một hệ skill do **người khác** công bố là XRepoSkill. Hệ này học skill từ trajectory SWE-bench Verified của 11 repo Python. Câu hỏi: khi đem hệ này áp lên **repo nó chưa từng thấy**, nó giúp, hại hay không đổi tỉ lệ resolved của agent?

- Đây là phép đo **chuyển giao âm thật** (negative transfer): skill hợp lý ở nơi học nhưng có thể hại ở nơi khác. Đây chính là tình huống Gatekeeper được thiết kế để chặn.
- Không có lựa chọn nào trong thiết kế dựa trên dữ liệu: skill, cách chọn rule và cách chèn đều lấy nguyên từ bản gốc.

## 2. Skill: lấy nguyên từ bản gốc

| Mục | Giá trị | Cơ sở |
| --- | --- | --- |
| Mã nguồn | XRepoSkill, commit `26fd70345698108c0fdce2d8904293a38b9cd42f` (đã ghim; script kiểm tra commit trước khi chạy) | Tái lập |
| Skill | 36 chiến lược chung trong `data/general_strategies_36.md` | Là bản skill duy nhất họ công bố |
| Chọn rule cho mỗi issue | `RetrievalFlow` của họ, **không sửa**: 2 lần gọi LLM (phân tích, rồi chọn); `top_n = 3`; `issue_max_chars = 6000`; temperature 0; `reasoning_effort` low (mặc định trong `configs/pipeline.yaml` và `retrieval.default_llm`) | Đúng cách họ dùng |
| Backbone của bước chọn | `vertex_ai/gemini-3.1-flash-lite`, cùng model với agent | Họ dùng cùng một backbone cho bước chọn và agent (`models.backbone`) |
| Cách chèn | Khung `SKILL_FRAME` của họ (`<relevant_skills>` … "Verify each step against the actual code before acting"), đặt **trên** đề bài; chỉ chèn tiêu đề và nội dung rule được chọn (`render_rules`) | `rollout.py`, `swebench_pro_with_skills.yaml` |
| Bản quyền | Repo **không có LICENSE**: không commit nội dung rule. Nội dung được tạo lại cục bộ từ commit đã ghim; repo chỉ lưu mã rule được chọn (`results/e2_selection.json`) | Tôn trọng bản quyền mặc định |

**Ba điểm khác bản gốc, đã biết trước và phải nêu trong paper:**

1. Bản đóng gói `SKILL.md` gốc kèm thẻ bằng chứng (support, z). Bản công bố `general_strategies_36.md` không có thẻ này, nên thẻ được thay bằng `strategy <số>` và nội dung là "Trigger: … Action: …" nguyên văn. `scripts/xreposkill_select.py` kiểm tra parser của họ đọc lại đúng 36 rule.
2. Họ đánh giá trên SWE-bench Pro với template agent riêng. Ở đây khung `<relevant_skills>` được đặt ở đầu đề bài, bên trong template SWE-bench mặc định của mini-swe-agent 2.4.6, giống như trong E1.
3. Backbone là Gemini Flash-Lite, không phải DeepSeek. Họ cho phép đổi backbone qua `PIPELINE_MODEL` hoặc `--model`.

## 3. Tập đánh giá

| Mục | Giá trị | Cơ sở |
| --- | --- | --- |
| Nguồn | SWE-bench-Live, bản Python, split `full` (Zhang et al. 2025, arXiv 2505.23419) | Task từ issue thật tạo từ năm 2024; mỗi task có image Docker riêng |
| Loại trừ | Toàn bộ 12 repo của SWE-bench, vì XRepoSkill học từ các repo của Verified | Tránh rò rỉ skill: đánh giá trên repo mới |
| Lấy mẫu | Ngẫu nhiên đơn giản: thứ tự ngẫu nhiên theo seed `"2027-e2"` trên 1.649 ứng viên (215 repo). Kiểm định **120 task đầu** (`configs/pools/e2.json`; `scripts/select_e2_pool.py`) | Như E1 (S1: suy rộng ra tổng thể) |
| Chấm điểm | **Bản fork harness của SWE-bench-Live** (nhánh `python-only`, commit `ad79b850f15e33992e96f03f6e97f05ddf9aa0be`), `--split full --namespace starryzhang`, đúng hướng dẫn trong README của họ. `swebench` 5.0.2 không đọc được `test_cmds` của Live | Đã đọc mã: `make_test_spec` dùng `test_cmds` và `log_parser` của từng task |
| Task dùng được | Gold resolve 2 lần, no-op cho F = 1 và R = 0 (`scripts/validate_pool.py`) | Như G1 và E1 |
| **Tập kích hoạt** | Các task dùng được mà bước chọn của XRepoSkill chọn **≥ 1 rule**. Danh sách được ghi vào `configs/pools/e2_task_sets.json` **trước** mọi lần chạy agent | Là I(x) của hệ skill: không có rule nào được chọn thì prompt giống hệt nhánh `none`. Tỉ lệ kích hoạt được báo cáo |

## 4. Chạy

- **Nhánh:** `none` và `xreposkill` (`configs/skills/xreposkill-e2.json`), trên cùng các task của tập kích hoạt.
- **Model và giới hạn:** như E1: `gemini-3.1-flash-lite`, `reasoning_effort` low, step_limit 250 (mặc định của harness), cost_limit 1,00 USD.
- **Seed:** 41, 51, 61, như E1 để so sánh được. E2 dùng task khác nên không có cặp nào trùng với E1.
- **Thứ tự chạy:** lô 4 task. Mỗi vòng chạy **cùng các task** cho seed 41, rồi 51, rồi 61, sau đó mới sang lô kế tiếp. Nếu chạm trần ngân sách, mọi task đã có đủ 3 seed vẫn dùng được.
- **Cỡ mẫu:** dựa trên nguồn lực (Lakens 2022, "resource constraints").
  - Chi phí đo được trong E1 là 0,0617 USD mỗi lần chạy (62 lần, seed 41).
  - Dự kiến: 45 / (2 nhánh × 3 seed × 0,0617) ≈ 121 task, nhiều hơn số task có thể có. Vì vậy **mọi task trong tập kích hoạt** đều được chạy.
  - Nếu Live đắt hơn, trần dừng việc chạy. Phân tích dùng các task đã có đủ 3 seed và báo cáo hiệu ứng tới hạn tương ứng.
- **Trần:** 45 USD theo số ghi nhận. Trần cộng dồn trong driver = trần của E1 (106,26) + 45 = **151,26 USD**. E2 chạy sau E1 vì cả hai dùng chung ổ đĩa của container.
- **Biến cố xen giữa:** như E1 §3: treatment policy là chính, hypothetical là phân tích độ nhạy, lỗi hạ tầng thì chạy lại hoặc loại khỏi ghép cặp.

## 5. Phân tích (mã đã khóa: `scripts/analyze_g1_final.py`, như E1)

Z_ik = R(none) − R(xreposkill) ∈ {−1, 0, 1}; Z̄_i là trung bình qua 3 seed.

1. **Hai giả thuyết một phía**, mỗi giả thuyết ở α = 0,025 (tương đương hai phía 0,05; ICH E9):
   - **có ích:** E[Z] < 0;
   - **có hại (chuyển giao âm):** E[Z] > 0.
   - Kiểm định chính là đổi dấu chính xác (Hemerik & Goeman 2018), H₀: hai nhánh hoán đổi được.
2. **S1:** t ghép cặp (Student 1908), suy luận cho tổng thể các task được kích hoạt. **S2:** đổi dấu chính xác theo cụm repo (Canay, Romano & Shaikh 2017). Live có nhiều repo nên S2 có ý nghĩa hơn ở E1.
3. **A/A:** nhánh `none` seed 41 so với seed 51, đổi dấu chính xác hai phía, mức 0,05 (Kohavi et al.).
4. **Phán quyết:** có ích hoặc có hại nếu kiểm định chính, S1 và S2 cùng bác bỏ theo chiều đó và A/A không bác bỏ; "chưa kết luận" nếu chỉ kiểm định chính bác bỏ; còn lại là không phát hiện hiệu ứng (kèm hiệu ứng tới hạn và CI 95%).
5. **Gatekeeper trên ô E2** (nối với RQ1, *không* gộp vào K = 7 của E1):
   - quy tắc giống hệt §6 của E1: sàng lọc bằng seed 41; nhãn kiểm định trên seed 51 và 61;
   - ô E2 là giả thuyết riêng với α = 0,05;
   - báo cáo Gatekeeper và quy tắc nhận ngây thơ có admit hệ này không, và nhãn thật là gì.
6. **Chỉ báo cáo, không suy luận:**
   - **Nhiễm dữ liệu:** cùng phân tích, chỉ trên các task có `created_at` sau mốc cắt dữ liệu huấn luyện của model. Google ghi mốc này là tháng 01/2025; nguồn được lấy về qua `configs/sources.json` (`gemini_31_flash_lite_cutoff`).
   - **Theo rule:** với mỗi rule được chọn ở ≥ 10 task, Z̄ trên các task có rule đó. Có nhiễu gây nhiễu (confounding), vì việc chọn rule phụ thuộc issue.
   - Token theo nhánh; tỉ lệ bị cắt; token của bước chọn rule.

## 6. Không làm

- Không thêm seed, task hay skill sau khi thấy dữ liệu; không phân tích giữa chừng.
- Không chỉnh prompt hay rule của XRepoSkill.
- Không chọn lại `top_n`.

**Ghi chú thực thi 1** (03/11/2026, chưa có dữ liệu E2; `docs/audit_pilot.md` A29–A35):
- Pool chỉ nhận task có ≥ 1 test FAIL_TO_PASS. Task có danh sách rỗng thì "resolved" với mọi patch.
- Bước chọn rule bị lỗi API thì được chạy lại; còn lỗi thì không lập tập task.
- Trần = số đã chi ngoài E2 lúc bắt đầu + 45 USD. E2 chỉ chạy khi E1 xong.
- **Lệnh phân tích:** `python scripts/analyze_g1_final.py verdict --label E2 --out results/e2_final.json --skills xreposkill --confirm g2-e2-s41 g2-e2-s51 g2-e2-s61` (giả thuyết có ích: `reject`/`robust`; có hại: `harm`/`harm_verdict`); `python scripts/rq1_mini.py --e2 g2-e2-s41 g2-e2-s51 g2-e2-s61`.

**Ghi chú thực thi 2** (03/11/2026, chưa có dữ liệu E2; áp dụng `docs/research_rules.md` R1–R2):
- **§5.6, phân tích theo rule:** bỏ ngưỡng "≥ 10 task", vì đó là con số tự đặt (N1). Báo cáo **mọi** rule được chọn, kèm số task và Z̄, chỉ để mô tả, không suy luận.
- **§5.6, nhiễm dữ liệu:** mốc cắt dữ liệu huấn luyện "01/2025" **chưa được xác nhận từ bản gốc**. Trang của Google tải được (`sources-snapshots`, sha256 `2d12689d…`) nhưng không chứa thông tin này (N3). Phân tích này **treo** cho đến khi trích được câu gốc. Nếu không trích được thì không làm, và ghi là giới hạn.

**Ghi chú thực thi 3** (03/11/2026, chưa có dữ liệu E2; R2): **cỡ mẫu theo ràng buộc nguồn lực** (Lakens 2022, Table 1).
- n = ⌊45 / (2 × 3 × 0,0617)⌋ = **121** task dùng được và được kích hoạt, lấy **theo đúng thứ tự ngẫu nhiên đã cố định** (`random_order`, seed `"2027-e2"`).
- Nếu khối 120 task đầu chưa đủ 121 task như vậy, kiểm định và chọn rule cho các khối tiếp theo, cũng theo thứ tự đó, đến khi đủ. Không bước nào nhìn vào kết quả của agent.
- Trần 45 USD vẫn là giới hạn cứng. Nếu Live đắt hơn Verified, việc chạy dừng ở trần và phân tích dùng các task đã có đủ 3 seed (§4).
- Thay cho câu "mọi task trong tập kích hoạt" ở §4.

**Ghi chú thực thi 4** (03/11/2026, chưa có dữ liệu E2): như ghi chú thực thi 2 của E1 (A37). Bản vá không áp được tính là không resolved. Image Live có file chưa theo dõi (A36), nhưng chỉ ảnh hưởng tới mô hình giả lập.

**Sai lệch D1** (03/11/2026, trước khi phân tích; `docs/audit_pilot.md` A39):
- **Kết luận chính** (có ích hoặc có hại) = kiểm định chính xác ở mức Holm, theo ICH E9(R1): phép ước lượng chính quyết định, phân tích độ nhạy "explore the robustness of inferences from the main estimator".
- S1 và S2 được báo cáo như phân tích độ nhạy, kèm p nhỏ nhất đạt được của S2.
- Quy tắc đã đăng ký (cả ba cùng bác bỏ) **vẫn được tính và báo cáo** cạnh kết quả (Nosek et al. 2018: sai lệch phải được công khai).
- Lý do: mô phỏng trên dữ liệu G1 cho thấy điều kiện S2 làm power gần 0 với 8 repo, trong khi không làm tỉ lệ sai tốt hơn chuẩn.

**Sai lệch D2** (03/11/2026, trước khi phân tích; `docs/audit_pilot.md` A41):
- **α của RQ1** (Gatekeeper và nhãn đã xác lập) = **0,025 một phía**, theo ICH E9, thay cho 0,05. Lý do: admit là khẳng định một phía, và 0,05 trước đây bị gắn nhầm là "quy ước hai phía".
- θ của Gatekeeper = 0 (trước đây là 1e-9 để lách một ràng buộc không có cơ sở trong mã).
- Quyết định ở α = 0,05 đã đăng ký vẫn được báo cáo (`Gatekeeper (registered alpha, D2)`).
- **Ký hiệu:** "R(none) − R(skill)" ở §4 nghĩa là 1[resolved | none] − 1[resolved | skill] = Z_resolved (`docs/glossary.md` §7).
