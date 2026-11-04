# BẢN NHÁP: Đăng ký trước thí nghiệm chính (RQ1, Gatekeeper)

> **Trạng thái:** bản nháp, chưa đăng ký.
> - Phải được commit thành bản chính thức **trước khi phân tích E1/E2** (L27). Sau mốc đó, dữ liệu E1/E2 không còn dùng làm đoạn đầu được nữa.
> - Mục đánh dấu **[@thuthuy]** chờ @thuthuy quyết (mục "Quyền quyết định" trong `CLAUDE.md`). Mục **[mô phỏng]** chờ kết quả plasmode, chạy trước khi đăng ký.
> - Soạn ngày 03/11/2026. Chưa xem kết quả nào của E1/E2, trừ lần xem ngoài kế hoạch đã công bố ở A66 (tỉ lệ giải gộp theo nhánh); không quyết định nào dưới đây dùng số liệu đó.

## 1. Câu hỏi (RQ1)

Với mỗi ô (skill, scope), Gatekeeper (e-process, admit khi E_n ≥ 1/α_ô) có:
- **(a) An toàn:** không admit ô có hại hoặc trung tính, với xác suất sai ≤ α_ô (Theorem 4′; `docs/theory/proofs.md`);
- **(b) Độ phủ:** admit được ô thật sự có ích với số trial khả thi?

So sánh với quy tắc sàng lọc ngây thơ (plug-in) trên cùng dữ liệu.

## 2. Quyết định đã chốt (tự quyết vì là phương án trội hoặc theo chuẩn; lý do kèm theo)

| Mục | Giá trị | Lý do và nguồn |
| --- | --- | --- |
| Model | Gemini 3.1 Flash-Lite, cấu hình như E1/E2 | Hướng @thuthuy đã chọn ("thí nghiệm chính với Gemini"); điều kiện để nối tiếp E1/E2 |
| θ | 0 | Sai lệch D2; chi phí–lợi ích ≤ 0 (nhánh skill không đắt hơn); θ = 0 cho số trial ít nhất. Lakens 2018: mọi θ > 0 phải có căn cứ |
| α tổng | 0,025 một phía | ICH E9 (đã lưu) |
| Chia α | α_ô = 0,025 / K, chia đều cho K ô đăng ký trước | `docs/number_provenance.md` (thay chia 70/20/10 tự đặt) |
| e-process | aGRAPA, c = 0,5 | Waudby-Smith & Ramdas; c chọn bằng GRO (`results/gro_c.json`) |
| **Đơn vị trial** | **một task** (giả định SP, `proofs.md` §0). Giá trị trial = Z của task: trung bình qua các seed nếu task có nhiều seed (E1/E2: 3 seed), hoặc Z của một lần chạy (phần mới) | Mọi trial nằm trong [−1, 1] và có kỳ vọng có điều kiện bằng STR, nên Bổ đề E đúng dù các trial không cùng phân phối |
| **Nối tiếp E1/E2** | Trial của E1 (null-guard, type-guard, exception-handling và 3 skill có hại) và của E2 (xreposkill) là đoạn đầu của chuỗi e-process của ô tương ứng, theo đúng thứ tự ngẫu nhiên đã cố định | Anytime-valid: "optional stopping or continuation for any reason" (Ramdas, Grünwald, Vovk & Shafer, đã lưu). Có lợi hoàn toàn: tiết kiệm 11–55% số trial mỗi ô |
| Task mới | Lấy tiếp theo `random_order` đã cố định của từng pool, sau các task đã dùng; mỗi task một lần | Giữ giả định SP; không chọn task theo kết quả |
| Dừng | Mỗi ô dừng khi admit, hoặc khi hết số trial phân cho ô | Ville: hợp lệ với mọi thời điểm dừng |
| Thước đo phụ | Tỉ lệ phương sai ghép cặp (Prop. 9) đo trên nhánh `none` và các nhánh skill | Nối Prop. 9 với thực nghiệm |
| Đầu vào mô phỏng | q từ **nhánh không skill** của E1 (112 task) và E2 (121 task), không dùng nhánh skill | Tham số nền, không vi phạm R5. Tốt hơn 32 task của G1 (`results/power_input_uncertainty.json`) |

