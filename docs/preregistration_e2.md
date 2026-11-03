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

**Ghi chú thực thi 5** (03/11/2026, chưa có dữ liệu agent của E2):
- **Kiểm định khối 1** (120 task, run 41585420373): **79 task dùng được**.
  - 36 task bị loại vì patch gold sửa được bug (F = 0) nhưng có test PASS_TO_PASS hỏng **như nhau ở nhánh gold và nhánh no-op** (cùng R). Tức là test đó hỏng bất kể bản vá, và phụ thuộc môi trường chạy. Ví dụ conan-15453: 5/3.573 test.
  - 5 task bị loại vì nhánh no-op không sạch.
  - 0 lỗi hạ tầng.
- Cách loại này đúng theo quy tắc pool (§3): không agent nào đạt "resolved" được trên những task đó, và hai nhánh bị ảnh hưởng như nhau nên Z không bị lệch.
- Phát hiện này được báo cáo trong paper: test PASS_TO_PASS của SWE-bench-Live nhạy với môi trường ở 36/120 task.
- **Khối 2** theo ghi chú thực thi 3: `random_order[120:200]` (`configs/pools/e2b.json`).
  - Cần thêm 42 task dùng được.
  - Với tỉ lệ dùng được 79/120, phân phối Binomial(80; 0,66) cho số task dùng được ≥ 42 với xác suất ≈ 0,996.
  - Chỉ 121 task dùng được và được kích hoạt đầu tiên theo thứ tự ngẫu nhiên được dùng.

**Ghi chú thực thi 6** (03/11/2026, trước khi phân tích; A54, A56):
- **Thứ tự chạy:** các seed **xen kẽ** trên cùng nhóm 4 task, để dùng lại image. Mỗi cặp (skill, không skill) vẫn chạy trong cùng một lô của cùng một seed. Ước lượng và kiểm định không đổi.
- **Khâu chấm:** tuần tự giữa các nhánh (`--score-parallel 1`), để tránh tranh CPU ở khâu nặng CPU nhất.
- **Quá giờ khi chấm** (harness dừng test ở 1.800 s) được tính là **không resolved**, như quy ước chính thức của SWE-bench (giống bản vá không áp được, A37). Phân tích độ nhạy *hypothetical* bỏ thêm các cặp có quá giờ (`harness_test_timeout`).

**Ghi chú thực thi 7** (03/11/2026, chưa có lần chạy agent nào của E2):
- **Kiểm định khối 2** (`random_order[120:200]`, run 41623378275): **59/80 task dùng được**, 0 lỗi hạ tầng (`results/pool_validation/e2b/summary.json`). Hai khối phủ đúng `random_order[0:200]`; tổng cộng 138 task dùng được.
- **Bước chọn rule** cho khối 2: cùng commit, model và cấu hình như khối 1. Kết quả khối 1 được đọc lại từ file, không gọi lại mô hình; 120/120 mục giống hệt lần trước.
  - Kích hoạt: 138/138 task dùng được; 178/179 trên tất cả task đã chọn rule.
  - Chi phí cộng dồn của bước chọn: **0,4454 USD** (khối 1: 0,2946; khối 2: 0,1508). Số này được trừ vào 45 USD của E2.
- **Tập E2:** 121 task kích hoạt đầu tiên theo `random_order` (vị trí cuối: 173), tạo bởi `scripts/make_e2_selection.py --blocks e2 e2b --n 121`, ghi vào `configs/pools/e2_selected.json` và `e2_task_sets.json`.
- **File hướng dẫn:** SHA-256 `59360eb5cc6b45b0f9d5ca7975662aaeb65b863f77f45a99342934fd480e28e4` (178 task). Bản dựng lại chỉ từ mã rule (`scripts/build_e2_guidance.py`) cho cùng SHA.