## 3. Giới hạn đã biết trước (phải ghi trong paper)

| Ô | Task kích hoạt có thể dùng (ước) | Trial cần để admit ở δ = 0,109 | Hệ quả |
| --- | --- | --- | --- |
| null-guard | khoảng 122 | 216–470 | **Không thể admit** dù bao nhiêu tiền. Chỉ kiểm được vế an toàn |
| exception-handling | khoảng 200 | 216–470 | Sát ngưỡng |
| type-guard | khoảng 309 | 216–470 | Có thể |
| xreposkill (E2) | khoảng 1.100 (1.649 ứng viên × 69% dùng được × 99% kích hoạt) | 216–470 | Có thể |
| 3 skill có hại | như skill gốc | không áp dụng (đối chứng an toàn) | Kiểm vế (a) |

Nguồn: số task kích hoạt `data/activation.json` × 86/89 (`docs/g1_verdict.md`); số trial cần `results/design_table_plasmode.json`. Số trial cần sẽ được tính lại bằng q mới **[mô phỏng]**.

## 4. Còn mở

1. **[@thuthuy] Ngân sách B.** Quyền: ngân sách mới. Ảnh hưởng: chi phí một trial mới (1 task × 2 nhánh × 1 seed) ≈ 2 × 0,064 = 0,13 USD (đo ở E1 và E2). Ví dụ B = 114,6 USD (3 triệu VND theo tỉ giá Vietcombank ngày 04/10) cho khoảng 890 trial mới. Lời khuyên: chờ kết quả mô phỏng ở mục 2, rồi chọn B để ít nhất một ô có ích đạt power admit ≥ mức đã báo cáo ở §5.
2. **[mô phỏng] Phân trial giữa các ô.** Đây là phương án trội nếu chỉ dồn trial cho các ô có thể admit (type-guard, xreposkill) mà không làm yếu vế an toàn. Vế an toàn đã đủ với số trial hiện có, vì nó không cần trial để "không admit". Sẽ tính bằng plasmode trước khi đăng ký.
3. **[@thuthuy] Số seed của phần mới: 1 seed, hay kết hợp với một tập con 2 seed** để đo nhiễu và làm A/A. Đây là đánh đổi: 1 seed rẻ hơn 13% cho cùng độ chính xác, nhưng mất phép đo nhiễu trong cùng task. Lời khuyên: kết hợp; kích thước tập con tính bằng mô phỏng.
4. **[mô phỏng] Nhãn "thật" để chấm độ phủ.** Ô nào thật sự có ích hay có hại phải được ước trên dữ liệu tách rời với dữ liệu admit (Rinaldo et al., đã lưu: tách dữ liệu). Cần chốt cách tách trước khi đăng ký.

## 5. Phân tích (sẽ khóa mã trước khi chạy)

- Với mỗi ô: quyết định admit hay không, số trial đã dùng, và E_n cuối.
- Harmful acceptance và clean-reuse coverage, kèm khoảng tin cậy chính xác (Clopper–Pearson; ⏳ cần nguồn).
- So với plug-in trên cùng trial.
- Phân tích độ nhạy: S-infra (dữ liệu thiếu do lỗi hạ tầng), và bỏ các trial có quá giờ khi chấm (như E1/E2).

## 6. Kết quả mô phỏng thiết kế (`scripts/main_design_sim.py` → `results/main_design_sim.json`, 03/11/2026)

- **Đầu vào:** q của nhánh `none`: E2 (Live, 109 task) cho ô xreposkill; giai đoạn mở rộng E1 (37 task × 3 seed) cho các ô E1.
- **Thiết lập:** α_ô = 0,025/7 = 0,0036; θ = 0. Đoạn đầu là trial E1/E2 (trung bình 3 seed), đoạn sau là trial mới (1 seed). Mỗi ô 400 lần lặp (sai số Monte Carlo ≤ 0,025).
- **Tính hợp lệ:** tỉ lệ admit ở δ ≤ 0 là 0–0,0025, không vượt α_ô.