**Ghi chú thực thi 8** (03/11/2026, chưa có lần chạy agent nào của E2; A60): **chạy trên GitHub Actions với một sổ ngân sách chung.**
- **Máy chạy:** toàn bộ E2 chạy trên runner của GitHub Actions: 20 job song song, cùng phiên bản đã ghim như máy chạy E1. Không trộn hai loại máy trong E2.
- **Chia task:** job k nhận `instances[k::20]` theo thứ tự ngẫu nhiên đã cố định. Mỗi lần gọi chạy 1 task × 2 nhánh. Các seed 41, 51, 61 chạy liền nhau trên cùng task rồi mới sang task kế tiếp. Mỗi cặp vẫn nằm trong một lần gọi của một seed.
- **Ngân sách:** 45 USD trừ 0,4454 USD đã chi cho bước chọn rule, còn **44,5546 USD**, giữ bằng sổ chung `scripts/e2_ledger.py` (nhánh `e2-ledger`):
  - trước mỗi lần gọi, job giữ chỗ phần xấu nhất: 2 nhánh × 1 task × `cost_limit` 1,00 USD = 2,00 USD, đúng giới hạn mà driver dùng;
  - sau lần gọi, job ghi số thật và trả phần giữ chỗ;
  - ghi theo kiểu so-và-đổi: git từ chối lần đẩy dựa trên bản đã cũ.

  Vì vậy tổng đã chi cộng tổng đang giữ chỗ luôn ≤ trần, và tổng chi không thể vượt trần.
- **Dừng:** job dừng khi tổng đã chi cộng 2,00 USD vượt trần, hoặc khi hết thời gian. Lần gọi nào không ghi được kết quả thì giữ nguyên phần giữ chỗ, vì chi phí của nó chưa biết. Như §4: phân tích dùng các task đã có đủ 3 seed. Một task có thuộc tập phân tích hay không phụ thuộc vào thời gian và chi phí của các task khác, không phụ thuộc kết quả của chính nó.
- **Hệ quả của sổ chung (bổ sung ghi chú thực thi 8, trước lần chạy có trả phí):**
  - Số lần gọi chạy cùng lúc = min(20, ⌊(trần − đã chi) / 2,00⌋). Mỗi lần gọi giữ chỗ phần xấu nhất 2,00 USD, trong khi chi phí đo được khoảng 0,14 USD.
  - Vì vậy về cuối, số job chạy cùng lúc giảm dần. Đây là cái giá của bảo đảm "không thể vượt trần".
  - Job nào không giữ được chỗ thì chờ, rồi dừng khi hết giờ. Lần dispatch sau chạy tiếp (cùng 20 shard).
  - Task không xong chỉ phụ thuộc vào shard và thời gian. Task được chia vào shard theo thứ tự ngẫu nhiên đã cố định, nên tập có đủ 3 seed vẫn là một mẫu ngẫu nhiên, không phụ thuộc kết quả của chính task.
- **Bằng chứng chạy thử trên Actions** (run 41656611463, `budget_usd` 3, 2 job): k1 giữ chỗ 2,00 → ghi số thật → giữ chỗ lại. k0 phải chờ, vì 2 + 2 > 3. Bất biến không bị vi phạm trong suốt lịch sử nhánh sổ.

**Ghi chú thực thi 9** (03/11/2026, trước khi có kết quả E2 nào; A62): **dữ liệu thiếu do lỗi hạ tầng.**
- **Phân loại theo ICH E9(R1)** (bản gốc `sources-snapshots/data/sources/ich_e9_r1.json`, sha256 `f7471f41…`):
  - Lỗi hạ tầng (ví dụ Vertex trả 429 sau 10 lần thử) là việc **không đo được** kết quả, không phải do can thiệp gây ra. ICH: "the addendum distinguishes discontinuation of randomised treatment from study withdrawal. The former represents an intercurrent event […]. The latter gives rise to missing data to be addressed in the statistical analysis". Lỗi hạ tầng thuộc loại thứ hai: **dữ liệu thiếu**.
  - Cách chạy lại (§4) giả định việc thiếu không liên quan đến kết quả. ICH yêu cầu: "To explore the robustness of inferences from the main estimator to deviations from its underlying assumptions, a sensitivity analysis should be conducted".
- **Bằng chứng hiện có:**
  - Lần chạy dài giải được ít hơn: trên 1.037 lần chạy của pilot, tỉ lệ giải được là 0,729 khi có 0–29 lời gọi LLM và 0,065 khi có 120–250 (Mann–Whitney một phía, p = 6,8 × 10⁻⁴⁷). Nếu xác suất lỗi tăng theo số lời gọi, việc chạy lại sẽ thiên về lần chạy ngắn.
  - Nhưng cả 2 lần lỗi 429 đã gặp (lô g1-e1x-s41-p03) đều xảy ra **ở lời gọi đầu tiên** (0 lời gọi hoàn tất), nên chúng không liên quan đến kết quả. Với n = 2 thì không kết luận được chiều nào. Vì vậy phân tích độ nhạy là cần, và nó là một kiểm tra, không phải giả định rằng có lệch.
- **Ước lượng chính:** không đổi (chạy lại, như §4).
- **Báo cáo thêm:**
  - số và tỉ lệ lần chạy lỗi hạ tầng theo từng nhánh, lấy từ `infra_failures` của từng file lô (dữ liệu của lần đầu vẫn còn);
  - **phân tích độ nhạy S-infra:** với mỗi (task, seed), chỉ dùng **lần chạy đầu tiên**; nhánh nào lỗi hạ tầng ở lần đó thì tính là không giải được. Ước lượng, CI và kiểm định giống ước lượng chính. Đây là giới hạn bất lợi cho nhánh bị lỗi nhiều hơn.
- Nếu không có lỗi hạ tầng nào thì S-infra trùng với ước lượng chính, và chỉ ghi như vậy.

**Ghi chú thực thi 10** (03/11/2026, chỉ trường vận hành, chưa phân tích): **lượt dispatch 1** (run 41659629033) **và lượt nối tiếp.**
- **Lượt 1:**
  - 329 file lô, 658 lần chạy agent.
  - Chi 40,0719 USD, khớp đúng sổ ngân sách.
  - `runs == scored + infra` ở mọi nhánh; 0 lệch tiêu chí giải được; 0 quá giờ khi chấm; 4 bản vá không áp được (tính là không giải được).
  - 8 lỗi hạ tầng (RateLimitError 429): 6 ở `none`, 2 ở `xreposkill`. Đây là dữ liệu thiếu; S-infra đã đăng ký ở ghi chú thực thi 9.
  - 103 task có đủ 3 seed.
- **Bước gom:** thất bại vì va chạm khi đẩy lên `raw-archive` (A68). Đã chạy lại bước gom; kết quả nay đã lên `e2-results`.
- **Lượt nối tiếp:** cùng 20 shard, cùng ngân sách 45 USD, chạy bằng mã đã sửa (A61, A68). Lượt này lấy kết quả cũ từ `e2-results`, nên không chạy lại task đã xong. Nó dừng ở trần như §4.

**Ghi chú thực thi 11** (03/11/2026, khoảng 22:00 UTC, chỉ trường vận hành, **chưa phân tích**): **E2 kết thúc ở trần** (§4).
- **Lượt nối tiếp:** run 41715903458.
- **Tổng cộng hai lượt:**
  - 344 file lô, 688 lần chạy agent, chi 42,5931 USD (khớp đúng sổ ngân sách, không còn khoản giữ chỗ). Cộng bước chọn rule là **43,04 / 45 USD**.
  - `runs == scored + infra` ở mọi nhánh; 0 lệch tiêu chí giải được; 0 quá giờ khi chấm; 4 bản vá không áp được.
  - 8 lỗi hạ tầng (429), đã được chạy lại.
- **Tập phân tích:** **109 task có đủ 3 seed**, theo quy tắc của `per_task_mean`. Số task xong theo từng seed: 113 / 114 / 110.
- **Power mô phỏng** ở n = 109: khoảng 0,89 ở δ = 0,109 (nội suy giữa 0,873 ở n = 105 và 0,936 ở n = 121, `results/e2_power_final.json`).
- File kết quả được chép từ `e2-results` vào **`results/e2/`** (không phải `results/pilot/`, A69) để phân tích. Phân tích chỉ chạy sau khi bản đăng ký trước của thí nghiệm chính được commit (L27).