Xác suất admit theo số trial mới (chi phí ≈ 0,13 USD mỗi trial mới):

| Ô | Trial mới tối đa | δ = 0,05 | δ = 0,109 | δ = 0,15 |
| --- | --- | --- | --- | --- |
| xreposkill (n0 = 109) | khoảng 990 | 100: 0,07; 300: 0,47; 800: 0,85 | **0: 0,10; 100: 0,88; 200: 0,99** | 0: 0,63; 50: 0,97 |
| type-guard (n0 = 53) | 256 | 200: 0,06 | 100: 0,25; 200: 0,70 | 100: 0,63; 200: 0,97 |
| exception-handling (n0 = 53) | 147 | 100: 0,005 | 100: 0,26 | 100: 0,68 |
| null-guard (n0 = 53) | 69 | 50: 0 | 50: 0,04 | 50: 0,21 |

**Giới hạn:** q của các ô E1 chỉ đo trên 37 task. Mô hình hiệu ứng như `docs/method_check.md`.

## 7. Rà soát (R-28, 04/11/2026): vấn đề tiềm ẩn và phương án chưa xét

| # | Điểm | Ảnh hưởng | Xử lý |
| --- | --- | --- | --- |
| 1 | **Số task của các ô E1 bị ước cao (A70).** Bản nháp lấy số task kích hoạt từ `data/activation.json` (gồm cả Live và các bộ khác). Khung thật của E1 là SWE-bench full bỏ repo SWE-Gym: 221 / 118 / 89 task kích hoạt × 94,4% dùng được | Trial mới tối đa: type-guard 156 (không phải 256), exception-handling 58, null-guard 31. Mô phỏng lại: type-guard 0,52 ở δ = 0,109, 0,92 ở δ = 0,15; hai ô kia ≤ 0,33 ở δ = 0,15 | Đã sửa trong `scripts/main_design_sim.py`. **Không chi tiền cho exception-handling và null-guard**: chúng không đạt được admit vì thiếu task, không phải vì thiếu tiền |
| 2 | **Thiếu baseline đã đăng ký cho RQ1:** quy tắc admit của XRepoSkill (`docs/preregistration.md`: "XRepoSkill (+ fingerprint screen)"). Câu gốc: resolution gain có trọng số Mantel–Haenszel, so trong từng issue | Reviewer sẽ hỏi: RQ1 là so với baseline nào? | Áp **đúng** công thức của họ lên cùng các trial, không tốn tiền. Cần đọc đủ quy tắc admit (ngưỡng, kiểm định) từ toàn văn: ⏳ thêm từ khóa nguồn |
| 3 | **Model có thể bị đổi phía Vertex giữa đoạn E1/E2 và đoạn mới.** Khi đó STR không còn cố định, nên nối tiếp không hợp lệ | Có thể làm hỏng giả thiết của Bổ đề E | Kiểm đã đăng ký: trường `model` mà API trả về phải giống nhau ở mọi lời gọi của một ô. Nếu khác thì ô bắt đầu chuỗi mới (không nối tiếp), và báo cáo. Chạy thí nghiệm chính sớm |
| 4 | **Holm từng bước trên p-value anytime-valid** (p_i = min(1, 1/max_t E_i,t)) thay cho Bonferroni α/K | Theo Ville, p_i hợp lệ ở mọi thời điểm dừng. Holm hợp lệ với mọi phụ thuộc, và tập bác bỏ chỉ lớn lên khi p giảm, nên quyết định admit sớm vẫn hợp lệ. **Mạnh hơn hoặc bằng Bonferroni** ở lần admit thứ hai trở đi; lần đầu vẫn ở α/K | Phương án trội: dùng. ⏳ cần câu gốc của Holm (A64) |
| 5 | **Chỉ phân trial mới cho các ô có thể admit** (xreposkill, type-guard). Ô có hại và ô thiếu task không cần trial mới: vế an toàn ("không admit") không cần thêm trial | Tiết kiệm tiền, không làm yếu kết quả | Phương án trội: dùng |
| 6 | **Dùng chung nhánh `none`** khi một task mới được kích hoạt cho nhiều ô | Ít tiền hơn cho mỗi trial. Bất đẳng thức hợp các biến cố không cần độc lập | Phương án trội: dùng (lợi nhỏ, vì chỉ type-guard nhận task mới trên SWE-bench) |
| 7 | **Nhãn "thật" để chấm độ phủ.** Không có ô nào biết trước là có ích | Chưa đo được độ phủ thật | Hai cách: (a) báo cáo ô được admit kèm dãy tin cậy, không gọi là "độ phủ"; (b) thêm **ô đối chứng dương thiết kế sẵn** (skill biết chắc là có ích, ví dụ chỉ ra file cần sửa), giống đối chứng âm là các skill có hại. **[@thuthuy]**: (b) tốn thêm tiền và thêm một ô vào họ giả thuyết |
| 8 | **Máy chạy:** đoạn E1 chạy trên máy cục bộ, đoạn mới có thể chạy trên Actions | Khác biệt về quá giờ khi chấm; hai nhánh của một cặp vẫn chung máy | Ghi thành giới hạn; phân tích độ nhạy theo máy |

**Ngân sách khuyên (sửa từ 60 USD):** xreposkill +200 trial (khoảng 26 USD; 0,99 ở δ = 0,109) và type-guard +156 trial (khoảng 20 USD; 0,52 ở δ = 0,109, 0,92 ở δ = 0,15), tổng **khoảng 46 USD**. Cộng phần đối chứng dương nếu chọn mục 7(b).

## 8. Ô đối chứng dương (@thuthuy chọn phương án 7(b), 04/11/2026)

- **Skill `pc-oracle-files`:** chèn trước đề bài danh sách **các file mà bản vá đúng sửa**. Câu chèn sẽ được đăng ký nguyên văn trước khi chạy.
  - **Cơ sở:** thiết lập "Oracle" retrieval của SWE-bench (Jimenez et al. 2024, `swebench`, Hình 4: tỉ lệ giải khi biết đúng file), và nguyên lý đối chứng gieo sẵn của mutation testing (Jia & Harman, `mutation_survey`: lỗi "deliberately seeded" để đo khả năng phát hiện).
  - **Hướng hiệu ứng được thiết kế là có ích**, nên ô này cho "đáp án đúng" để đo độ phủ. Hiệu ứng thật vẫn được ước lượng và báo cáo kèm dãy tin cậy. Nếu sau khi hết trial ô này không được admit và dãy tin cậy vẫn chứa 0, báo cáo là "đối chứng dương không được xác lập", không kết luận về Gatekeeper.
- **Họ giả thuyết:** K = 8 (7 ô cũ cộng ô này), α_ô = 0,025/8, Holm trên p-value anytime-valid (§7 mục 4).
- **Trial (phương án trội về chi phí):**
  - Đoạn 1: 109 task của E2. Chạy nhánh `pc-oracle-files` với seed 41, ghép với nhánh `none` seed 41 **đã chạy** trong E2. Mỗi trial là 1 lần chạy mới (≈ 0,063 USD), không phải 2. Điều kiện: kiểm tên model trả về (§7 mục 3) và cùng harness, cùng image.
  - Đoạn 2, nếu chưa admit: task Live mới theo `random_order`, 1 seed, dùng chung nhánh `none` với ô xreposkill khi cùng task (§7 mục 6).
- **Số trial tối đa:** 200 (`results/pc_design_sim.json`). Xác suất admit: 0,88 nếu hiệu ứng là 0,15; 0,93 nếu là 0,20 (đạt ở 150 trial); 0,54 nếu là 0,109.
  - Căn cứ: ràng buộc nguồn lực (Lakens 2022), kèm đường cong power theo δ.
  - Chi phí tối đa ≈ 109 × 0,063 + 91 × 0,126 ≈ 18 USD. Ô dừng ngay khi admit, nên chi phí thật có thể thấp hơn.
- **Ngân sách thí nghiệm chính khuyên:** xreposkill 26 + type-guard 20 + đối chứng dương 18 ≈ **64 USD**.

## 9. Cơ sở của phương pháp: câu gốc đã lưu (04/11/2026)

| Thành phần | Nguồn (`sources-snapshots`, sha256) | Câu gốc |
| --- | --- | --- |
| Đối chứng có hiệu ứng biết trước | `franklin_2014_plasmode` (95f05f73) | "A plasmode is a real dataset … has some aspect of the data-generating model known, for example, a 'spike-in' experiment … where a known amount of genome transcript is added to each sample." |
| | `mutation_survey` (056ac9b9) | "Such faults are deliberately seeded into the original program … To assess the quality of a given test set, these mutants are executed against the input test set." |
| Gợi ý đúng file | `swebench` (f7e8e1df) | "'Oracle' retrieval. For analysis purposes we also consider a setting where we 'retrieve' the files edited by the reference patch that solved the issue on GitHub. This 'oracle' setting is less realistic …". Bài gốc tự gọi thiết lập này là kém thực tế, nên ở đây nó chỉ là **đối chứng**, không phải skill |
| Ville | `ville_inequality` (19dfc4e9) | "any gambler's wealth is a nonnegative supermartingale"; "P(sup_t M_t ≥ α) ≤ 1/α" |
| Nối tiếp, dừng tùy ý | `ville_inequality` | "optional stopping or continuation for any reason" |
| Holm | `holm`: Shaffer 1986 (ac9312c7) | "Holm (1979) introduced a modified Bonferroni procedure with greater power than the B procedure …" |
| Superpopulation | `miller_2024` (22570aaf) | "sampling questions from the super-population" |
| Tổng biến phân | `levin_peres_2017` (9ef39f94) | Proposition 4.5 |

**Không có nguồn (nêu rõ):**
- Ghép với nhánh `none` đã chạy của E2 là **giả định** model và harness không đổi; được kiểm bằng `response.model`.
- Câu chèn vào đề bài là **định nghĩa can thiệp** (R2); được đăng ký nguyên văn.

## 10. Kiểm giả định "model không đổi" trước khi ghép với nhánh `none` của E2 (đăng ký trước)

- **Cơ sở:**
  - A/A test kiểm chính hệ thống đo (Kohavi et al. 2020, `kohavi_aa`).
  - Tính tất định theo seed của Vertex, đã đo ngày 02/11 (`configs/models/vertex_gemini.json`: hai lời gọi seed 1 cho cùng kết quả).
- **Bước 1, tính tất định:** với mỗi task trong 109 task E2, gửi **lời gọi đầu tiên** của agent (đúng system prompt và đề bài như trajectory E2, seed 41) **hai lần**.
- **Bước 2, có đổi không:** so câu trả lời mới với câu trả lời đầu tiên trong trajectory E2 seed 41. Đồng thời, trường `model` trả về phải trùng.
- **Quy tắc:**
  - Chỉ ghép khi bước 1 cho hai câu trả lời giống hệt **và** bước 2 khớp, trên **mọi** task.
  - Nếu có bất kỳ khác biệt nào, không ghép: ô đối chứng dương chạy cả hai nhánh mới (2 lần chạy cho mỗi trial).
  - Báo động nhầm chỉ làm tăng chi phí, không ảnh hưởng tính hợp lệ.
- **Chi phí:** dưới khoảng 0,5 USD (327 lời gọi đầu, mỗi lời gọi vài nghìn token), tính vào ngân sách thí nghiệm chính.

## 11. Baseline XRepoSkill cho RQ1 (đọc từ mã đã ghim `26fd703`, 04/11/2026)

- **XRepoSkill không có bước admit.** `src/xreposkill/score.py`, nguyên văn: "the gain is the Mantel-Haenszel risk difference across issues, with Sato's variance. The z score is gain / standard error. Scoring never removes a rule: a rule without a usable predicate or without a usable issue stratum gets a 'fallback' record and is ordered by support later." Thống kê chỉ dùng để xếp thứ tự và gắn nhãn bằng chứng cho LLM khi chọn rule (`pack.py`: `evidence_tag(support, z)`).
- **Baseline B-X1 (đúng như XRepoSkill):** admit mọi skill mà bước chọn rule kích hoạt trên task. Ở E2: 138/138 task dùng được.
- **Baseline B-X2 (dùng thống kê của XRepoSkill làm cổng; biến thể do ta tạo ra, ghi rõ trong paper):**
  - Mỗi task là một stratum: hai nhánh, mỗi nhánh một lần chạy với cùng seed.
  - Tính đúng hàm `mh_risk_difference` của họ (Mantel–Haenszel, phương sai Sato), chép từ mã đã ghim và có test so với mã gốc.
  - Admit khi `ci_low` = rd − 1,959964·se > 0. Đây là hằng số `Z95` của họ, áp **một lần** khi hết ngân sách của ô, không hiệu chỉnh cho nhiều ô, giống cách thống kê này được dùng.
  - Với trial là trung bình 3 seed: mỗi seed là một stratum riêng của task. Cần chốt trước khi đăng ký.
- **So sánh:** harmful acceptance và clean-reuse coverage của Gatekeeper, B-X1, B-X2 và plug-in, trên cùng trial của 8 ô. Mọi khác biệt được báo cáo cùng tỉ lệ admit nhầm mong đợi (từ mô phỏng) của từng quy tắc.
- **Căn cứ trong bài gốc (đã lưu, `xreposkill`, arXiv 2609.36807):** "The gain and z score are not used as thresholds for retaining rules; instead, they inform issue-adaptive rule selection in Stage 3." Bộ lọc giữ rule duy nhất của họ là lặp lại qua nhiều repo: "retains only behaviors recurring across repositories as transferable rules" (không phải kiểm định thống kê).
- **Khoảng trống so với `docs/preregistration.md` §5 (04/11/2026, chờ @thuthuy, quyền mục 2):** bản đăng ký gốc ghi MemGovern và gskill (GEPA) là "baseline có code ✅" và ghi RQ1 là so với "XRepoSkill (+ fingerprint screen)". Bản nháp này chưa có hai baseline đó. Bỏ chúng là Sai lệch D# (R5), phải ghi và báo cáo. Cơ chế giữ skill của gskill (bộ chọn ứng viên của GEPA) chưa có câu gốc đã lưu: ⏳ thêm nguồn trước khi dùng làm baseline cổng. Nối lại "fingerprint screen" với B-X1/B-X2: việc kỹ thuật, tự làm trước khi đăng ký.

### 11b. Giải quyết khoảng trống baseline (@thuthuy: "Chọn phương án có lợi cho research", 04/11/2026)

- **B-G (cổng của gskill/GEPA): thêm vào RQ1, không tốn tiền, phương án trội.** Mã đã ghim `gepa-ai/gepa@8c7b697` (MIT): `StrictImprovementAcceptance`, "Accept only if the sum of new subsample scores is strictly greater than the old sum. This is the default acceptance criterion used by GEPA." `core/engine.py`: `acceptance_criterion or StrictImprovementAcceptance()`. gskill không đổi tiêu chí này và đặt `reflection_minibatch_size=3` (`gskill/train_optimize_anything.py`). Áp vào cùng trial: admit ô khi tổng Z của 3 trial đầu > 0 (B-G3, đúng cỡ của gskill); biến thể B-Gall: tổng Z trên toàn bộ trial của ô > 0. Câu "Accept only if … default acceptance criterion used by GEPA" đã có trong snapshot `gepa_acceptance` (04/11); hai câu còn lại ở `gepa_engine_default`, `gskill_train_config`.
- **gskill làm nguồn skill: không chạy, ghi Sai lệch D# khi đăng ký.** Lý do: skill của gskill được học riêng cho từng repo (blog: Jinja, Bleve), cần task SWE-smith của repo đó và mặc định `max_metric_calls=600` lần chạy để học. Ước tính 600 × 0,064 ≈ 38 USD mỗi repo, chưa tính trial. Phần cổng của gskill đã được kiểm bằng B-G.
- **MemGovern làm nguồn skill (một ô mới): cần ngân sách mới [@thuthuy].** Dữ liệu thẻ kinh nghiệm đã công bố (Git LFS, 158.201.317 byte, `a845658`), nên không tốn tiền học. Không có file LICENSE (chỉ có badge MIT trong README): xử lý như XRepoSkill, không phân phối lại nội dung. Chạy trên SWE-agent; ta chỉ viết adapter đưa thẻ truy xuất được vào hướng dẫn, không đổi harness. Ước tính khoảng 200 trial × 0,13 ≈ 26 USD, chưa đo (prompt dài hơn), sẽ đo khi chạy thử miễn phí.

### 11c. Thay thế MemGovern (04/11/2026)

| Phương án | Chi phí | Căn cứ đã kiểm | Hạn chế |
| --- | --- | --- | --- |
| **(1) Dữ liệu đã công bố của SWE-Skills-Bench** (`ControllableModel/SWE-Skills-Bench@4d3450d`, MIT; `data/external/swe-skills-bench/`): 98 skill công khai × 10 requirement × 4 cấu hình agent–model = 3.920 cặp có/không skill, 0 ô thiếu | 0 USD | Bài gốc: "We start from 98 public SWE skills, each paired with a real GitHub repository pinned at a fixed commit"; XRepoSkill dẫn lại: "most public software engineering skills provide little or no improvement … and some can even hurt" | Chỉ là phân tích **thăm dò** (dữ liệu đã xem ở pilot, R5; `SOURCE.md`: không phải benchmark, R13). Mỗi ô có 10 trial: Gatekeeper không thể admit (đã đo: cần 9–23 trial ngay cả với skill hoàn hảo), nên chỉ kiểm được vế an toàn và hành vi của các cổng ngây thơ. Nhãn từ một nửa dữ liệu là nhiễu (A23), nên dùng thiết kế sàng lọc rồi xác nhận |
| (2) Chạy skill của SWE-Skills-Bench trên harness của ta | ≈ 1.960 lần chạy × 0,064 ≈ 125 USD | README: agent là Claude Code CLI hoặc Codex CLI, không phải mini-swe-agent | Phải đổi harness; vẫn chỉ 10 task mỗi skill |
| (3) Skill đã học sẵn của gskill | — | Repo `gepa@8c7b697` không có file skill (thư mục `gskill/assets` chỉ có `architecture.png`) | Phải tự học: ≈ 38 USD mỗi repo, cần task SWE-smith |
| (4) Không có nguồn thứ hai | 0 USD | — | Ghi vào phần giới hạn |

Phương án (1) là phương án trội về chi phí: tự làm, đăng ký trước cách phân tích. Áp 5 quy tắc (Gatekeeper, B-X1, B-X2, B-G3, plug-in) lên 392 ô. Bỏ MemGovern là Sai lệch D# so với `docs/preregistration.md` §5, chờ @thuthuy xác nhận.

### 11d. MemGovern dạng truy xuất cố định (B-M), phương án xác định được (04/11/2026)

Đã kiểm (miễn phí):
- Dữ liệu: `experience_data.json` tải qua LFS, sha256 `c5bcc6e2…f4ea` khớp con trỏ LFS ở `a845658`. 121.475 thẻ, 48 repo. Trường: `repo`, `issue_id`, `bug_description`, `fix_experience`, `content_preview`. **Không có ngày**, nên không cắt theo thời gian được.
- Truy xuất của họ: model embedding `Qwen3-Embedding-0.6B` (SentenceTransformer, chạy CPU), `/search` mặc định `top_k` 5 (`tools/experience_server.py`). Agent tự gọi `exp_search`/`exp_read` nhiều lần (`config/dsv31t_agenticMemSearch_1220_13w.yaml`). Câu gốc: snapshot `memgovern_server`, `memgovern_search_tool`.
- Thẻ được viết để dùng **khác repo**: "Help retrieve semantically similar issues across different repositories" (`scripts/experience_process.py`, snapshot `memgovern_cards`).

Thiết kế B-M:
- Truy xuất **một lần cho mỗi task, ngoài vòng chạy**: truy vấn là nội dung issue, `top_k` = 5, dùng đúng model embedding và chỉ mục ChromaDB của họ. Ghép `bug_description` và `fix_experience` của 5 thẻ vào đầu prompt, cùng adapter với XRepoSkill.
- **Loại mọi thẻ cùng repo với task.** Lý do: chống rò rỉ đáp án khi không có ngày; thẻ vốn được thiết kế để dùng khác repo.
- Khác bản gốc: không có tìm kiếm lặp do agent tự gọi. Đây là biến thể, ghi rõ trong paper.
- Tính truy xuất trên GitHub Actions (miễn phí): chỉ mục 220 + 515 MB và model, vì đĩa máy chạy E1 chỉ còn 4,7 GB.

Thiết kế ô:
- Pool SWE-bench-Live của E2 (các repo của SWE-bench đã bị loại).
- **Dùng chung nhánh `none`**: 109 task của E2 (đã có 3 seed) cộng các task mới của ô xreposkill ở thí nghiệm chính. Ô B-M chỉ cần chạy nhánh có thẻ, tức 1 lần chạy mỗi trial, khoảng 0,064 USD.
- FWER vẫn được giữ dù các ô tương quan, vì Holm đúng với mọi dạng phụ thuộc (Shaffer 1986, đã lưu).
- ⏳ Cần nguồn cho thiết kế nhiều nhánh dùng chung nhóm đối chứng.

Chi phí: khoảng (109 + 200) × 0,064 ≈ 20 USD, chưa tính phần prompt dài hơn (đo khi chạy thử miễn phí). Cần ngân sách mới [@thuthuy].

### 11e. Quyết định của @thuthuy và trình tự thử (04/11/2026)

> "Lúc thử thì thử phương án B-M, khả thi thì thử bản Megovern gốc chứ không dùng bản biến thể. Cho phép ngân sách"

- **Ngân sách:** 20 USD cho ô MemGovern, ghi trong `CLAUDE.md`. Đây là số tôi đề xuất ở §11d. Chạm mức thì dừng và chờ @thuthuy.
- **"Bản gốc" trong thiết kế ghép cặp (tự quyết, phương án trội):** dùng đúng thẻ, model embedding, mã server tìm kiếm, công cụ `exp_search`/`exp_read` và đoạn hướng dẫn trong cấu hình agent của MemGovern, cài vào container của mini-swe-agent. Agent tự gọi công cụ, lặp nhiều lần như bản gốc. Không chạy SWE-agent, vì làm vậy cần một nhánh `none` mới bằng SWE-agent: chi phí gấp đôi, khác harness với mọi ô khác, và mất nhánh `none` dùng chung. Thay đổi duy nhất so với mã của họ: server bỏ thẻ cùng repo với task (chống rò rỉ, §11d) nhưng vẫn trả đủ `top_k`.
- **T1, B-M (miễn phí, GitHub Actions):**
  - (F1) mỗi task trong 109 task E2 và 200 task kế tiếp nhận đủ 5 thẻ, mọi thẻ khác repo với task;
  - (F2) chạy thử bằng model giả lập trên ≥ 1 task Live thật: hoàn tất, `infra_failures` = 0.
- **T2, bản gốc (miễn phí, GitHub Actions):**
  - (F3) server khởi động trong job, `/health` trả lời;
  - (F4) bên trong container của task, model giả lập gọi `exp_search` nhận ≥ 1 kết quả, rồi `exp_read` nhận được nội dung thẻ, trên ≥ 1 task thật;
  - (F5) có test chứng minh thẻ cùng repo bị loại;
  - (F6) chạy thử hoàn tất với `infra_failures` = 0.
- **Quy tắc chọn:** đạt đủ F3–F6 thì ô có chi phí dùng bản gốc. Thiếu bất kỳ mục nào thì dùng B-M, ghi rõ mục nào không đạt và vì sao.
- **Khi chạy có chi phí:** sổ chi chung (như E2) với trần 20 USD. Sau 10 trial đầu, nếu chi phí dự kiến cho cả ô vượt 20 USD thì dừng và hỏi @thuthuy.
