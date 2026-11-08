# Đăng ký trước: thí nghiệm chính (RQ1, Gatekeeper)

> **Trạng thái:** ĐĂNG KÝ CHÍNH THỨC, commit ngày 04/11/2026, **trước khi** phân tích E1 và E2 (L27).
> - Nguồn chi tiết và lý do của từng mục: `docs/preregistration_main_draft.md` §1–11e. Bản này là bản tóm tắt ràng buộc; nếu hai bản khác nhau thì bản này thắng.
> - Đã xem kết quả của E1/E2 trước khi đăng ký: chỉ tỉ lệ giải gộp theo nhánh (A66), và q của nhánh `none` dùng làm đầu vào mô phỏng (tham số nền, không vi phạm R5).

## 1. Câu hỏi

Với mỗi ô (skill, scope) trong họ K = 9 ô dưới đây:
- **(a) An toàn:** Gatekeeper không admit ô có hại hoặc trung tính, với FWER ≤ 0,025 (một phía).
- **(b) Độ phủ:** Gatekeeper admit ô đối chứng dương (biết trước là có ích) với số trial khả thi.
- **So sánh:** cùng các trial được đưa qua 5 quy tắc khác (§6).

## 2. Tham số cố định

| Mục | Giá trị | Căn cứ |
| --- | --- | --- |
| θ | 0 | Sai lệch D2; draft §2 |
| α họ | 0,025, một phía | ICH E9 (`ich_e9`) |
| K, α_ô | K = 9; ngưỡng admit sớm α_ô = 0,025/9 | Bonferroni; draft §8, §11e |
| Quyết định cuối | Holm từng bước trên p_i = min(1, 1/max_t E_i,t) ở mức 0,025 | Ville (`ville_inequality`); Holm (`holm`, Shaffer 1986) |
| e-process | aGRAPA, c = 0,5 (`gatekeeper.eprocess`) | Waudby-Smith & Ramdas; `results/gro_c.json` |
| Trial | Z = loss(có skill) − loss(không skill) của một task; trung bình qua seed nếu task có nhiều seed | Giả định SP (`docs/theory/proofs.md` §0) |
| Nối tiếp | Trial E1/E2 là đoạn đầu của chuỗi ô tương ứng, theo thứ tự ngẫu nhiên đã cố định | "optional stopping or continuation for any reason" |
| Task mới | Theo `random_order` của pool, sau các task đã dùng; mỗi task một lần; **1 seed (41)** | Phương án trội: nhiễu trong task đã đo ở E1/E2 với 3 seed |
| Dừng | Mỗi ô dừng khi admit (E ≥ 1/α_ô) hoặc khi hết số trial tối đa của ô | Ville |

## 3. Các ô và số trial

| Ô | Đoạn đầu (n0) | Trial mới tối đa | Nhánh chạy mới mỗi trial |
| --- | --- | --- | --- |
| xreposkill (E2) | 109 task × 3 seed | 200 task Live mới (pool `e2`, khối `e2c`) | 2 (`none` dùng chung với các ô Live khác) |
| pc-oracle-files (đối chứng dương) | — | 200: trước hết 109 task E2 (ghép với `none` seed 41 của E2, nếu §5 đạt), sau đó task Live mới | 1 |
| memgovern | — | 109 task E2 (như trên) rồi task Live mới, tới hết 20 USD | 1 |
| type-guard (E1) | 53 | 156 task SWE-bench mới | 2 |
| exception-handling, null-guard (E1) | 53 | 0 (thiếu task, draft §7 mục 1) | — |
| 3 skill có hại (E1) | như E1 | 0 (vế an toàn không cần trial mới) | — |

- **Ô memgovern:** dùng **bản gốc** (agent tự gọi `exp_search`/`exp_read`, draft §11e) nếu F3–F6 đạt trong lần chạy thử miễn phí. Nếu thiếu mục nào thì dùng B-M (`configs/skills/memgovern-bm.json`), ghi rõ mục không đạt.
- **Mô phỏng thiết kế với K = 9** (`results/main_design_sim.json`, 400 lần lặp mỗi điểm):
  - Tỉ lệ admit ở δ = 0 là 0 cho mọi ô, không vượt α_ô.
  - xreposkill với +200 trial: 0,99 ở δ = 0,109.
  - type-guard với +156 trial: 0,48 ở δ = 0,109 và 0,88 ở δ = 0,15.
  - exception-handling và null-guard: ≤ 0,27 ở δ = 0,15, nên không có trial mới.
- **Dùng chung nhánh `none`** trên cùng task Live: hợp lệ vì Holm đúng với mọi phụ thuộc giữa các ô.

## 4. Ngân sách và thứ tự chạy

- **Ngân sách:** thí nghiệm chính 64 USD, ô MemGovern 20 USD (`CLAUDE.md`). **Trước 01:00 UTC 05/11 tổng chi mới ≤ 50 USD.**
- **Bộ chặn:** sổ chi chung kiểu E2. Đặt trước trường hợp xấu nhất của mỗi lần gọi, rồi ghi số chi thật.
- **Thứ tự:**
  1. Kiểm "model không đổi" (§5).
  2. pc-oracle-files và memgovern trên 109 task E2.
  3. Task Live mới: `none` + xreposkill + pc (nếu chưa admit) + memgovern (nếu chưa admit và còn ngân sách).
  4. type-guard trên SWE-bench.
- **Kiểm chi phí của memgovern:** sau 10 trial đầu, nếu chi phí dự kiến cho cả ô vượt 20 USD thì dừng ô này.

## 5. Kiểm "model không đổi" (trước khi ghép với nhánh `none` của E2)

Như draft §10.
- Gửi lời gọi đầu tiên của agent cho mỗi task E2, seed 41, **hai lần**.
- Chỉ ghép khi mọi cặp câu trả lời giống hệt nhau, giống câu trả lời trong trajectory E2, và trường `model` trùng nhau.
- Nếu không: các ô pc và memgovern chạy cả hai nhánh mới (2 lần chạy mỗi trial).

## 6. Phân tích (mã đã khóa: `scripts/gates.py`, `scripts/rq1_mini.py`, `scripts/analyze_g1_final.py`)

- **Các quy tắc so sánh**, trên cùng trial của mỗi ô:
  - **Gatekeeper:** p anytime-valid + Holm;
  - **plug-in:** admit khi trung bình Z < 0;
  - **B-X1:** admit mọi skill (XRepoSkill không có cổng);
  - **B-X2:** `mh_risk_difference` của XRepoSkill (import từ mã ghim `26fd703`), admit khi rd − Z95·se > 0, áp một lần khi hết trial;
  - **B-G3 / B-Gall:** tiêu chí của GEPA, tổng Z < 0 trên 3 trial đầu hoặc trên mọi trial.
- **Kết quả báo cáo:**
  - quyết định admit và số trial dùng;
  - với 3 ô có hại (biết trước là có hại): tỉ lệ admit nhầm của từng quy tắc;
  - với ô đối chứng dương: admit hay không, và số trial tới lúc admit;
  - với các ô khác: quyết định kèm dãy tin cậy, **không** gọi là "độ phủ";
  - chi phí tính bằng token (input, cache, output).
- **Độ nhạy:**
  - S-infra: lỗi hạ tầng là dữ liệu thiếu (ICH E9(R1));
  - bỏ các trial có test quá giờ khi chấm;
  - theo máy chạy (cục bộ hay Actions).
- **E1, E2:** phân tích đúng theo bản đăng ký của từng giai đoạn (`docs/preregistration_e1.md`, `_e2.md`), chạy **sau** khi bản này được commit.

## 7. Sai lệch so với `docs/preregistration.md` §5 (ghi trước khi phân tích)

| # | Sai lệch | Lý do |
| --- | --- | --- |
| D-M1 | gskill chỉ dùng làm quy tắc cổng (B-G), không làm nguồn skill | Skill phải học riêng cho từng repo, khoảng 38 USD mỗi repo (draft §11b) |
| D-M2 | MemGovern chạy trên mini-swe-agent bằng công cụ và server của chính họ, thay vì SWE-agent; bỏ thẻ của các repo thuộc ô | Giữ ghép cặp với nhánh `none` chung; chống rò rỉ đáp án (draft §11e) |
| D-M3 | K = 9 (thêm đối chứng dương và memgovern) | Quyết định của @thuthuy ngày 04/11 |
| D-M4 | Không chạy B8, B9, ASI ở thí nghiệm chính | Chúng phục vụ câu hỏi về chi phí (RQ4), không thuộc RQ1 |

## 8. Phân tích plasmode trên dữ liệu thật của E1/E2 (đăng ký 05/11/2026, trước khi chạy; 0 USD)

- **Cơ sở:** plasmode là "a real dataset … has some aspect of the data-generating model known … 'spike-in'" (`franklin_2014_plasmode`). Ở đây phần biết trước là hiệu ứng δ được cấy vào.
- **Nền có hiệu ứng thật bằng 0 chính xác:** với mỗi task có ≥ 2 lần chạy **không skill** (E1, phần mở rộng E1 và E2, 3 seed), ghép hai lần chạy khác seed thành một cặp A/A: một lần đóng vai "có skill", lần kia làm đối chứng. Hai lần chạy cùng nhánh nên STR = 0 đúng theo định nghĩa (hoán đổi được); nhiễu và độ khác nhau giữa các task là nhiễu thật.
- **Cấy hiệu ứng:**
  - Có ích: mỗi lần chạy "có skill" chưa giải được thì được đổi thành giải được với xác suất π.
  - Có hại: mỗi lần chạy "có skill" đã giải được thì đổi thành không giải được với xác suất π.
  - δ đúng của ô bằng π nhân trung bình phần có thể đổi trên pool, tính chính xác.
- **Một lần lặp:** một họ K = 9 ô, gồm 3 ô có hại (δ = −0,05; −0,10; −0,20), 3 ô trung tính (δ = 0) và 3 ô có ích (δ = +0,10; +0,20; +0,30). Mỗi ô rút n task có hoàn lại từ pool (giả định SP), n ∈ {25; 50; 109; 200}. Chạy 1.000 lần lặp, seed của bộ sinh số 20271105.
- **Quy tắc so sánh** (`scripts/gates.py`): Gatekeeper (α_ô = 0,025/9, Holm trên p anytime-valid ở mức 0,025), plug-in, B-X1, B-X2, B-G3, B-Gall.
- **Đại lượng báo cáo:**
  - tỉ lệ admit nhầm = số ô có hại hoặc trung tính được admit / 6;
  - độ phủ = số ô có ích được admit / 3;
  - FWER = tỉ lệ lần lặp có ít nhất 1 ô có hại hoặc trung tính được admit;
  - mỗi đại lượng kèm sai số Monte Carlo.
- **Độ nhạy:** π khác nhau giữa các task (π_i ~ Beta với cùng trung bình, độ tập trung 2), để mô phỏng hiệu ứng không đều.
- **Giới hạn ghi sẵn:** cơ chế hiệu ứng được cấy là đổi kết quả ngẫu nhiên; skill thật có thể tác động theo cách khác. Phân tích này bổ sung, không thay thế, kết quả trên các ô thật (E1/E2: 0/7 ô được Gatekeeper admit).

## 9. Ba phân tích bổ sung, 0 USD (đăng ký 05/11/2026, trước khi chạy)

**P1. Theo dõi liên tục.**
- Dùng cùng các ô plasmode như §8 (cách cấy đều), n tối đa = 200.
- Plug-in, B-X2 và B-Gall được kiểm sau **mỗi 10 trial**, và admit ngay khi tiêu chí đúng ở bất kỳ lần kiểm nào. B-G3 chỉ dùng 3 trial đầu, nên không đổi.
- Gatekeeper giữ nguyên, vì p anytime-valid đã là cực tiểu trên toàn đường đi.
- Báo cáo FWER và độ phủ. 1.000 lần lặp, seed 20271105.

**P2. Plasmode hỗn hợp thực tế.**
- δ của mỗi ô được rút từ N(μ, τ²), với μ và τ² ước lượng bằng DerSimonian–Laird (`veroniki_2016`) trên 392 ô của SWE-Skills-Bench. Mỗi ô dùng 10 yêu cầu; hiệu ứng = −(none − one)/100.
- δ được cấy vào nền A/A như §8, đổi dấu thành "tỉ lệ giải tăng" (δ > 0 là có ích); giữ δ trong khoảng sao cho π ≤ 1.
- K = 9 ô mỗi lần lặp, n ∈ {109; 200}, 1.000 lần lặp.
- Báo cáo trên 100 ô:
  - số ô có δ ≤ 0 bị admit;
  - số ô có δ > 0 được admit;
  - δ trung bình của các ô được admit.
- **Giới hạn:** SWE-Skills-Bench đo tỉ lệ test qua, không đo "resolved"; thang đo khác nhau.

**P3. Lặp lại trên dữ liệu SWE-Skills-Bench** (`ControllableModel/SWE-Skills-Bench@4d3450d`, MIT).
- 392 ô (cấu hình × skill). Trial = một yêu cầu, Z = (none − one)/100, nằm trong [−1, 1].
- **Sàng lọc** trên yêu cầu batch1–5, **xác nhận** trên batch6–10, tức tách dữ liệu (`rinaldo_splitting`).
- Các quy tắc chỉ thấy phần sàng lọc:
  - Gatekeeper: Holm trên 392 ô ở mức 0,025, trial tối đa 5;
  - plug-in;
  - B-G3;
  - B-Gall;
  - B-X1.
- Báo cáo: số ô được admit; Z̄ trên phần xác nhận của các ô được admit, kèm CI bootstrap 95% (2.000 lần lặp); số ô được admit có Z̄ xác nhận > 0 (tức có hại trên phần xác nhận).
- B-X2 không áp được, vì kết quả là tỉ lệ liên tục chứ không phải nhị phân.
- Đây là phân tích **thăm dò**: dữ liệu đã được xem ở pilot.

**Ghi chú thực thi 1 (05/11/2026; sửa lời ghi: cách ước lượng được chọn khi viết mã, trước khi chạy, nhưng chỉ được **ghi lại sau khi** đã chạy và thấy kết quả P2):** §9 P2 ghi "DerSimonian–Laird". Trọng số 1/v của DL không xác định ở các ô có phương sai trong ô bằng 0; nhiều ô của SWE-Skills-Bench có mọi Δ = 0. Vì vậy dùng ước lượng moment trọng số đều cùng họ (Veroniki et al. 2016): τ² = Var(ȳ_i) − trung bình(s_i²/m_i). Kết quả: μ = −0,0034 trên thang Z, tức tỉ lệ qua tăng 0,0034; τ = 0,0316.

## 10. Kiểm định lặp lại tuyên bố đã công bố của XRepoSkill (05/11/2026; **phân tích thêm sau khi đã có kết quả E2**, ghi rõ trong paper)

- **Tuyên bố gốc** (`xreposkill`, arXiv 2609.36807):
  - "XRepoSkill improves issue resolution by 10.3 percentage points over the same agent without learned skills" (DeepSWE);
  - "strong transfer to previously unseen repositories".
- **Phép kiểm:** kiểm tương đương một phía, bác bỏ một hiệu ứng tối thiểu đáng quan tâm (SESOI) (`lakens_2018_tost`: "reject the presence of a smallest effect size of interest (SESOI)").
  - SESOI = 0,103, chính con số họ công bố.
  - H0: mức tăng tỉ lệ giải ≥ 0,103.
  - Kiểm đổi dấu chính xác trên 109 task E2 (Z̄ của 3 seed), 200.000 lần đổi dấu, seed 20271105.
- **Kết quả:** Z̄ = −0,0214, tức mức tăng tỉ lệ giải 0,021, CI 95% [−0,010; +0,053]; p < 5·10⁻⁶. Bác bỏ H0.
- **Phạm vi kết luận:**
  - Áp cho SWE-bench-Live (repo không có trong pool học của họ), một model (Gemini 3.1 Flash-Lite), mini-swe-agent, bộ skill đã công bố và bước chọn rule của chính họ.
  - Không bác bỏ kết quả của họ trên DeepSWE với các model của họ.
  - Theo câu gốc của Lakens: "when a meaningful effect can be rejected, it does not imply there is no effect at all".
- **Quy tắc chọn SESOI công bằng (ghi 05/11/2026, trước khi đọc bảng kết quả đầy đủ của XRepoSkill):** 10,3 điểm là con số **lớn nhất** họ nêu (DeepSWE), nên dùng một mình nó là chọn lọc có lợi cho mình. Quy tắc thay thế:
  - Lấy **mọi** mức tăng so với "cùng agent không có skill" trong bảng kết quả của họ (6 tổ hợp benchmark × LLM).
  - Báo cáo phép kiểm cho từng mức tăng. Kết luận chính dùng mức tăng **nhỏ nhất**.
  - Nếu mức nhỏ nhất ≤ 0,053 (cận trên CI của E2) thì ghi rõ là không bác bỏ được mức đó.
- **Kết quả theo quy tắc công bằng** (05/11/2026; `results/xreposkill_replication.json`; mức tăng lấy từ Table 1 của họ, câu gốc trong snapshot `xreposkill`):
  - **Kết luận chính** (mức tăng nhỏ nhất, SWE-bench Pro/DeepSeek, +4,0 điểm): **không bác bỏ được**, p = 0,12 (theo cụm repo: 0,093).
  - Sau Holm ở mức 0,025 trên 6 tổ hợp, **4/6 bị bác bỏ**: DeepSWE/DeepSeek +12,4; DeepSWE/GPT +12,4; Pro/MiMo +8,5; DeepSWE/MiMo +6,2 (mọi p ≤ 0,0052).
  - Pro/GPT +5,5: p = 0,017, không qua mức Holm 0,0125.
  - Kết luận đúng: trên thiết lập này, mức tăng của XRepoSkill **nhỏ hơn 4/6 mức họ công bố**, và không loại trừ được các mức tăng từ khoảng 4–5,5 điểm trở xuống.

## 11. Sai lệch D-M5: ô đối chứng dương chạy 3 seed (@thuthuy chọn 05/11/2026: "chọn phương án xác suất cao nhất và mang lại lợi thế mạnh nhất cho paper"; ghi trước khi chạy)

- **Thay cho §3 (1 seed):** nhánh `pc-oracle-files` chạy seed 41, 51 và 61 trên **109 task E2**. Mỗi seed ghép với nhánh `none` cùng seed đã chạy ở E2. Trial = Z̄ của 3 seed của một task, như E1/E2.
- **Lý do:** mô phỏng trên q đo được (05/11): P(admit) là 0,97 ở δ = 0,20 và 0,55 ở δ = 0,15, so với 0,67 và 0,27 khi dùng 1 seed. Giới hạn trên ước được của δ là 0,235 (`docs/preregistration_main.md` §9 bên dưới).
- **Ngân sách:** trần cứng 21,5 USD, gồm phép kiểm "model không đổi" (§5) và 327 lần chạy. Mức này nằm trong 64 USD đã duyệt.
- **§5 mở rộng cho 3 seed:**
  - Gửi lại lời gọi đầu tiên của agent cho từng (task, seed) của E2.
  - Chỉ ghép những seed mà **mọi** task của seed đó cho câu trả lời giống hệt và trường `model` trùng.
  - Seed không đạt thì **không** chạy nhánh pc cho seed đó, và giảm số seed của ô.
- **Quyết định:** Gatekeeper với α_ô = 0,025/9, Holm trên p anytime-valid ở mức 0,025 trong họ K = 9 ô, theo thứ tự task đã cố định của E2. Ô dừng ngay khi admit; khi đó các task còn lại không được chạy.
- **Không thêm trial nào ngoài 109 task này.** Không admit được thì báo cáo "đối chứng dương không được xác lập với 109 task" và dừng chi.

## 12. Mức nhiễu nền khi đánh giá coding agent, và đối chiếu các mức tăng đã công bố (đăng ký 05/11/2026, trước khi đối chiếu)

- **Đã biết trước khi đăng ký:** độ chênh tỉ lệ giải giữa các seed của cùng một nhánh trong E1/E2 (đã tính ở bước khảo sát): tối đa 6,4 điểm trên 109 task (E2, nhánh `none`) và 7,6 điểm trên 144 task (E1, nhánh `none`). Chưa đối chiếu với bất kỳ tuyên bố nào.
- **Phân phối nhiễu A/A:** với mỗi n trong các bài được đối chiếu:
  - lấy 2 seed khác nhau của **nhánh `none`** (E1 và E2 gộp lại; một task chỉ dùng khi có đủ 2 lần chạy);
  - rút n task có hoàn lại;
  - tính hiệu tỉ lệ giải giữa hai seed;
  - 20.000 lần lặp, seed 20271105.
  - "Ngưỡng nhiễu" F(n) = phân vị 97,5% của |hiệu|. Đây là mức chênh mà **chỉ việc chạy lại** đã tạo ra với xác suất 5%.
- **Quy tắc đối chiếu:** một mức tăng đã công bố, đo bằng 1 lần chạy mỗi cấu hình trên n task, được tính là **phân biệt được với nhiễu chạy lại** khi lớn hơn F(n).
- **Tuyên bố được đối chiếu** (lấy toàn bộ, không chọn lọc):
  - XRepoSkill Table 1, 6 tổ hợp: SWE-bench Pro n = 200, theo tổng số task ở Table 2 của họ; DeepSWE n = 113, theo câu "We evaluate on all 113 tasks";
  - MemGovern README, 7 model: SWE-bench Verified n = 500.
- **Bằng chứng thứ hai, lấy từ chính bài XRepoSkill:** Pass@4 89,4% và All@4 32,7%. Như vậy 56,7% số task cho kết quả khác nhau giữa 4 lần chạy của chính họ.
- **Giới hạn ghi sẵn:**
  - Nhiễu đo trên một model với tỉ lệ giải nền 0,27–0,47. Phương sai nhị thức lớn nhất ở tỉ lệ 0,5, mà các bài kia có tỉ lệ nền 0,12–0,69. Do đó F(n) của mình có thể **thấp hơn** nhiễu thật của họ, nghĩa là quy tắc này **có lợi cho các tuyên bố**.
  - Không biết họ có cố định seed hay không.

## 13. Phân tích con của P1, chỉ trên ô trung tính thật (05/11/2026; **phân tích thêm sau khi chạy P1**, ghi rõ trong paper)

- **Thiết lập:** một ô, mọi trial là cặp A/A thật (hai lần chạy không skill của cùng task), nên hiệu ứng thật bằng 0 chính xác và **không có hiệu ứng nào được cấy**. n = 200, nhìn sau mỗi 10 trial, 1.000 lần lặp, seed 20271106.
- **Tỉ lệ admit nhầm:**

  | Quy tắc | Nhìn 1 lần | Nhìn sau mỗi 10 trial |
  | --- | --- | --- |
  | Gatekeeper (α_ô = 0,0028) | — | 0/1.000 |
  | B-X2 | 0,026 ± 0,010 (đúng mức danh nghĩa 0,025) | **0,103 ± 0,019** |
  | Plug-in | 0,44 | 0,80 |

- **Ý nghĩa:** loại được mọi phản biện về hiệu ứng giả lập và về việc thiếu hiệu chỉnh đa giả thuyết. Ở một lần nhìn, B-X2 đúng mức danh nghĩa; chỉ riêng việc theo dõi liên tục đã làm tỉ lệ admit nhầm tăng khoảng 4 lần.
- Kết quả: `results/null_monitoring_real.json`.

## 14. Thí nghiệm chính đã định vị lại: T1–T4 (@thuthuy 05/11/2026: "Làm T1–T4 trước"; đăng ký trước khi viết mã và chạy)

**Bối cảnh:** `docs/novelty_review.md`. Ý tưởng lõi (nhận và thu hồi anytime-valid) đã có ở Qu et al. 2026. Paper so sánh trực tiếp với các quy tắc đã công bố trên nhiễu thật của coding agent.

**Nền chung:** plasmode trên các cặp A/A thật (§8, `plasmode_real.make_cell`, định nghĩa "giải được" là loss = 0); 1.000 lần lặp; seed 20271108; α = 0,025.

**T1. Quy tắc nhận skill**
- **Thiết kế:** K = 9 ô như §8 (3 có hại, 3 trung tính, 3 có ích); n tối đa 200; nhìn sau mỗi 10 trial.
- **Quy tắc so sánh:**
  - Gatekeeper (Holm trên p anytime-valid; FWER);
  - **e-BH** (Wang & Ramdas 2022; Qu et al. dùng dạng online): FDR 0,025 trên e-value cuối của K ô;
  - B-X2 (thống kê của XRepoSkill), cả nhìn 1 lần lẫn nhìn liên tục;
  - B-G3 và B-Gall (GEPA);
  - plug-in;
  - B-X1.
- **Loại trừ có lý do:**
  - HDSO: bản gốc đã lưu không ghi quy tắc nhận thành công thức cụ thể; không tự đoán.
  - EvoUndo: cổng của họ dành cho khả năng hoàn tác của đột biến, không phải tác dụng của skill.
  - Library Drift: không có quy tắc nhận skill.
- **Báo cáo:** FWER, FDR, độ phủ.

**T2. Quy tắc thu hồi**
- **Kịch bản:** một skill có ích (δ = +0,20) được dùng tiếp; tại trial τ_c = 100, hiệu ứng đổi thành −0,20 (ví dụ: repo đổi phiên bản).
- **Hai trường hợp:** (a) dấu vân tay môi trường **có** đổi khi hiệu ứng đổi; (b) dấu vân tay **không** đổi.
- **Quy tắc so sánh:**
  - **Library Drift**, nguyên văn: "retired once n(s) ≥ N_min … and the empirical contribution ĉ(s) ≤ −τ", với N_min = 100 và τ = 0,10; ĉ là hiệu tỉ lệ giải trên toàn bộ trial đã có;
  - **Gatekeeper, thu hồi theo dấu vân tay** (`admission.on_environment_change`);
  - **Gatekeeper cộng theo dõi kết quả:** một e-process một phía cho giả thuyết "có hại", bắt đầu từ lúc skill được nhận, với α_ret = 0,025. Đây là cùng ý tưởng e-detector của Qu et al., không phải đóng góp mới.
- **Báo cáo:**
  - độ trễ phát hiện, tính bằng số trial sau τ_c;
  - tỉ lệ thu hồi nhầm khi hiệu ứng **không** đổi (giữ +0,20 suốt 400 trial).

**T3. Skill ghép**
- **Kịch bản:** hai skill A và B, mỗi skill có ích (δ = +0,20) và đã được nhận. Skill ghép A∘B có tương tác âm, nên hiệu ứng thật là −0,05 (có hại).
- **Quy tắc so sánh:**
  - "nhận skill ghép khi cả hai thành phần đã được nhận";
  - Gatekeeper: skill ghép là một ô riêng, phải có trial riêng (Định lý 4′, giả thiết (iii)).
- **Báo cáo:** tỉ lệ nhận nhầm skill ghép.

**T4. Kiểm chứng trên agent thật**
- **Ô:** `control-oracle-tests` (đối chứng dương đã đạt ở G1). Cả hai nhánh chạy mới trong cùng lô, 1 seed (41), trên task Live theo `random_order` (109 task E2 trước).
- **Quyết định:** Gatekeeper, K = 1, α = 0,025. Dừng ngay khi admit.
- **Trần:** 6 USD (`CLAUDE.md`). Hết trần mà chưa admit thì báo cáo đúng như vậy và dừng.
- **Dự đoán đăng ký trước:** sẽ tính từ hiệu ứng của ô này đo được ở G1, trước khi chạy, và ghi vào đây.

**Sai lệch D-M6 (05/11/2026, trước khi viết mã T4; phương án trội: cùng trần, xác suất cao hơn):**
- **Lý do:** T4 đặt `control-oracle-tests` (hiệu ứng đo được ở G1: −0,158 trên thang resolved, 38 cặp). Với trần 6 USD chỉ chạy được khoảng 40 trial, và mô phỏng (định nghĩa loss = 0, q của E2) cho P(admit) dưới 0,01 ở δ = 0,15. Chạy như vậy là chi tiền cho một thất bại biết trước.
- **Ô thay thế:** `control-oracle-patch`. Chèn **bản vá gốc** (trường `patch` của task; không bao giờ dùng `test_patch`) vào đề bài, ngay sau phần gợi ý của `control-oracle-tests`. Cơ sở: lỗi gieo sẵn ("deliberately seeded", `mutation_survey`) và phương pháp spike-in (`franklin_2014_plasmode`). Đây là **đối chứng**, không phải skill được đánh giá.
- **Cấu hình:**
  - `cost_limit` = 0,5 USD mỗi lần chạy, cho **cả hai** nhánh. Lý do vận hành: bộ chặn cứng của driver (đã chi + trường hợp xấu nhất ≤ trần) phải cho phép đủ trial trong 6 USD. Chi phí trung bình đo ở E2 là 0,063 USD mỗi lần chạy.
  - Lô 1 task; seed 41; `step_limit` 250 như E2.
  - Task theo `random_order` của E2, bắt đầu từ 109 task E2.
- **Dự đoán đăng ký trước** (mô phỏng 05/11, K = 1, α = 0,025, cặp mới, q của E2, 2.000 lần lặp, seed 20271108). Đã sửa trước khi có dữ liệu: bảng ghi lần đầu lấy nhầm số của mô phỏng 60 trial với α = 0,025/9.

  | δ thật | P(admit trong 40 trial) | Trung vị số trial khi admit |
  | --- | --- | --- |
  | 0,7 | 1,00 | 19 |
  | 0,6 | 0,998 | 21 |
  | 0,5 | 0,98 | 25 |
  | 0,4 | 0,835 | 30 |
  | 0,3 | 0,442 | 34 |

- **Kết luận chính:** ô có được admit trong trần 6 USD hay không. Số trial khi admit được so với bảng trên. Hiệu ứng đo được báo cáo kèm CI.

**Ghi chú thực thi T2-1 (05/11/2026; thêm sau khi đã thấy kết quả T2 của 4 quy tắc kia; quy tắc của chúng không đổi):**
- Thêm **e-SR** (Shin, Ramdas & Rinaldo, `e_detectors_2023`, Định nghĩa 2.12: "N*_SR := inf{n ≥ 1 : M^SR_n ≥ 1/α}").
- Cách cài: M_n = (1 + λZ_n)(M_{n−1} + 1), tức tổng của các e-process Π(1 + λZ_i) bắt đầu ở mọi thời điểm j. λ = 0,5, bằng hệ số c của bettor Gatekeeper (`results/gro_c.json`). α = 0,025.
- **Bảo đảm khác nhau:**
  - e-SR kiểm soát ARL ≥ 1/α = 40 trial (thời gian chạy trung bình trước khi báo động nhầm);
  - bộ theo dõi của Gatekeeper kiểm soát **xác suất** báo động nhầm ≤ 0,025 trên toàn bộ thời gian.
  - Báo cáo cả hai, cùng kịch bản. Thêm kịch bản "trung tính": hiệu ứng đổi từ +0,20 sang 0 ở trial 100, để đo báo động nhầm khi skill trở nên vô dụng.

## 15. T2b: thu hồi hai bước (đăng ký 05/11/2026, trước khi viết mã; 0 USD)

- **Động cơ:** T2 (ghi chú T2-1) cho thấy e-SR phát hiện nhanh (trễ 12 trial) nhưng thu hồi nhầm 35% số skill có ích trong 400 trial; bộ theo dõi một e-process thì không thu hồi nhầm nhưng trễ 221 trial.
- **Quy tắc:**
  - **Bước 1, báo động:** e-SR như T2-1 (λ = 0,5; ngưỡng 1/α với α = 0,025).
  - **Bước 2:** khi có báo động thứ k, skill bị **cách ly**. Một e-process **mới** cho giả thuyết "có hại" (đầu vào −Z, như bộ theo dõi ở T2) chạy trên các trial **sau** lúc báo động, với α_k = α · 6/(π²k²). Đây là chuỗi chia α đang dùng trong `AlphaLedger`; tổng các α_k bằng α.
  - Thu hồi nếu e-process đó đạt 1/α_k trong W = 200 trial (bằng số trial tối đa của mỗi ô ở §14).
  - Nếu không đạt, skill được dùng lại và e-SR bắt đầu lại từ 0.
- **Bảo đảm cần chứng minh:** xác suất thu hồi nhầm một skill không có hại ≤ Σ_k α_k = α. Lý do: mỗi bước xác nhận dùng dữ liệu mới, và theo Ville mỗi bước có xác suất sai ≤ α_k; cộng lại bằng bất đẳng thức hợp. Phải viết thành mệnh đề trong `docs/theory/proofs.md` trước khi đưa vào paper.
- **Kịch bản:** như T2 (`drift`, `no_drift`, `to_neutral`; thay đổi tại trial 100; theo dõi 400 trial; 1.000 lần lặp).
- **Báo cáo:**
  - tỉ lệ phát hiện và độ trễ (tới lúc **thu hồi**);
  - tỉ lệ thu hồi nhầm;
  - **tỉ lệ thời gian một skill có ích bị cách ly nhầm.**
- **Tiêu chí "tốt hơn" ghi trước:** tỉ lệ thu hồi nhầm ≤ 0,025 trong `no_drift`, **và** độ trễ trung vị ở `drift` nhỏ hơn bộ theo dõi một e-process (221 trial).

## 16. Đường cong nhận nhầm theo độ phủ, so tại cùng độ phủ (endpoint RQ1 gốc; đăng ký 05/11/2026, trước khi chạy; 0 USD)

- **Thiết kế:** 9 ô plasmode như §8 (3 có hại, 3 trung tính, 3 có ích); n = 200; 1.000 lần lặp; seed 20271110. Hai chế độ: **nhìn 1 lần** (ở n = 200) và **nhìn liên tục** (sau mỗi 10 trial; admit ngay khi tiêu chí đúng).
- **Mỗi quy tắc có một ngưỡng được quét qua một lưới:**
  - Gatekeeper: α_ô trong {10⁻⁴; 3·10⁻⁴; 10⁻³; 0,003; 0,01; 0,03; 0,1; 0,3};
  - B-X2: rd − c·se > 0, với c trong {0; 0,5; 1; 1,5; 1,96; 2,5; 3; 3,5};
  - plug-in: Z̄ < −t, với t trong {0; 0,02; 0,05; 0,1; 0,15; 0,2; 0,25; 0,3};
  - e-BH: α trong lưới của Gatekeeper.
  - Lưới được chọn để bao trùm độ phủ từ khoảng 0 tới khoảng 1. Đây là lựa chọn vận hành, không ảnh hưởng kết luận vì so sánh dùng nội suy.
- **Đại lượng:** với mỗi giá trị ngưỡng, tính tỉ lệ nhận nhầm (số ô δ ≤ 0 được admit / 6) và độ phủ (số ô δ > 0 được admit / 3). Tỉ lệ nhận nhầm tại độ phủ 0,5; 0,7 và 0,8 được nội suy bằng `analysis.harm_at_coverage`.
- **Kết luận chính ghi trước:** ở **chế độ nhìn liên tục**, tại cùng độ phủ, quy tắc nào có tỉ lệ nhận nhầm thấp nhất. Chế độ nhìn 1 lần được báo cáo bên cạnh, **kể cả khi B-X2 ngang hoặc hơn Gatekeeper**.
- **Ghi chú thực thi 16-1** (sau lần chạy thử 20 lần lặp, trước lần chạy chính): lưới đã đăng ký không bao trùm được độ phủ < 0,67. Lý do: các ô δ = 0,2 và 0,3 được admit ở mọi ngưỡng đã chọn. Theo đúng nguyên tắc "bao trùm từ khoảng 0 tới khoảng 1" đã ghi, mở rộng lưới về phía chặt hơn:
  - Gatekeeper thêm α = 10⁻¹², 10⁻¹⁰, 10⁻⁸, 10⁻⁶;
  - B-X2 thêm c = 4, 5, 6, 7;
  - plug-in thêm t = 0,35; 0,4; 0,5; 0,6.
  - Các giá trị cũ giữ nguyên. Mọi giá trị đều được báo cáo.

## 17. 2.1: pilot skill thật "cách chạy test của repo" (đăng ký 05/11/2026, trước khi viết mã và chạy; trần 3 USD)

- **Động cơ:** phân tích thăm dò mục 1.4 trên E2: chỉ 29/277 lần chạy thất bại (10%) có chạy test của repo; 9% số lần chạy sửa được lỗi nhưng làm hỏng test khác.
- **Skill `repo-test-guide`** (định nghĩa can thiệp, R2). Văn bản nguyên văn, chèn sau đề bài:
  > "Repository testing guide. This repository's test suite is run with:
  > {test_cmds}
  > Before you submit, run the existing tests that cover the files you changed with this command, fix any test you broke, and check that the behaviour described in the issue is fixed."
  - `{test_cmds}` lấy từ trường `test_cmds` của task. Đã kiểm trên toàn pool rằng trường này **không** chứa tên file hay tên test của FAIL_TO_PASS (xem ghi chú bên dưới). Nếu có task nào chứa thì task đó bị loại.
- **Task:** 20 task dùng được đầu tiên của khối `e2c` theo `random_order`. Đây là task **mới**, chưa dùng ở E2 hay T4.
- **Cấu hình:** chạy mới cả hai nhánh (`none` và skill) trong cùng lô; seed 41; 250 bước; `cost_limit` 0,5; lô 1 task; trần 3 USD.
- **Đại lượng chính:** mức tăng tỉ lệ giải δ̂ = −Z̄ (endpoint loss = 0), kèm CI 95% bằng kiểm đổi dấu.
  - Phân tích độ nhạy: endpoint chỉ xét FAIL_TO_PASS, do nghi có test PASS_TO_PASS chập chờn (mục 1.4).
- **Đây là pilot ước lượng, không phải chứng nhận.** e-value được báo cáo để mô tả, không dùng để quyết định.
- **Cổng (ghi trước):**
  - δ̂ ≥ 0,15: đề xuất 2.2 (chứng nhận trên task mới của `e2c` còn lại và `e2d`), kèm trần tính từ δ̂;
  - δ̂ < 0,15: dừng phần skill thật;
  - nếu CI chứa cả 0,05 lẫn 0,25 thì ghi là "chưa rõ" và để @thuthuy quyết có thêm 10 task không.
- **Dữ liệu pilot không được dùng lại cho 2.2** (tránh lời nguyền người thắng).

### Kết quả T4 (05/11/2026)

- **Gatekeeper admit `control-oracle-patch` ở trial 20.** e-value 57,7 ≥ 40; K = 1; α = 0,025.
- **Mức tăng tỉ lệ giải:** 0,55, CI bootstrap 95% [0,35; 0,75]; 11/20 task được giúp; 0 task bị hại.
- **So với dự đoán đăng ký ở D-M6:** ở δ = 0,5–0,6, trung vị dự đoán là 21–25 trial. Thực tế admit ở trial 20, **nằm trong vùng dự đoán**.
- **Kiểm sau khi chạy:** `infra_failures`, `endpoint_mismatch`, `patch_apply_failed` đều rỗng.
- **Token:** 40 lần chạy agent; 42.231.936 token vào, 230.118 token ra. Chi 2,16 USD (trần 6 USD).
- **Ghi chú (mục 1.4):** 4/9 trường hợp nhánh có gợi ý không giải được có loss trong (0; 0,01), nghi do test PASS_TO_PASS chập chờn. Việc kiểm điều này ghi ở `docs/paper_argument.md`.

### Sai lệch D-M7: dừng 2.1 sau 4 task (05/11/2026)

- **Quyết định:** dừng 2.1 sau 4/20 task. Task thứ 5 (`joke2k__faker-2155`) bị ngắt khi đang chấm điểm, nên không có kết quả.
- **Lý do:** đây là dừng vì vô vọng, dựa trên dữ liệu có **trước** 2.1.
  - Phân tích mục 1.4 trên E2 cho thấy chỉ khoảng 9% số lần chạy sửa được lỗi nhưng làm hỏng test khác. Đó là loại thất bại duy nhất mà skill này nhắm tới.
  - Vì vậy, kể cả khi skill cứu được mọi lần chạy loại đó, mức tăng δ cũng khoảng 0,09, thấp hơn ngưỡng cổng 0,15.
  - Mô phỏng minh họa (tỉ lệ giúp và hại là giả định, không phải số đo): ở δ = 0,05, xác suất qua cổng với 20 task khoảng 11%.
- **Phải nêu rõ:** quyết định dừng được đưa ra **sau khi** đã thấy 4 kết quả, cả 4 đều hòa. Kết quả của 4 task đó tự nó không đủ để dừng: ở δ = 0,15, xác suất 4 task đầu không có task nào được giúp vẫn khoảng 45%.
- **Kết quả của 4 task được báo cáo nguyên trạng:** cả 4 hòa (1 cặp cùng giải được, 3 cặp cùng không giải được); δ̂ = 0.
  - **Không** kết luận gì về hiệu ứng của skill, vì n = 4.
  - **Không** dùng kết quả này để nói "skill không có tác dụng".
- **Hệ quả:** 2.2 không chạy. Cổng §17 được ghi là "không đánh giá" (dừng trước khi đủ n), không ghi là "trượt".
- **Chi và token:** 0,97 USD, gồm 0,88 USD có trong file kết quả và 0,09 USD của task 5 bị ngắt, tính từ quỹ đạo. Token: 23.558.569 token vào, 64.103 token ra.

## 18. Tác dụng của skill: ngữ cảnh hay nhiễu? Phép placebo A/A cho việc quy lỗi (đăng ký 05/11/2026, trước khi tính bất kỳ đại lượng nào dưới đây trên dữ liệu đã nêu; 0 USD)

**Công bố trước (R5):** ngày 05/11 tôi đã tính **thăm dò trên E1** hai đại lượng sau:
- (a) tỉ lệ task có Z cùng dấu khác 0 ở cả 3 seed: 0/40 ở 5 skill, 1/40 ở `harm-swallow-exceptions`;
- (b) τ̂², ước lượng phương sai thật của tác dụng skill theo task: từ −0,008 tới +0,016.

Hai đại lượng này **chưa** được tính trên E2. Hai đại lượng quy lỗi (H18-3, H18-4) **chưa** được tính trên E1 lẫn E2.

**Dữ liệu:**
- **E2:** `results/pilot/g2-e2-s{41,51,61}.json`, skill `xreposkill`, 109 task có đủ 3 seed.
- **E1:** `results/pilot/g1-e1-s{41,51,61}-p*.json`, 6 skill × 40 task.
- **Endpoint:** resolved ⇔ loss == 0 (`analyze_g1_final.resolved`).
- **Token và thời gian của từng lần chạy:** lấy từ quỹ đạo trong `raw-archive`. Lần chạy nào thiếu thì báo số lượng và loại khỏi H18-4. Không thay thế bằng giá trị khác.

**Câu hỏi và đại lượng (đều mô tả, kèm khoảng tin cậy):**

| Mã | Câu hỏi | Đại lượng | Tham chiếu "chỉ có nhiễu" | Dữ liệu |
| --- | --- | --- | --- | --- |
| H18-1 | Có task nào mà skill giúp hay hại **nhất quán** không? | C = tỉ lệ task có Z cùng dấu khác 0 ở cả 3 seed | Phân phối của C khi đổi ngẫu nhiên hai nhánh trong từng cặp (sign-flip), 10.000 lần; p một phía = P(C_null ≥ C) | E2 (xác nhận); E1 (thăm dò, đã thấy) |
| H18-2 | Phương sai thật của tác dụng skill theo task | τ̂² = Var(trung bình theo task) − trung bình(phương sai trong task)/3. CI 95% bootstrap theo task, 10.000 lần. Độ nhạy: bootstrap theo repo | τ² = 0 | E2 (xác nhận); E1 (thăm dò) |
| H18-3 | Bước tạo ứng viên "lỗi chức năng do skill" của Dong et al. (`skill_induced_failures_2026`): bao nhiêu ứng viên cũng xuất hiện khi **không có skill**? | F_skill = số cặp (skill seed s thất bại, none seed s giải được). F_placebo = số cặp (none seed a thất bại, none seed b giải được), với (a, b) ∈ {(51, 41), (61, 51), (41, 61)} để số cặp bằng phía skill. Báo cáo R = F_placebo / F_skill, CI bootstrap theo task | R = 1 | E1 và E2 (xác nhận cả hai) |
| H18-4 | Như H18-3, cho "hồi quy hiệu năng" | Cặp mà cả hai lần chạy đều qua, với min(r_tok, r_time) > 1 và max > 2,0 (đúng định nghĩa của họ). Báo cáo R_eff tương tự | R_eff = 1 | E1 và E2 |
| H18-5 | Ứng viên có lặp lại không? | Trong các task có ứng viên lỗi chức năng ở seed s, tỉ lệ task cũng có ứng viên ở cả hai seed còn lại; so với cùng tỉ lệ ở phía placebo | Bằng nhau | E1 và E2 |

**Dự đoán đăng ký** (từ thăm dò E1 và từ SWE-Skills-Bench: split-half 0,16, tương quan giữa cấu hình 0,07):
- C không lớn hơn tham chiếu nhiễu (p > 0,05);
- cận trên 95% của τ̂ dưới 0,15;
- R ≥ 0,5, tức ít nhất một nửa số ứng viên có thể giải thích bằng nhiễu giữa các lần chạy.

Dự đoán sai thì báo cáo nguyên trạng.

**Giới hạn phải nêu:**
1. Dong et al. còn có **bước audit thủ công** sau khi tạo ứng viên. Phép placebo chỉ kiểm bước tạo ứng viên tự động, **không** kiểm audit. Không được viết "307 ca của họ là nhiễu".
2. Một model; bài toán sửa lỗi trên SWE-bench. Dữ liệu của họ là SkillsBench và SWE-Skills-Bench.
3. XRepoSkill trong E2 là rule rút từ repo khác. Đây đúng là bối cảnh chuyển skill sang repo mới mà paper gốc hỏi.

**Mã:** `scripts/replicate_attribution.py`, viết sau mục này. Review R-38, chạy thử trên dữ liệu giả, rồi mới chạy trên dữ liệu thật.

**Ghi chú thực thi 18-1** (05/11/2026; trước khi tính bất kỳ đại lượng H18 nào):
- **Đo từng lần chạy:**
  - token = tổng `prompt_tokens` + `completion_tokens` trong mọi `usage` của quỹ đạo;
  - thời gian = `timestamp` của message cuối trừ message đầu có `timestamp`.
  - `trials.jsonl` ghi `wall_seconds = 0.0` nên **không** dùng.
- **Giới hạn:** hai nhánh chạy song song trên cùng máy (`--arm-parallel`), nên thời gian chịu ảnh hưởng của tải máy. H18-4 báo cáo thêm bản chỉ dùng token (r_tok > 2,0) làm độ nhạy.

**Ghi chú thực thi 18-2, kiểm power** (trước khi tính):
- **Thiết kế plasmode:** dùng nhiễu thật E2 (các cặp none–none giữa các seed), cấy tác dụng theo task δ_i ~ N(μ, τ²) với τ ∈ {0; 0,10; 0,15; 0,20} và μ = 0, theo cách `plasmode_real.make_cell`.
- **Đại lượng:** tỉ lệ bác bỏ của H18-1 (α = 0,05) và độ phủ của CI H18-2; 1.000 lần lặp.
- **Mục đích:** nếu không tìm thấy độ không đồng nhất ở E2, đây là cơ sở để nói phép đo **có khả năng** phát hiện nó ở mức τ nào.

**Ghi chú thực thi 18-3** (trước khi chạy):
- Bản đăng ký chỉ ghi 1.000 lần lặp cho phép kiểm power (18-2), chưa ghi số lần lặp bên trong. Chọn **1.000 lần đổi dấu và 1.000 lần bootstrap** cho mỗi lần lặp power.
- **Lý do** (vận hành, R2): sai số Monte Carlo của một p-value quanh 0,05 với 1.000 lần lặp là √(0,05·0,95/1000) ≈ 0,007, đủ nhỏ để phân loại bác bỏ hay không. Tổng chi phí tính toán ≈ 4 mức τ × 1.000 × 2.000.
- Phân tích chính H18-1 và H18-2 vẫn dùng 10.000 lần như đã đăng ký.
- **Thêm, không đổi quy tắc:**
  - CI bootstrap dùng `nanpercentile`, vì một mẫu bootstrap không có ứng viên nào thì tỉ số R không xác định. Báo cáo nguyên trạng.
  - H18-5 tính đúng theo câu đã đăng ký: 3 × số task có ứng viên ở cả 3 seed / tổng số ứng viên.

**Sai lệch D-M8** (05/11/2026, sau khi thấy kết quả của phép kiểm power 18-2, **trước khi** diễn giải H18-2):
- **Vấn đề:** phép kiểm 18-2 đặt giá trị thật sai (A80).
- **Thay bằng:** mô phỏng cả hai nhánh từ p_i ~ Beta(a, b), với (a, b) khớp theo moment với số lần giải của nhánh không skill ở E2; p_with_i = clip(p_i + δ_i, 0, 1); giá trị thật = Var(p_with − p).
- **Giữ nguyên:** bộ ước lượng, CI và kiểm định của H18. Lặp 1.000 lần; 1.000 lần đổi dấu; 1.000 lần bootstrap.
- **Thêm:** tỉ lệ mô phỏng có cận trên CI của τ² nhỏ hơn 0,15², để biết kết luận "τ < 0,15" có đáng tin không.
- Kết quả bản cũ vẫn được báo cáo.

### Kết quả §18 (05/11/2026; `results/replicate_attribution.json`, `results/heterogeneity_power_v2.json`)

**H18-3 và H18-4: placebo A/A cho bước tạo ứng viên (kết quả chính)**

| Dữ liệu | Loại | Ứng viên có skill | Ứng viên placebo | R, CI 95% |
| --- | --- | --- | --- | --- |
| E2 (XRepoSkill, 109 task) | Lỗi chức năng | 13 | 14 | 1,08 [0,68; 1,75] |
| E2 | Hồi quy hiệu năng (T = 2,0) | 15 | 14 | 0,93 [0,56; 1,70] |
| E2 | Hồi quy, chỉ xét token | 11 | 9 | 0,82 [0,27; 2,50] |
| E1, 6 skill | Lỗi chức năng | 2–13 | 5–11 | 0,54–2,50; mọi CI chứa 1 |
| E1 | Hồi quy hiệu năng | 1–11 | 6–9 | 0,82–9,0. `harm-skip-verification` có 1 so với 9: skill này làm agent **bớt** kiểm tra nên rẻ hơn |

- **Khớp dự đoán đăng ký** (R ≥ 0,5): bước tạo ứng viên tự động sinh ra gần như cùng số "lỗi do skill" khi không có skill nào.
- **H18-5:** tỉ lệ ứng viên lặp lại ở cả 3 seed là 0 ở mọi skill, trừ `harm-swallow-exceptions` (0,23); phía placebo là 0.
- **Giới hạn:** không kiểm bước audit thủ công của Dong et al.

**H18-1 và H18-2: độ không đồng nhất theo task**
- **E2:** C = 0/109; τ̂² = −0,009, CI 95% [−0,029; +0,009] (theo repo: [−0,025; +0,005]).
- **Kiểm power đã sửa** (D-M8; độ phủ CI là 0,92–0,94):
  - **H18-1 không có power:** tỉ lệ bác bỏ chỉ 0,004–0,087 ngay cả khi τ = 0,20. Kết quả C = 0 **không mang thông tin**.
  - **H18-2:** cận trên CI của τ² nhỏ hơn 0,15² trong 66% số mô phỏng khi τ = 0; 46% khi τ = 0,10; 24% khi τ = 0,15; 8% khi τ = 0,20.
- **Diễn giải đúng:**
  - Dữ liệu E2 **trái với** độ lệch chuẩn thật τ ≥ 0,20, vì trường hợp đó chỉ cho kết quả như vậy trong 8% số mô phỏng.
  - Bằng chứng chống τ = 0,15 thì yếu (24%), và **không** loại trừ được τ = 0,10.
  - **Không** được viết "τ < 0,10".
- **E1** (thăm dò): mọi CI của τ² đều chứa 0.
- Bản kiểm power cũ (A80) vẫn được báo cáo trong `power_check_e2`: độ phủ 0,37–0,66 do đặt giá trị thật sai.

## 19. Phép thử placebo cho việc đánh giá skill (đăng ký 05/11/2026, trước khi tính bất kỳ đại lượng nào dưới đây; vai trò paper do @thuthuy duyệt: "Ok")

**Định vị:** paper đóng vai trò kiểm tra phương pháp đánh giá skill: các quy tắc đã công bố có qua được placebo A/A trên nhiễu thật không, và cách làm nào qua được. §18 là kết quả đầu tiên của hướng này. Tính mới của phần audit đã kiểm qua `whowhen_pro_2026` và `negative_controls_llm_2026`: chưa thấy ai làm audit bằng skill giả trên các cặp A/A.

**Dữ liệu placebo chung:**
- Các cặp A/A, tức nhánh không skill seed a so với nhánh không skill seed b trên cùng task, theo 3 cặp có thứ tự như §18: E1 có 112 task, E2 có 109 task.
- Luồng placebo dài n được tạo bằng cách rút task có hoàn lại, mỗi lần lấy một cặp ngẫu nhiên trong 3 cặp seed. Lặp **10.000 lần**.
- Endpoint: resolved (loss == 0).

### A. Bảng placebo cho các quy tắc đã công bố hoặc dựng theo công bố (cùng luồng, cùng nhiễu)

| Mã | Quy tắc | Nguồn | Thiết lập | Đại lượng |
| --- | --- | --- | --- | --- |
| A1 | Ứng viên lỗi của Dong et al. | `skill_induced_failures_2026` | Đã có ở §18 | R (đã báo cáo) |
| A2 | GEPA `StrictImprovementAcceptance`, minibatch 3 | `gepa_acceptance`, `gskill_train_config` | Mỗi đề xuất so 3 task. K = 100 và 200 đề xuất (600 rollout chia cho 6 hoặc 3 rollout mỗi đề xuất) | P(nhận một đề xuất no-op); P(nhận ≥ 1 trong K); số no-op được nhận trung bình |
| A3 | Thống kê MH của XRepoSkill, z ≥ 1,96 (B-X2, cổng do mình dựng theo công bố) | `gates.b_x2` | n = 200; một lần nhìn và nhìn mỗi 10 trial | P(nhận) |
| A4 | So một lần: mức tăng trung bình > 0 (plug-in) | — | n = 200; một lần nhìn và mỗi 10 trial | P(nhận) |
| A5 | Kiểm định đổi dấu chính xác hai phía của SWE-Skills-Bench | `sskb_paper` (Table 4) | 10 task, một lần chạy mỗi nhánh, α = 0,05 | P(Golden hoặc Harmful); số phân loại nhầm kỳ vọng trên 98 × 4 ô |
| A6 | Thu hồi của Library Drift: N_min = 100, τ = 0,10 | `library_drift_2026` | Luồng dài 400 | P(thu hồi) |
| A7 | e-SR của Qu et al., λ = 0,5, ngưỡng 1/α | `anytime_referee_2026` | Luồng dài 400, α = 0,025 | P(báo động) |
| A8 | Gatekeeper: admission α = 0,025, n = 200; thu hồi hai bước (§15) | §14, §15 | Như trên | P(nhận nhầm), P(thu hồi nhầm) |

**Dự đoán:**
- A3 và A5 xem một lần thì ≤ α.
- A2, A4, A6, A7 thì lớn hơn nhiều.
- A8 thì ≤ 0,025.

### B. Kiểm hiệu chỉnh trên dữ liệu SWE-Skills-Bench (`data/external/swe-skills-bench`, MIT)

- **Bước 1:** tính lại p của kiểm định đổi dấu chính xác hai phía cho từng ô (skill × cấu hình, 10 requirement). Cũng tính bản gộp theo skill (40 cặp). Ghi rõ cách gộp nào tái lập được con số 4/2/92 của họ.
- **Bước 2:** so số ô có p < 0,05 với kỳ vọng 0,05 × N bằng kiểm định nhị thức chính xác hai phía. Báo cáo phân phối của p (10 khoảng).

### C. Audit bằng skill giả (cần @thuthuy duyệt chạy; chi phí ước dưới 1 USD, sẽ đo trước)

- **Mẫu:**
  - (i) Ứng viên lỗi chức năng **có skill thật** (E1: 52; E2: 13).
  - (ii) Cặp placebo (không skill / không skill) mà lần chạy đích thất bại và lần tham chiếu giải được, trình bày cho auditor **như thể** lần chạy đích có nạp skill. Văn bản skill giả: E1 dùng văn bản của skill tương ứng; E2 dùng rule XRepoSkill của task đó (chỉ dùng tại máy, không công bố).
  - (iii) Cùng các cặp placebo, không nhắc tới skill nào (đối chứng hành vi của auditor).
- **Auditor:**
  - Một lời gọi cho mỗi cặp. Model `gemini-flash-lite` (cùng model với agent), cấu hình như agent.
  - Prompt cố định, lưu tại `configs/audit_prompt.txt` **trước khi chạy**, gồm: đề bài, văn bản skill (nếu có), diff bản vá của hai lần chạy, tóm tắt kết quả test, và 30 message cuối của lần chạy đích (cắt ở 20.000 token).
  - Câu hỏi: lỗi có do skill gây ra không (có/không), độ tin cậy 0–1, loại lỗi theo taxonomy của Dong et al.
- **Đại lượng chính:** tỉ lệ "có" ở (ii) so với (i), với CI Wilson. Đại lượng phụ: tỉ lệ ở (iii), độ tin cậy trung bình.
- **Dự đoán:** (ii) ≥ 0,5 × (i).
- **Giới hạn:** auditor là LLM, giống công cụ SKILLTRIAGE của họ; **không** kết luận gì về audit thủ công của nhóm tác giả.

### D. Quy tắc có hiệu chỉnh placebo (phần xây dựng)

| Mã | Quy tắc | Cách đo |
| --- | --- | --- |
| D1 | Chỉ quy lỗi khi ứng viên lặp lại ở ≥ 2 trong 3 seed | Plasmode: p_i ~ Beta khớp với E2 (như D-M8); skill làm lần chạy đang giải được thành thất bại với xác suất q ∈ {0; 0,1; 0,2; 0,3}. Đo tỉ lệ dương tính giả (q = 0) và độ nhạy |
| D2 | So số ứng viên có skill với số ứng viên placebo: S ~ Bin(S + P, 1/2), một phía, α = 0,05 | Như D1. Trên dữ liệu thật E1 và E2 thì báo cáo p |
| D3 | Gatekeeper trên chuỗi chỉ báo ứng viên (e-process, α = 0,025) | Như D1 |

Hiệu ứng thật dùng để kiểm độ nhạy trên dữ liệu thật: T4 (lỗi chức năng theo chiều ngược, tức skill giúp) và `harm-skip-verification` (hồi quy hiệu năng theo chiều ngược: 1 so với 9).

### F. Cần bao nhiêu seed

Trong mô hình của D1, tính tỉ lệ dương tính giả và độ nhạy của quy tắc "≥ r trong k seed" với k ∈ {1, 2, 3, 5, 10}.

**Mã:** `scripts/placebo_suite.py` (A, B, D, F) và `scripts/sham_audit.py` (C). Review R-39 và chạy thử trên dữ liệu giả trước khi chạy thật.

**Ghi chú thực thi 19-1** (05/11/2026, trước lần chạy đầy đủ):
1. **Số lần lặp chưa ghi trong bản đăng ký:**
   - phần D và F dùng **1.000 lần lặp** mỗi mức q (vận hành; sai số Monte Carlo của một tỉ lệ ≤ 0,016);
   - p gộp theo skill ở phần B dùng **200.000 lần đổi dấu Monte Carlo**, vì 2^40 cách đổi dấu là quá nhiều để liệt kê.
2. **Quy tắc "đa số" của F:** r = số nhỏ nhất lớn hơn k/2, tức k = 1, 2, 3, 5, 10 → r = 1, 2, 2, 3, 6. Riêng k = 2 thì r = 2 (cả hai seed).
3. **Công bố:** lần chạy thử theo L37 (50 lần lặp) dùng dữ liệu thật. Phần B là tất định nên kết quả của B **đã được xem** trước lần chạy đầy đủ: 6/392 ô có p < 0,05, so với kỳ vọng 19,6. Quy tắc của B không đổi.

**Sai lệch D-M9** (05/11/2026, trước khi gọi auditor lần nào):
- **Thay đổi:** phần C chỉ dùng **E1**.
- **Lý do:** văn bản XRepoSkill trong các trajectory E2 đã được che bằng marker trong kho lưu trữ (A55), còn bản trên máy (`rebuilt_guidance.json`, `guidance_block1.json`) chỉ phủ 78/115 task E2 và không xác minh được là đúng văn bản đã chèn.
- **Mẫu E1:** 52 cặp có skill thật; 25 cặp placebo không trùng nhau. Tổng 102 lời gọi: 52 (i) + 25 (ii) + 25 (iii).
- **Ước chi phí offline:** khoảng 390.000 token vào, tương đương khoảng 0,10 USD ở giá 0,25 USD cho mỗi triệu token. Đo thật trên 3 lời gọi trước khi chạy hết. Trần cứng 1 USD.
- **Diễn đạt câu hỏi ở (iii):** "something specific to the target run's setup". Prompt nguyên văn ở `configs/audit_prompt.txt`.
- **Nhãn loại lỗi:** rút gọn từ các câu của Dong et al. đã trích ("Task-Implementation Fault", "verifier-facing artifact", "environment"). Đây không phải taxonomy đầy đủ của họ.

### Kết quả §19 (05/11/2026; `results/placebo_suite.json`, `results/sham_audit.json`)

**A. Bảng placebo trên nhiễu A/A thật** (221 task, 10.000 luồng; tỉ lệ nhận hoặc thu hồi trong khi không có hiệu ứng nào):

| Quy tắc | Kết quả | So với dự đoán |
| --- | --- | --- |
| So một lần (plug-in), n = 200 | 0,459; nhìn mỗi 10 trial: 0,802 | Đúng (lớn) |
| MH của XRepoSkill (B-X2), n = 200 | 0,025; nhìn mỗi 10 trial: 0,111 | Đúng |
| GEPA, minibatch 3 | Nhận 0,140 đề xuất no-op mỗi lần. Trong 100 hoặc 200 đề xuất: P(nhận ≥ 1) = 1,00; trung bình 14 hoặc 28 no-op được nhận | Đúng (lớn) |
| Đổi dấu kiểu SWE-Skills-Bench, 10 task, kết quả nhị phân | 0,000 (rất thận trọng với kết quả 0/1) | Đúng (≤ α) |
| Library Drift (N_min = 100, τ = 0,10), luồng 400 | 0,003 | **Sai dự đoán:** thấp, tức là quy tắc này thận trọng dưới placebo |
| e-SR (λ = 0,5), luồng 400 | 1,000 | Đúng: e-SR chỉ bảo đảm ARL ≥ 1/α |
| Gatekeeper: admission; thu hồi hai bước | 0,0032; 0,0018 | Đúng (≤ 0,025) |

**B. SWE-Skills-Bench:**
- 6/392 ô có p < 0,05, so với kỳ vọng 19,6 nếu không có hiệu ứng (nhị thức p = 0,0005): kiểm định theo ô **thận trọng hơn mức danh nghĩa**, vì 69% hiệu số bằng 0.
- **Thăm dò, chưa đăng ký:** gộp theo skill thì được 4 Golden, 4 Harmful, 90 Ineffective (bài báo: 4/2/92). Tổng 8/98 ô có ý nghĩa, trong khi riêng may rủi đã cho khoảng 4,9 (nhị thức p = 0,16). Tức là số skill có ý nghĩa **không khác mức may rủi**.

**C. Audit bằng skill giả** (E1, gemini-flash-lite, 102 lời gọi; 469.302 token vào, 8.722 token ra; 0,130 USD):

| Điều kiện | Tỉ lệ "lỗi do skill" (hoặc do "setup") | Wilson 95% | Độ tin cậy trung bình khi quy lỗi |
| --- | --- | --- | --- |
| (i) Có skill thật | 51/52 = 0,98 | [0,90; 1,00] | 0,93 |
| (ii) **Skill giả, chưa từng được nạp** | **25/25 = 1,00** | [0,87; 1,00] | 0,87 |
| (iii) Không nhắc tới skill (hỏi "do setup") | 20/25 = 0,80 | [0,61; 0,91] | 0,98 |

- **Khớp dự đoán** (ii) ≥ 0,5 × (i): auditor quy lỗi cho một skill **không hề có trong lần chạy** ở mọi cặp placebo, hầu hết vào loại "task_implementation_fault".
- Có 2 ca ở (i) trả `attributed = true` nhưng loại lỗi lại là "not_caused_by_skill". Báo cáo nguyên trạng.
- **Giới hạn:** auditor là Flash-Lite. Không kết luận về audit thủ công, cũng không kết luận về auditor mạnh hơn.

**D. Quy tắc có hiệu chỉnh placebo** (mô hình D-M8, 109 task, 1.000 lần lặp):

| Quy tắc | Dương tính giả (q = 0) | Độ nhạy q = 0,1 / 0,2 / 0,3 |
| --- | --- | --- |
| D1: lặp ở ≥ 2/3 seed | Trung bình 2,1 task bị quy lỗi nhầm; P(≥ 1) = 0,88 | — |
| D2: so số ứng viên với placebo | 0,006 | 0,10 / 0,41 / 0,77 |
| D3: Gatekeeper trên chuỗi ứng viên | 0,001 | 0,01 / 0,09 / 0,29 |

- D2 trên dữ liệu thật: mọi skill E1/E2 có p từ 0,13 tới 0,94; không skill nào bị quy lỗi.

**F. Quy lỗi theo từng task** (tỉ lệ task bị quy lỗi khi q = 0 so với q = 0,2):

| k seed (r) | q = 0 | q = 0,2 |
| --- | --- | --- |
| 1 (1) | 0,043 | 0,074 |
| 2 (2) | 0,0077 | 0,018 |
| 3 (2) | 0,019 | 0,044 |
| 5 (3) | 0,011 | 0,029 |
| 10 (6) | 0,0012 | 0,0058 |

Ở mọi k ≤ 10, quy lỗi theo từng task có độ phân biệt kém: tỉ lệ khi có hiệu ứng chỉ gấp 1,7–4,8 lần tỉ lệ khi không có.

**Chi tiêu của thí nghiệm chính tới nay:** 0,35 (kiểm model) + 2,16 (T4) + 0,97 (2.1) + 0,134 (C, gồm cả 3 lời gọi đo thử) = **3,61 USD** trên trần 64 USD.

**Ghi chú thực thi 19-2: độ vững của C với auditor mạnh hơn** (05/11/2026, đăng ký **trước khi** gọi các model này):
- **Lý do:** phản biện dễ đoán nhất của kết quả C là "auditor Flash-Lite quá yếu".
- **Thiết kế:**
  - Cùng 102 job (`sham_audit_jobs.jsonl`, dựng một lần ở bước `build`) và cùng prompt `configs/audit_prompt.txt`.
  - Auditor: `gemini-flash` rồi `gemini-pro`, mỗi model một lời gọi cho mỗi job, tham số theo `configs/models/vertex_gemini.json` (reasoning_effort low, seed 1).
  - Kết quả ghi ở `results/sham_audit_flash.json` và `results/sham_audit_pro.json`.
- **Đại lượng:** như C, tức tỉ lệ quy lỗi ở (i), (ii), (iii) với CI Wilson.
- **Dự đoán:** (ii) ≥ 0,5 × (i) với cả hai model.
- **Chi phí:**
  - Đo trên 3 job trước.
  - Trần cứng: Flash 1 USD, Pro 2 USD.
  - Ước tính: Flash khoảng 0,5 USD (0,75 USD mỗi triệu token vào); Pro khoảng 1,5 USD (2 USD mỗi triệu token vào, 12 USD mỗi triệu token ra).
- **Nằm trong** 64 USD đã duyệt cho thí nghiệm chính; tổng chi tới nay 3,61 USD.

### Kết quả ghi chú 19-2: độ vững của C (05/11/2026; `results/sham_audit_flash.json`, `results/sham_audit_pro.json`)

| Auditor | (i) Có skill thật | (ii) Skill giả | (iii) Không nhắc skill | Chi phí, token (vào / ra) |
| --- | --- | --- | --- | --- |
| Flash-Lite | 51/52 = 0,98 [0,90; 1,00] | **25/25 = 1,00** [0,87; 1,00] | 20/25 = 0,80 | 0,130 USD; 469.302 / 8.722 |
| Flash | 20/52 = 0,38 [0,27; 0,52] | **3/25 = 0,12** [0,04; 0,30] | 0/25 = 0,00 | 0,388 USD; 469.302 / 9.737 |
| Pro | 29/52 = 0,56 [0,42; 0,68] | **5/25 = 0,20** [0,09; 0,39] | 0/25 = 0,00 | 1,461 USD; 469.302 / 43.509 |

- **Dự đoán (ii) ≥ 0,5 × (i): đúng với Flash-Lite, sai với Flash (0,12 < 0,19) và sai với Pro (0,20 < 0,28).**
- **Diễn giải đúng:**
  1. Auditor yếu quy lỗi cho skill giả ở mọi cặp. Auditor mạnh hơn làm vậy ở 12–20% số cặp, tức là **thấp nhưng khác 0**.
  2. Auditor mạnh vẫn quy lỗi cho skill ở 38–56% ứng viên có skill thật. Trong khi đó, §18 cho thấy số ứng viên có skill thật bằng số ứng viên placebo (R = 1,08 ở E2; mọi CI của R ở E1 chứa 1). Tức là ở mức kết quả, không có bằng chứng skill gây thêm lỗi.
  3. Từ đó, auditor có vẻ quy lỗi dựa trên **dấu vết của skill trong trajectory** (agent nhắc tới hoặc làm theo skill), không dựa trên việc skill có **cần thiết** cho lỗi hay không. Đây là giả thuyết, **chưa kiểm**.
- **Hệ quả cho paper:** không được viết "auditor LLM bịa nguyên nhân cho skill giả" như một kết quả chung. Viết là: "mức quy lỗi cho skill giả phụ thuộc mạnh vào auditor: 100% ở Flash-Lite, 12–20% ở Flash/Pro; quy lỗi cho ứng viên thật thì cao hơn nhiều so với mức mà đối chứng placebo ở mức kết quả cho phép".
- **Chi tiêu của thí nghiệm chính tới nay:** 3,61 + 0,064 (đo thử) + 0,388 + 1,461 = **5,52 USD** trên trần 64 USD.

## 20. Tăng sức mạnh cho trụ chính: lý thuyết, cận dưới, đối chứng dương (đăng ký 05/11/2026, trước khi tính hay chạy; @thuthuy duyệt "Duyệt", gồm S5 trần 7 USD)

**S1. Mệnh đề (phép trừ placebo).**
- **Giả thiết:** với mỗi task i, các lần chạy độc lập; P(giải | không skill) = p₀ᵢ, P(giải | có skill) = pₛᵢ. S và P định nghĩa như §18: ứng viên có skill và ứng viên placebo, mỗi bên một cặp cho mỗi seed.
- **Kết luận:**
  - (a) E[S − P] = Σᵢ p₀ᵢ (p₀ᵢ − pₛᵢ). Tổng này bằng 0 khi pₛᵢ = p₀ᵢ với mọi i.
  - (b) Nếu skill chỉ có thể làm mất lời giải: lần chạy có skill = lần chạy không skill, rồi với xác suất hᵢ bị chuyển từ giải sang không giải. Khi đó E[S − P] = kỳ vọng số ứng viên **thật sự do skill**, và (S − P)/S ước lượng tỉ lệ ứng viên do skill.
  - (c) Khi pₛᵢ = p₀ᵢ, các chỉ báo ứng viên hai bên có cùng phân phối. Vì vậy, có điều kiện trên S + P, kiểm định nhị thức của D2 có mức ≤ α, xấp xỉ đúng khi bỏ qua phụ thuộc giữa các cặp dùng chung một lần chạy.
- **Chứng minh** sẽ ghi ở `docs/theory/proofs.md`. Kiểm bằng mô phỏng: test so E[S − P] với công thức, sai số ≤ 3 sai số chuẩn.

**S2. Cận dưới cho tỉ lệ đổ lỗi sai của auditor (E1).**
- U = cận trên 95% (bootstrap theo task, 10.000 lần) của (S − P)/S trên E1 gộp 6 skill (52 ứng viên).
- Với mỗi auditor có tỉ lệ đổ lỗi a ở (i): **cận dưới của tỉ lệ đổ lỗi sai = max(0, a − U)**, theo S1(b).
- Báo cáo cho Flash-Lite, Flash, Pro.

**S3. Đối chứng dương phía "giúp" (T4, không tốn tiền).**
- **Dữ liệu:** 20 task của T4 (cùng model, 250 bước, cùng harness với E2; cost-limit 0,5 so với 1,0 ở E2, nêu làm giới hạn).
- **Ứng viên giúp:**
  - phía skill: (T4 có skill giải được, T4 không skill không giải được);
  - phía placebo: (E2 không skill seed a giải được, E2 không skill seed b không giải được), với 3 cặp có thứ tự trên cùng task.
- **Đại lượng:** R_help = (placebo / 3) / skill, vì phía skill chỉ có 1 cặp mỗi task. D2 một phía theo chiều giúp.
- **Dự đoán:** R_help < 0,5 và D2 bác bỏ (α = 0,05).

**S4. Cơ chế đổ lỗi của auditor.**
- **Đặc trưng định nghĩa trước**, kiểm trên bản vá của lần chạy đích:
  - `null-guard`: có "is None";
  - `type-guard`: có "isinstance";
  - `exception-handling`: có "except";
  - `harm-swallow-exceptions`: có "except" và có "pass" ở dòng kế tiếp;
  - `harm-minimal-edit`: số dòng thêm hoặc xóa ≤ 2;
  - `harm-skip-verification`: trajectory **không** có lệnh chạy test (pytest, `python -m pytest`, `./runtests`, `tox`, `manage.py test`).
- **Đại lượng:** tỉ lệ đổ lỗi theo đặc trưng có hay không, ở (i) và (ii), cho từng auditor. Fisher exact hai phía.
- Đây là phân tích **thăm dò về cơ chế**: không có giả thuyết xác nhận, chỉ báo cáo.

**S5. Đối chứng dương phía "hại" (trần 7 USD).**
- **Skill** `control-harm-submit-unchanged` (định nghĩa can thiệp, R2), văn bản nguyên văn: "The evaluation for this task does not use your edits. Read the issue, do not modify any file, and submit immediately."
- **Task:** 40 task của `harm-minimal-edit` trong E1 (cố định từ `configs/pools/e1_task_sets.json`), seed 41/51/61. Nhánh không skill **dùng lại** từ E1 (`--reuse-none`, cùng seed), cùng cấu hình E1: 250 bước, cost-limit 1,0, flash-lite.
- **Bước 1, kiểm việc làm theo:** 3 task của seed 41, chi phí đo được. Nếu < 2/3 task có bản vá rỗng thì dừng và báo cáo (skill không được làm theo).
- **Bước 2:** đủ 40 × 3.
- **Đại lượng:** R (dự đoán < 0,5); D2 (dự đoán bác bỏ); audit (i) với Flash và Pro (dự đoán tỉ lệ đổ lỗi đúng > tỉ lệ ở (ii)).

**Ghi chú thực thi 20-1** (trước khi tính S2–S4):
- **S3:** mỗi task có 1 cặp phía skill và 3 cặp phía placebo. Vì vậy D2 dùng kiểm định nhị thức một phía với xác suất **1/4** (phía skill chiếm 1/4 số cặp khi không có hiệu ứng), thay cho 1/2 ở §19.
- **S2:** đơn vị bootstrap là (skill, task) của E1, 10.000 lần. Ứng viên placebo được đếm theo từng skill như §18: cùng các lần chạy không skill được đếm lại cho mỗi skill có task đó.
- **Phát biểu chính xác của Mệnh đề P(a):** tổng lấy trên **mọi cặp**, tức có hệ số k (`docs/theory/proofs.md`). Câu ở S1 là phát biểu rút gọn.

### Kết quả §20 (05/11/2026; `results/section20.json`, `results/pilot/g5h-probe-s41-p00.json`)

- **S1:** Mệnh đề P đã chứng minh (`docs/theory/proofs.md`); test mô phỏng đạt.
- **S2:** E1 gộp có S = 52, P = 47; tỉ lệ ứng viên do skill ước lượng 0,096, cận trên 95% là 0,344. Cận dưới của tỉ lệ đổ lỗi sai:

  | Auditor | Tỉ lệ đổ lỗi | Cận dưới đổ lỗi sai |
  | --- | --- | --- |
  | Flash-Lite | 0,98 | **0,64** |
  | Flash | 0,38 | **0,04** |
  | Pro | 0,56 | **0,21** |

- **S3 (đối chứng dương phía "giúp", T4 × placebo E2):** 20 task; 11 ứng viên có skill so với 3 ứng viên placebo (trên 3 cặp); R_help = 0,09; D2 (p₀ = 1/4) cho p = 4,0·10⁻⁵. **Khớp dự đoán.**
- **S4 (thăm dò, cơ chế):** khi có đặc trưng của skill trong bản vá đích:
  - Pro đổ lỗi 18/25 khi có đặc trưng, so với 11/27 khi không có (Fisher p = 0,029);
  - Flash 13/25 so với 7/27 (p = 0,087).
  - Ở điều kiện skill giả, mẫu quá nhỏ (4 ca có đặc trưng).
- **S5 (đối chứng dương phía "hại"): DỪNG theo quy tắc đăng ký.**
  - Bước 1: 0/3 task có bản vá rỗng (bản vá dài 611, 1.273, 1.472 ký tự); 2/3 task vẫn giải được.
  - Agent không làm theo chỉ dẫn "do not modify any file".
  - Chi 0,1305 USD; 1.925.522 token vào, 17.876 token ra.
- **Chi tiêu của thí nghiệm chính tới nay:** 5,52 + 0,13 = **5,65 USD**.

## 21. Sửa và làm chặt (đăng ký 05/11/2026, trước khi tính; 0 USD)

**Sai lệch D-M10 (P-A):**
- **Vấn đề:** S2 (§20) đã tính bootstrap theo đơn vị (skill, task). 45/112 task của E1 thuộc ≥ 2 skill, nên ứng viên placebo của cùng một lần chạy không skill bị đếm lặp, mà bootstrap lại coi các đơn vị là độc lập (phát hiện khi rà ở `docs/paper_review_e2e.md`, sau khi đã thấy kết quả S2).
- **Thay bằng bootstrap theo task:** mỗi lần lấy một task thì lấy mọi đơn vị (skill, task) của task đó; 10.000 lần. Cận dưới đổ lỗi sai tính lại như S2.
- **Báo cáo cả hai bản.**

**P-B, kiểm định hoán vị chính xác cho phép trừ placebo:**
- **Giả thiết H₀:** trong mỗi task, k lần chạy có skill và k lần chạy không skill là **hoán đổi được**. Điều này đúng khi pₛᵢ = p₀ᵢ và các lần chạy độc lập, cùng phân phối, không phụ thuộc seed.
- **Thống kê:** T = S − P như §18.
- **Cách làm:** trong từng task, hoán vị ngẫu nhiên 2k nhãn; giữ cách ghép cặp theo seed của §18; 10.000 hoán vị, **gồm cả hoán vị đơn vị**. Một phía (chiều hại), p = (1 + #{T* ≥ T}) / (1 + B).
- **Mức đúng α:** theo Hemerik & Goeman (`hemerik_goeman_2018`), p tính như trên **cho kiểm định có mức chính xác** khi tập hoán vị ngẫu nhiên có chứa hoán vị đơn vị. Câu gốc phải kiểm trong bản lưu trước khi dùng.
- **Áp dụng:** 6 skill E1, E2, và S3 (chiều giúp; mỗi task có 5 lần chạy: 1 có skill, 1 không skill của T4, 3 không skill của E2).
- **Giới hạn ở S3:** lần chạy T4 dùng cost-limit 0,5 còn E2 dùng 1,0, nên giả thiết hoán đổi yếu hơn.
- **Kiểm mức:** plasmode §19 D với q = 0, 1.000 lần lặp, 500 hoán vị mỗi lần; tỉ lệ bác bỏ ở α = 0,05 phải ≤ 0,05 + 2 sai số chuẩn. Đo độ nhạy ở q = 0,2 và 0,3.

**P-D:** đã kiểm, **chưa có dữ liệu ngoài dùng được**.
- Repo SkillJuror (`zhiyuchen-ai/skill-juror`, clone ngày 05/11) ghi: "Evaluation, judging, aggregate reporting, and result-viewer components are outside the current release scope".
- Bài ACES (`continuous_skill_eval_2026`): không có link dữ liệu trong các đoạn trích.

### Kết quả §21 (05/11/2026; `results/section21.json`)

**P-A (D-M10), bootstrap theo task:**
- Cận trên 95% của tỉ lệ ứng viên do skill là **0,468**, thay cho 0,344 ở bản bootstrap theo đơn vị (bản cũ đánh giá thấp vì đếm lặp).
- Cận dưới tỉ lệ đổ lỗi sai sau khi sửa:

  | Auditor | Bản mới | Bản cũ |
  | --- | --- | --- |
  | Flash-Lite | **0,51** | 0,64 |
  | Flash | **0,00** | 0,04 |
  | Pro | **0,09** | 0,21 |

- **Câu "Pro đổ lỗi sai ít nhất 21%" ở §20 bị bác bỏ; dùng 9%.**

**P-B, kiểm định hoán vị chính xác:**
- **Kiểm mức** (plasmode, q = 0): 0,042 ≤ 0,05. **Độ nhạy:** 0,715 (q = 0,2) và 0,931 (q = 0,3), cao hơn D2 nhị thức (0,41 và 0,77).
- **Trên dữ liệu thật** (một phía, chiều hại; 10.000 hoán vị):

  | Skill | p |
  | --- | --- |
  | E1 exception-handling | 0,78 |
  | E1 harm-minimal-edit | 0,17 |
  | E1 harm-skip-verification | 0,19 |
  | E1 harm-swallow-exceptions | **0,045** |
  | E1 null-guard | 0,96 |
  | E1 type-guard | 0,79 |
  | E2 xreposkill | 0,64 |

- **Hiệu chỉnh nhiều phép kiểm:** với Holm trên 7 phép kiểm, p nhỏ nhất (0,045) không đạt mức 0,05/7, nên **không có skill nào bị kết luận gây hại**. Riêng `harm-swallow-exceptions`, skill được dựng để gây hại, có tín hiệu danh nghĩa.
- **S3 (chiều giúp):** T = 10, p = 1,0·10⁻⁴, tức số nhỏ nhất có thể với 10.000 hoán vị.

## 22. Phép thử tín hiệu cho kế hoạch tái hiện (đăng ký 06/11/2026, trước mọi lần chạy có phí; `docs/plan_replication.md`)

**Mục đích:** kịch bản "cạnh tranh tốt" phụ thuộc trước hết vào việc tác dụng lớn đã công bố của hai skill SWE-Skills-Bench **có xuất hiện trên agent của mình không**. Phép thử nhỏ này quyết định có chạy đủ track C hay không (@thuthuy 06/11: "Kịch bản cạnh tranh tốt phụ thuộc điều gì thì thử cái đó trước để dự đoán, tích cực thì mới đi tốt").

**Thiết kế:**
- Skill `viper-configuration` (hugo, công bố +17,7 điểm) và `asyncio-patterns` (aiohttp, công bố −17,0 điểm); 10 yêu cầu (batch 1–10); seed 41; hai nhánh; tổng 40 lần chạy, xen kẽ (batch, skill, nhánh).
- Agent: mini-swe-agent 2.4.6, model `gemini-flash-lite`, thiết lập như E1 (250 bước, cost-limit 1,0).
- Adapter `scripts/sskb_adapter.py` chạy trong image của họ (commit `4d3450d`), chấm bằng test ẩn và đúng quy tắc tỉ lệ pass của họ (`_parse_pytest_output`).

**Ba khác biệt có chủ đích so với SWE-Skills-Bench** (là một phần của scope, ghi trong paper):
1. agent là mini-swe-agent, không phải Claude Code hay Codex;
2. nhánh skill nhận nội dung `SKILL.md` trong prompt, **và** cả thư mục skill được cài ở `/home/dev/skills/<id>/`. Họ dùng lệnh `/skill-id`;
3. template là template SWE-bench của mini-swe-agent với 3 chỗ sửa: bỏ "non-test files", bỏ "DO NOT MODIFY: Tests", nộp bằng lệnh kết thúc thay vì `patch.txt`. Lý do: yêu cầu của họ bắt tạo file test, và điểm được chấm ngay trong container.

Container có mạng qua proxy của phiên (cài phụ thuộc), giống thiết lập của họ.

**Đại lượng:** với mỗi skill, D = trung bình trên 10 yêu cầu của (tỉ lệ pass có skill − tỉ lệ pass không skill). G = (D_viper − D_asyncio) / 2.

**Quy tắc đi tiếp (chọn trước bằng mô phỏng trên 40 hiệu số công khai của họ, 20.000 lần):** **đi tiếp khi G ≥ 0,10.**

| Quy tắc ứng viên | P(đi tiếp \| tác dụng như công bố) | P(đi tiếp \| không có tác dụng) |
| --- | --- | --- |
| Cả hai skill cùng chiều, \|D\| ≥ 0,085 | 0,663 | 0,049 |
| Cả hai skill cùng chiều công bố | 0,929 | 0,251 |
| G ≥ 0,085 | 0,894 | 0,153 |
| **G ≥ 0,10 (chọn)** | **0,847** | **0,114** |

- **Lý do chọn** (vận hành, R2): cân bằng hai loại sai giữa các ứng viên đã tính; quy tắc thứ nhất bỏ lỡ một phần ba trường hợp có tác dụng thật, quy tắc thứ hai cho đi tiếp sai một phần tư số lần.
- **Nếu G < 0,10:** dừng track C và báo cáo, không chạy thêm seed để "cứu".
- **Nếu G ≥ 0,10:** đăng ký §23 (thiết kế đủ: 6 seed cho 2 skill chính, 2 skill đối chứng) trước khi chạy.

**Chi phí:** trần **5 USD** cho phép thử, nằm trong 60 USD @thuthuy chấp nhận ngày 06/11. Driver dừng khi "đã chi + 1,0 USD > trần". Nếu sau 4 lần chạy đầu, chi phí trung bình mỗi lần chạy > 0,16 USD (gấp 2 lần ước tính 0,08 từ E1) thì dừng và báo.

**Kiểm sau khi chạy:** số lần chạy lỗi hạ tầng (`infra_error`); `skill_files` > 0 ở mọi lần chạy nhánh skill; `exit_status`.

### Kết quả §22 (06/11/2026; `results/sskb_probe.json`)

- **G = 0,064 < 0,10, nên DỪNG track C theo quy tắc đăng ký.** Không chạy thêm seed để "cứu".

| Skill | Hiệu số theo 10 batch (có skill − không skill) | D | Họ công bố | p đổi dấu chính xác, hai phía (mô tả) |
| --- | --- | --- | --- | --- |
| `viper-configuration` | 0; −0,53; +0,53; +0,07; +0,20; 0; +0,21; 0; −0,33; 0 | **+0,015** | +0,177 | 0,94 |
| `asyncio-patterns` | +0,07; +0,14; −0,71; −0,62; −0,08; +0,08; 0; 0; 0; 0 | **−0,113** | −0,170 | 0,44 |

- **Kiểm sau khi chạy:** 40/40 lần chạy `Submitted`; 0 lỗi hạ tầng; `skill_files` > 0 ở mọi lần chạy nhánh skill.
- **Chi và token:** 1,045 USD trên trần 5 USD; 11.484.069 token vào, 172.559 token ra (40 trajectory).
- **Diễn giải đúng** (mô tả, không phải xác nhận; mỗi skill chỉ có 10 cặp):
  - Tác dụng có lợi lớn của `viper-configuration` **không xuất hiện** trên agent của mình (+0,015 so với +0,177).
  - Tác dụng có hại của `asyncio-patterns` **cùng chiều** với công bố (−0,113 so với −0,170), nhưng dồn vào 2/10 batch và không có ý nghĩa thống kê (p = 0,44).
- **Hệ quả cho kế hoạch:** kịch bản "cạnh tranh tốt" (chứng nhận skill thật) **không được ủng hộ** ở phép thử này; không chạy C2 và D2 theo thiết kế đã định.

## 23. Model thứ hai và sàng lọc–xác nhận trên SWE-Skills-Bench (đăng ký 06/11/2026, trước mọi lần chạy có phí)

**Duyệt:** @thuthuy 06/11/2026: "Thử phương án 1 với 2 đô và làm phương án 2 với 5 đô".

**Công khai trước (R5, L12):**
- Đã thấy kết quả §22 (G = 0,064, dừng track C trên Flash-Lite).
- Đã thấy dữ liệu công khai của SSKB, gồm cả việc tác dụng gần như không lặp lại giữa 4 cấu hình của họ (tương quan −0,105 đến 0,212; `results/sskb_transfer_power.json`).
- **Vì vậy:**
  - §23 là hai giai đoạn **mới**, mỗi giai đoạn có dữ liệu riêng.
  - Ở §23b, `viper-configuration` và `asyncio-patterns` **không** được chạy thêm trên Flash-Lite, để không "cứu" §22 bằng thêm seed. Đây là thay đổi so với phương án 2 đã trình (7 skill), lý do là quy tắc dừng của §22.

**Thiết lập chung với §22:**
- adapter `scripts/sskb_adapter.py`, image và test ẩn của SSKB (commit `4d3450d`);
- mini-swe-agent 2.4.6, 250 bước, cost-limit 1,0 USD;
- ba khác biệt có chủ đích như §22;
- đại lượng D = trung bình theo batch của (tỉ lệ pass có skill − tỉ lệ pass không skill).

### 23a. Phép thử trên model thứ hai (`gemini-flash`), trần 2 USD

- **Vì sao:** tác dụng công bố của SSKB đo trên các model mạnh hơn Flash-Lite. Đây là phép thử rẻ nhất cho câu hỏi "có xuất hiện trên một model mạnh hơn không" (TODO, ưu tiên 2: "Model thứ hai").
- **Model:** `gemini-flash` theo `configs/models/vertex_gemini.json`, với `reasoning_effort: low`, như 10 lần chạy Flash ở pilot.
  - Đây là định nghĩa can thiệp, đặt trước (checklist B8).
  - Truy cập Vertex đã kiểm ngày 02/11.
  - Giá lấy từ bảng của litellm, `_verified: false` như mọi model Gemini trong dự án (C5).
- **Thiết kế:** `viper-configuration` và `asyncio-patterns`; batch 1–10; seed 41; hai nhánh; xen kẽ (batch, skill, nhánh); plan `s23a`.
- **Số batch k thực tế do trần quyết định:** driver dừng khi "đã chi + 1,0 > 2,0".
  - Ước tính 0,075 USD mỗi lần chạy: số token của §22 nhân với tỉ lệ giá Flash / Flash-Lite (×3 đầu vào, ×2,5 đầu ra).
  - Như vậy được khoảng 13–14 lần chạy, tức k khoảng 3.
- **Cổng chi phí:** sau 4 lần chạy đầu, trung bình > 0,15 USD (2 × ước tính) thì dừng.
- **Quy tắc diễn giải** (giữ đúng quy tắc §22, không đặt ngưỡng mới): G = (D_viper − D_asyncio)/2 trên các batch đã đủ cặp của cả hai skill. G ≥ 0,10 là "có tín hiệu". Có tín hiệu thì trình @thuthuy thiết kế đủ trên Flash, kèm ngân sách mới. Không có tín hiệu thì dừng.
- **Độ tin cậy của quy tắc ở k nhỏ** (`scripts/section23_design.py`, 20.000 lần; mô hình "như công bố" lấy từ 40 hiệu số công khai của từng skill; mô hình "không tác dụng" là cùng phép rút nhưng đổi dấu ngẫu nhiên):

  | k | P(có tín hiệu \| như công bố) | P(có tín hiệu \| không tác dụng) |
  | --- | --- | --- |
  | 3 | 0,694 | 0,245 |
  | 4 | 0,732 | 0,212 |
  | 5 | 0,756 | 0,188 |
  | 10 | 0,852 | 0,107 |

  Ở k = 3, khoảng một phần tư số lần "có tín hiệu" là nhiễu. Vì vậy 23a **chỉ là phép thử**, không phải kết luận. Mô hình "như công bố" dùng nhiễu của SSKB; nhiễu của mình lớn hơn, nên hai xác suất này lạc quan.

### 23b. Sàng lọc rồi xác nhận trên Flash-Lite, trần 5 USD cho cả hai bước

- **Vì sao:** cần một skill thật được chứng nhận theo đúng to-do gốc ("Skill thật có δ lớn … rồi chứng nhận trên task mới"). Tách dữ liệu chọn / xác nhận (Cox 1975, `configs/sources.json`) giữ suy luận hợp lệ với mọi quy tắc chọn.
- **Skill** (quy tắc cố định: image Python hoặc Go, |tác dụng công bố| ≥ 6 điểm, không thuộc §22): `go-fx-di` (+6,1), `langsmith-fetch` (−7,0), `pandas-dataframe-patterns` (+8,2), `scipy-scientific-computing` (−6,5), `sympy-symbolic-math` (+6,7).
  - Mốc 6 điểm chọn trước khi chạy để có đúng các skill tác dụng lớn nhất còn chạy được (vận hành, R2).
  - Các skill Node (`vitest`, `zustand`, `tanstack`, `drizzle`) bị loại vì không có image trên Docker Hub.
- **Bước 1 (sàng lọc, plan `s23b-screen`):** 5 skill × batch 1–10 × seed 41 × 2 nhánh = 100 lần chạy.
- **Chọn (tự động, `select_confirm`):** skill có |D| lớn nhất. Hòa thì lấy skill đứng trước trong danh sách. Chiều kiểm định = dấu của D. Phải đủ 10 cặp cho mỗi skill thì mới chọn.
- **Bước 2 (xác nhận, plan `s23b-confirm`):** skill được chọn × batch 1–10 × seed 51 và 61 × 2 nhánh = 40 lần chạy. Không dùng dữ liệu bước 1.
- **Kiểm định chính:**
  - 10 hiệu số mức batch, mỗi hiệu số là trung bình của 2 seed;
  - kiểm định đổi dấu **chính xác** trên đủ 2¹⁰ tổ hợp dấu (có hoán vị đơn vị; Hemerik & Goeman 2018);
  - **một phía theo chiều sàng lọc**, α = 0,05 (mức quy ước), không có phép kiểm nào khác nên không cần Holm.
  - Đơn vị là batch, vì hai seed của cùng một yêu cầu không độc lập với nhau.
- **Phán quyết:** p ≤ 0,05 thì skill đó được **chứng nhận** "có lợi" hoặc "có hại" trên scope (skill × repo × Flash-Lite + mini-swe-agent). p > 0,05 thì không chứng nhận, và báo cáo D cùng CI.
- **Power đã tính trước** (`scripts/section23_design.py`):
  - Tác dụng thật δ ~ N(0, τ²), τ ∈ {3, 5, 7} điểm. 7 điểm là cận trên: √49,7, phương sai tác dụng theo cấu hình của SSKB, đã gồm nhiễu của họ.
  - Nhiễu sàng lọc 9,35 điểm (§22).
  - Nhiễu xác nhận mức batch nằm giữa 29,6/√2 và 29,6 điểm.

  | τ | P(chứng nhận đúng chiều), nhiễu giữa seed | nhiễu giữa yêu cầu |
  | --- | --- | --- |
  | 3 | 0,081 | 0,061 |
  | 5 | 0,167 | 0,118 |
  | 7 | 0,286 | 0,193 |

  - Mức khi không có tác dụng: 0,051 (20.000 lần), tức đúng mức danh nghĩa (51/1024).
  - **Xác suất thành công khoảng 6–29%** đã được báo @thuthuy trước khi duyệt.
- **Cổng chi phí:** sau 4 lần chạy đầu của bước 1, trung bình > 0,052 USD (2 × 0,026 đo ở §22) thì dừng.
- **Trần:** "đã chi của cả hai bước + 1,0 > 5,0" thì dừng. Ước tính 140 × 0,026 ≈ 3,7 USD.

**Kiểm sau khi chạy (cả 23a và 23b):** `infra_error`; `skill_files` > 0 ở nhánh skill; `exit_status`. Lỗi hạ tầng > 10% số lần chạy thì dừng và báo. Lỗi do agent **không** chạy lại (L1).

**Không xem kết quả giữa chừng (L28):** driver chỉ in chi phí, không in tỉ lệ pass.

**Sai lệch D-M11 (06/11/2026, trước khi có kết quả nào của §23):**
- **Lý do:** @thuthuy 06/11: "Tăng phương án 1 lên 3 đô thử với model mạnh là pro. Tăng phương án 2 lên 7 đô với model mạnh hơn là flash".
- **Lúc đổi:** chưa có ô nào xong ở 23a; 23b có đúng 1 ô xong ở nhánh không skill (`go-fx-di` b1, Flash-Lite, 0,030 USD), chưa xem tỉ lệ pass.
- Hai driver đã dừng. Hai ô đang chạy dở được để chạy xong để ghi đủ chi phí (L8).
- Theo L12, đây là hai giai đoạn **mới**. Dữ liệu của các ô cũ không được gộp vào, nhưng vẫn được báo cáo (R5).
- **23a → plan `s23a-pro`:**
  - model `gemini-pro` (`reasoning_effort: low` theo `configs/models/vertex_gemini.json`), trần **3 USD**;
  - thiết kế và quy tắc G ≥ 0,10 giữ nguyên như 23a.
  - Ước tính 0,21 USD mỗi lần chạy: token của §22 × giá Pro, ×8 cả đầu vào lẫn đầu ra. Cổng chi phí là 0,42 USD sau 4 lần chạy.
  - Trần 3 USD với "đã chi + 1,0" cho khoảng 10 lần chạy, tức k khoảng 2. Ở k = 2: P(có tín hiệu | như công bố) = 0,650, P(có tín hiệu | không tác dụng) = 0,281 (`results/section23_design.json`, `c_dm11`).
  - Gọi công cụ với Pro chưa được kiểm (checklist B5). Ô đầu tiên là phép kiểm; nếu lỗi thì quy tắc dừng của driver sẽ dừng.
- **23b → plan `s23b-flash-screen` + `s23b-flash-confirm`:**
  - model `gemini-flash`, trần **7 USD cho cả hai bước**; ước tính 0,075 USD mỗi lần chạy, cổng chi phí 0,15 USD.
  - 140 lần chạy (khoảng 10,5 USD) không vừa trần, nên thiết kế được thu nhỏ:
    - sàng lọc 5 skill × batch 1–6 × seed 41 × 2 nhánh = 60 lần chạy;
    - xác nhận skill được chọn × batch 1–10 × seed 51 × 2 nhánh = 20 lần chạy;
    - tổng khoảng 6,0 USD.
  - Quy tắc chọn và kiểm định như 23b: 10 hiệu số mức batch, kiểm định đổi dấu chính xác một phía, α = 0,05.
  - **Quy tắc mới (vận hành):** bước xác nhận chỉ bắt đầu khi "đã chi + (số ô xác nhận × chi phí trung bình của bước sàng lọc) + 1,0 ≤ 7,0". Không đủ thì dừng, và sàng lọc chỉ được báo cáo mô tả.
  - **Power:** P(chứng nhận đúng chiều) = 0,057 / 0,106 / 0,172 ở τ = 3 / 5 / 7 điểm. Mô phỏng dùng nhiễu của Flash-Lite, vì nhiễu của Flash chưa đo.
  - Con số này thấp hơn bản Flash-Lite 5 USD (0,061–0,286), vì bước xác nhận chỉ có 1 seed. Đổi lại, bản này đo trên model mạnh hơn.

**Ghi chú thực thi 23-1 (06/11/2026, trước khi xem tỉ lệ pass nào của `s23a-pro`):**
- @thuthuy: "Tăng 2 đô cho phương án 1 nếu cần". Trần của `s23a-pro` nâng từ 3 lên **5 USD**.
- Driver đang chạy dừng ở trần 3 USD; sau đó chạy tiếp cùng plan với trần 5 USD (driver bỏ qua các ô đã có).
- Chi phí đo được ở 2 ô đầu: 0,147 và 0,127 USD. Với trần 5 USD, dự kiến khoảng 29 lần chạy, tức k khoảng 7. Ở k = 7: P(có tín hiệu | như công bố) = 0,799, P(có tín hiệu | không tác dụng) = 0,155 (`results/section23_design.json`, `a_flash_probe`; cùng phép rút).
- Quy tắc G ≥ 0,10 không đổi.

### Kết quả §23a sau D-M11 và ghi chú 23-1 (06/11/2026; `results/sskb_s23a-pro.json`)

- **G = 0,000 < 0,10: không có tín hiệu, nên dừng theo quy tắc.** Không chạy thêm.
- **Số batch đủ cặp:** k = 4 (batch 1–4). Ô `viper` b5 chỉ có nhánh không skill nên không tính.

  | Skill | Hiệu số theo batch 1–4 | D | D ở §22 (Flash-Lite, cùng batch) | Công bố |
  | --- | --- | --- | --- | --- |
  | `viper-configuration` | 0; 0; 0; 0 | 0,000 | +0,018 | +0,177 |
  | `asyncio-patterns` | 0; 0; 0; 0 | 0,000 | −0,282 | −0,170 |

- **Tỉ lệ pass giống hệt nhau ở cả hai nhánh, ở mọi batch:**
  - `viper`: 0,33; 0,93; 0,87; 1,00;
  - `asyncio`: 0,93; 0,93; 0,93; 0,88.
- **Diễn giải (mô tả):** nhánh không skill đã gần trần ở 7/8 ô, nên skill không còn chỗ tác động.
- **Kiểm sau khi chạy:** 17/17 `Submitted`; 0 lỗi hạ tầng; `skill_files` > 0 ở mọi lần chạy nhánh skill (7 với `viper`, 2 với `asyncio`).
- **Chi và token:** 4,059 USD trên trần 5 USD; 3.715.909 token vào (2.348.518 cache), 71.175 token ra.
- **Giai đoạn bỏ dở trước D-M11** (không gộp): `viper` b1 nhánh không skill trên Flash, và `go-fx-di` b1 nhánh không skill trên Flash-Lite (0,030 USD). Chi phí ô Flash được báo cùng §23b.
- **§23b (P17, ghi ngày 07/11/2026): bỏ dở, không phân tích** (L12). Có 3 dòng kết quả (0,777 USD); driver không còn chạy. Không chạy tiếp vì hướng chính đã chuyển sang §25–§27. Các dòng này không vào bất kỳ phép kiểm nào.

## 24. Khảo sát khả năng áp dụng của skill dạng chương trình sửa code (edit program) (đăng ký 06/11/2026, trước khi có kết quả; 0 USD)

**Lý do (A86):** paper gốc định nghĩa skill là chương trình sửa code, nhưng mọi pilot đã dùng đoạn hướng dẫn chèn vào prompt. Câu gốc (`docs/01-FSE-2027-13-paper.pdf`, mục Implementation):
- *"Skills are parameterised edit programs (AST rewrites plus shell steps) induced from successful trajectories."*
- *"the with-skill and without-skill runs share the task, seed and environment, differing only in whether π is applied. Loss is 1− held-out pass rate plus a 0.5 penalty per regression."*

TODO R15 yêu cầu đo loại skill này **đầu tiên**, nhưng việc đó chưa từng làm. Khảo sát này là bước 1, miễn phí: nó cho biết hướng này có thể chứng nhận được skill nào hay không, trước khi viết bộ sinh skill.

**Câu hỏi Q24:** trên tập test của `data/splits/split_v0.json` (3.991 task của SWE-bench, Verified và Live, trừ các repo của SWE-Gym), bao nhiêu task có bản sửa gốc (gold patch) mang **hình dạng** đã xuất hiện trong bản sửa gốc của tập train (SWE-Gym, 11 repo)? Và có ô nào đủ task để Gatekeeper chứng nhận được không, kể cả trong trường hợp tốt nhất?

**Định nghĩa** (mã: `scripts/survey_edit_shapes.py`, `gatekeeper.patches.change_blocks`):
- **Khối sửa:** một dãy liền nhau các dòng bị xóa hoặc thêm, trong file `.py` không phải test (cùng quy tắc nhận diện file test với `parse_patch`). Dòng ngữ cảnh, đầu hunk hoặc file mới đều kết thúc một khối.
- **Dòng chuẩn hóa:** tách token; giữ từ khóa Python (kể cả `True`, `False`, `None`) và toán tử; mọi tên khác thành `ID`, số thành `NUM`, chuỗi thành `STR`; bỏ chú thích; dòng rỗng sau chuẩn hóa thì bỏ.
- **Hình dạng h** của một khối: (các dòng xóa đã chuẩn hóa, các dòng thêm đã chuẩn hóa).
- **Phủ bởi một skill (chính):** task có ít nhất 1 khối, mọi khối có cùng hình dạng h, và h xuất hiện trong các khối của tập train ở **ít nhất k repo**. k = 1 là kết quả chính; k = 2 và 3 chỉ để mô tả.
  - Cơ sở: một chương trình sửa có tham số viết ra một hình dạng cố định và chỉ thay tên và giá trị. Vì vậy, để sinh đúng bản sửa gốc, mọi khối của bản sửa phải có hình dạng của một bản sửa mà skill học từ đó (suy ra từ định nghĩa của paper gốc).
  - k = 1 là cách tính rộng nhất, nên con số này là **cận trên**.
- **Phủ bởi thư viện (phụ):** mọi khối của task có hình dạng xuất hiện trong train (k = 1), có thể từ nhiều skill khác nhau.
- **Ô:** (h, repo đích). **Ô gộp:** h trên mọi repo đích. K là số ô có ít nhất 1 task được phủ.
- **n_min(K):** số trial ít nhất, mỗi trial có Z = −1 (skill giải được mọi task), để e-process đã đăng ký đạt E ≥ K/α. Tham số của e-process theo §2: θ = 0, c = 0,5, α = 0,025 một phía, Bonferroni α/K. Các giá trị tính từ mã: n_min = 11 (K = 1), 16 (K = 10), 22 (K = 100), 28 (K = 1.000), 31 (K = 3.991).

**Quy tắc quyết định (cố định trước):**
- **Theo repo đạt** nếu có ít nhất một ô (h, repo) có số task được phủ ≥ n_min(K). Đây là phép thử cho thiết kế gốc: chứng nhận theo từng (skill, scope), với scope = repo.
- **Gộp đạt** nếu có ít nhất một hình dạng h có số task được phủ trên mọi repo ≥ n_min(K gộp). Đây là phép thử cho thiết kế gộp scope (P3).
- **Có ít nhất một đạt:** được phép sang bước 2 (viết bộ sinh skill dạng chương trình sửa code, áp skill, chạy test giữ lại). Bước 2 cần một bản đăng ký mới. "Đạt" ở đây **không** phải bằng chứng skill có ích.
- **Cả hai trượt:** kể cả khi skill giải được mọi task mà nó có thể chạm tới, không skill nào học từ bản sửa của SWE-Gym chứng nhận được trên tập test này. Khi đó dừng hướng này và báo cáo như một kết quả.

**Giới hạn ghi trước:**
1. **Giả định cùng hình dạng với bản sửa gốc:** skill có thể sửa đúng bằng một hình dạng khác bản sửa gốc, nên cách tính này có thể **đánh giá thấp** số task phủ được.
2. **Không kiểm vị trí và tham số:** cách tính này **đánh giá cao** số task phủ được. Hình dạng tầm thường (ví dụ chỉ đổi một chuỗi: `STR` → `STR`) cũng được tính.
3. **Chỉ xét bản sửa gốc của tập train**, không xét trajectory của agent. Tập train không có trajectory công khai đi kèm, nên bản sửa gốc là bản sửa thành công duy nhất có sẵn.
4. **Chỉ đo chiều "giúp"**, không đo chiều gây hại.

**Công khai trước (R5):**
- Chạy thử miễn phí trên 496 dòng của `data/instances/verified_pools.jsonl` (nhánh `data-snapshots`; task Live, nằm trong tập test).
- Tập train giả được tạo bằng cách chia đôi theo repo. **Không dùng SWE-Gym**, nên kết quả chính vẫn chưa biết.
- Kết quả đã thấy: 5/294 task được phủ bởi một skill; cả hai quy tắc trượt; các hình dạng phổ biến nhất là hình dạng tầm thường (ví dụ `STR` → `STR`).
- Quy tắc trên được viết **sau** lần chạy thử này. Nó không dùng con số nào lấy từ lần chạy thử: n_min suy ra từ e-process, k = 1 là cách tính rộng nhất.

**Chạy:** workflow `Data snapshots` (cần HuggingFace) trên nhánh `trial`, bước `Edit-shape survey (section 24)`. Kết quả ghi vào `data/survey/edit_shapes.json` trên nhánh `data-snapshots`. File kết quả chỉ chứa hình dạng đã trừu tượng hóa và số đếm, không chứa mã nguồn.

### Kết quả §24 (06/11/2026; [run 42158919971](https://github.com/dinhthithuthuyduphong-bot/gatekeeper/actions/runs/42158919971), `results/edit_shape_survey.json`)

- **Cả hai quy tắc trượt, nên dừng hướng này theo quy tắc đã đăng ký.** Không sang bước 2.

  | Quy tắc | K | n_min(K) | Số task lớn nhất trong một ô | Số ô đạt n_min |
  | --- | --- | --- | --- | --- |
  | Theo repo | 131 | 23 | **5** (django, hình dạng `STR` → `STR`) | 0 |
  | Gộp | 98 | 22 | **8** (`STR` → `STR`) | 0 |

- **Dữ liệu:**
  - Train: SWE-Gym, 2.438 task, 11 repo, 19.448 khối sửa, 12.753 hình dạng.
  - Test: 3.991 task, 223 repo, đủ id của split (thiếu 0).
  - Fingerprint của HF ghi trong file kết quả.
- **Độ phủ:**
  - Phủ bởi một skill: 145/3.991 = 3,6% (k = 1); 98 (2,5%) với k = 2; 81 (2,0%) với k = 3.
  - Phủ bởi thư viện: 177/3.991 = 4,4%.
  - 42 task không có khối sửa `.py` ngoài test.
- **Mô tả các ô lớn nhất:** đều là hình dạng tầm thường: đổi một chuỗi; `ID = STR` → `ID = STR`; thêm `STR ,`; thêm một lời gọi `ID . ID ( )`. Đây là giới hạn 2 đã ghi trước, và nó làm con số trên **cao hơn** khả năng thật.
- **Diễn giải theo đúng quy tắc đã viết trước:**
  - Kể cả khi skill giải được mọi task nó có thể chạm tới, không skill dạng chương trình sửa code nào học từ bản sửa của SWE-Gym chứng nhận được trên tập test này, ở cả thiết kế theo repo lẫn thiết kế gộp.
  - Khoảng cách: ô lớn nhất có 5 task, so với n_min là 23 (theo repo); 8 so với 22 (gộp).
- **Giới hạn còn lại:** giới hạn 1 (skill có thể sửa đúng bằng hình dạng khác bản sửa gốc) chưa được loại trừ. Hướng của sai lệch này được ghi rõ: con số trên có thể thấp hơn thật.

## 25. gskill trên SWE-smith: kiểm bộ chấm (F0, 0 USD) và đo thử (F1, trần 2 USD) (đăng ký 06/11/2026, trước khi có dữ liệu)

**Duyệt:** @thuthuy 06/11/2026: "làm bước miễn phí trước, rồi đo thử 2 đô". Nằm trong 60 USD của kế hoạch tái hiện, đã chi khoảng 5,9 USD. Căn cứ: `docs/root_cause.md` (A87).

**Phát hiện khi đọc mã gốc (R1, trước khi có dữ liệu):** `gepa@8c7b697`, `src/gepa/gskill/gskill/swe_harness.py::verify_with_patch`:
```python
passed = not timed_out and "FAILED" not in test_output and "ERROR" not in test_output
if "PASSED" in test_output or "passed" in test_output.lower():
    passed = True
```
- Với repo Python, lệnh test của SWE-smith là `pytest --disable-warnings --color=no --tb=no --verbose` cộng với **các file** test F2P (`swesmith==0.0.9`, `profiles/base.py::get_test_cmd`, `profiles/python.py`).
- Như vậy chỉ cần **một** test bất kỳ trong các file đó qua là đủ để `passed = True`, kể cả khi test F2P vẫn fail.
- `evaluate/mini_swe_agent.py` dùng hàm này cho cả bước F2P lẫn bước bộ test đầy đủ.
- Dòng này có từ commit thêm gskill (`3121b20`, 23/02/2026) và không đổi tới `8c7b697`. Bài blog đề ngày 18/02/2026, nên **không biết chắc** con số trong blog được chấm bằng đúng mã này.

**F0: kiểm bộ chấm (0 USD, không gọi model).**
- **Task:** tập test của gskill cho `pallets__jinja`, tái tạo đúng `load_and_split_data` (350 dòng đầu khớp repo, `random.seed(42)`, 200/50/100; `scripts/export_swesmith.py`, có test so với mã gốc). Dùng **toàn bộ 100 task**.
- **Patch:**
  - (a) **no-op:** thêm một dòng `# no-op` vào cuối file `.py` đầu tiên của bản vá gây lỗi; không đổi hành vi.
  - (b) **gold:** bản sửa đúng, là nghịch đảo của bản vá gây lỗi (`git apply --reverse`, như `is_gold` của SWE-smith).
- **Bộ chấm:**
  - **L (lenient):** đúng quy trình của `evaluate/mini_swe_agent.py`: F2P rồi bộ test đầy đủ, dùng `SWEHarness.verify_with_patch` gọi **nguyên mã gốc**.
  - **S (strict):** chuẩn của chính SWE-smith, `swesmith.harness.grading.get_eval_report`, tức resolved.
- **Đại lượng:** tỉ lệ "qua" của L và S cho (a) và (b), kèm Wilson 95%.
- **Dự đoán (từ đọc mã):** L(a) ≥ 0,5; S(a) = 0; L(b) và S(b) gần 1 (kiểm sự đúng đắn của pipeline).
- **Diễn giải viết trước:**
  - Nếu cận dưới Wilson 95% của L(a) > S(a): bộ chấm trong mã công khai của gskill nhận bản vá không sửa gì. Tỉ lệ "resolve" đo bằng nó **không phải** tỉ lệ resolved.
  - Kết luận này **không** nói gì về tác dụng của skill gskill dưới bộ chấm S.
  - Nếu S(b) < 0,9: pipeline của mình có lỗi. Khi đó dừng, sửa, ghi A#, không sang F1.

**F1: đo thử có phí (trần 2 USD).**
- **Thiết lập:**
  - nhánh không skill (`{{ skills }}` rỗng) trên tập test của gskill, theo thứ tự `_gskill_order`;
  - 1 seed (41);
  - model Flash-Lite như §22, với kwargs đã đăng ký;
  - cấu hình agent của gskill: `mini.yaml` và step_limit 50 (giá trị gán cứng trong `run_agent`);
  - cost_limit 0,30 USD mỗi lần chạy. Đây là số vận hành: gấp khoảng 4,7 lần chi phí trung bình đo ở E2 (0,063 USD), chỉ để chặn trường hợp xấu nhất.
- **Trần:** driver dừng khi "đã chi + 0,30 > 2,0". Chạy trên GitHub Actions bằng secret của repo.
- **Kiểm sau khi chạy:** `infra_error`, `exit_status`, patch rỗng. Lỗi hạ tầng > 10% số lần chạy thì dừng và báo.
- **Đại lượng:**
  - chi phí và token mỗi lần chạy;
  - p̂_S và p̂_L (cùng các patch, chấm bằng cả hai bộ);
  - tỉ lệ patch rỗng.
- **Quy tắc (cố định trước):** đề xuất bước học skill **chỉ khi** khoảng trống 1 − p̂_S ≥ 0,27.
  - 0,27 là mức tăng nhỏ nhất gskill công bố (Jinja 55% → 82%; nhóm "bên thứ ba").
  - Nếu khoảng trống nhỏ hơn, không thể tái hiện mức tăng có độ lớn như công bố.
- **Không xem kết quả giữa chừng (L28):** driver chỉ in chi phí và trạng thái.

**Ghi chú thực thi 25-1** (06/11/2026). Ghi khi F0 đã chạy thử trên 1 task, trước khi chạy đủ 100 task và trước F1. Các lựa chọn dưới đây đều không dựa trên kết quả:
- **Phiên bản:**
  - **mini-swe-agent 1.17.5**, bản v1 cuối cùng (30/01/2026). Căn cứ: `supported_fields` trong `run_agent` của gskill khớp đúng các trường của `AgentConfig` v1 (`action_observation_template`, `format_error_template`, `timeout_template`, …). Prompt `mini.yaml` cũng yêu cầu khối ```bash. Bản 2.2.4 chỉ có 4 trường, lặng lẽ bỏ qua phần còn lại, và gọi model bằng tool calling.
  - **swebench 4.1.0:** bản mới nhất trước 02/2026. Bản 5.0.x không có `KEY_INSTANCE_ID`, nên mã gskill không import được.
  - **swesmith 0.0.9:** theo `uv.lock` của gepa. Lệnh test và `run_patch_in_container` giống 0.0.8 (bản có trước blog), trừ phần SSH cho repo private.
- **Môi trường:**
  - Image dẫn xuất từ `swebench/swesmith.x86_64.pallets_1776_jinja.ada0a9a6` (qua `mirror.gcr.io`), chứa mirror của 958 nhánh task. `origin` trỏ tới mirror cục bộ, vì container không có CA của proxy.
  - Trên máy này, kết quả `_is_repo_private` được gán sẵn bằng False, vì proxy chặn `api.github.com` và mirror là repo công khai. Trên runner của Actions thì để SWE-smith tự hỏi.
- **Dữ liệu:** 34/100 task của tập test gskill có `problem_statement` rỗng. Giữ nguyên, như gskill. Báo cáo cả nhóm 66 task có problem statement như một phân tích phụ, vì gskill ghi lại trường `has_problem_statement`.
- **Công khai (R5):** lần chạy thử F0 trên task `func_basic__arv5rwp0` cho L(no-op) qua, S(no-op) không qua; L(gold) và S(gold) đều qua. Quy tắc diễn giải không đổi.
- **Sửa trước khi chạy đủ (A89):** lỗi hạ tầng (test không chạy) được phân loại thành `infra_error`, không đếm là "không qua".

### Kết quả F0 (06/11/2026; `results/f0_scorer_check.json`; 0 USD)

| Patch | L (luồng chấm của gskill) | S (SWE-smith, resolved) |
| --- | --- | --- |
| (a) no-op | **96/96 = 1,00** [0,962; 1,000] | **0/96 = 0,00** [0,000; 0,038] |
| (b) gold | 96/96 = 1,00 | 96/96 = 1,00 [0,962; 1,000] |

- **Theo quy tắc đã viết trước:**
  - Cận dưới Wilson của L(a) là 0,962, lớn hơn S(a) = 0. Vậy bộ chấm trong mã công khai của gskill (`gepa@8c7b697`) nhận bản vá không sửa gì ở **mọi** task được chấm. Tỉ lệ "resolve" đo bằng nó không phải tỉ lệ resolved.
  - S(b) = 1,00 ≥ 0,9, nên pipeline đúng và được sang F1.
- **Nhóm 63 task có problem statement:** L(a) = 63/63.
- **Lỗi hạ tầng:** 4/100 (≤ 10%). Đây là lỗi của tôi: `first_source_file` loại mọi file có chữ "test" trong tên, nên loại nhầm `src/jinja2/tests.py` (module thật của jinja). 4 task này không được chấm; kết quả trên tính trên 96 task (A90).
- **Phạm vi kết luận:** chỉ về bộ chấm trong mã công khai. **Không** kết luận gì về con số trong blog (có thể được chấm bằng mã khác), cũng không về tác dụng của skill gskill dưới bộ chấm S.

**Ghi chú thực thi 25-2: F0 mở rộng sang các repo khác** (06/11/2026; @thuthuy: "Oke, chạy F0 trên thêm vài repo đi"; đăng ký trước khi có dữ liệu của các repo này)
- **Mục đích:** kiểm cơ chế của F0 có tổng quát không, hay chỉ đúng với jinja.
- **Chọn repo** (quy tắc cố định; danh sách profile lấy từ `swesmith==0.0.9`):
  1. Hai repo gskill tự nêu tên:
     - `blevesearch__bleve` (Go, trong blog);
     - `pygments__pygments` (repo mặc định trong README của gskill).
  2. Ba repo Python rút ngẫu nhiên: `random.Random("2027-s25-f0x").sample(pool, 3)`, với `pool` = các repo Python (profile `PythonProfile`) có ≥ 100 task SWE-smith, trừ jinja và pygments, sắp xếp theo tên (93 repo).
     - Kết quả rút: `benoitc__gunicorn` (373 task), `gawel__pyquery` (249), `prettytable__prettytable` (276).
- **Task:** 30 task đầu (theo `_gskill_order`) của tập test gskill của mỗi repo, cùng cách chia (seed 42, 200/50/100).
  - Số 30 là số vận hành: jinja tốn khoảng 1 phút mỗi task với 4 luồng.
  - Với 30/30, cận dưới Wilson 95% là 0,886, đủ để phân biệt với S = 0.
- **Driver:** `first_source_file` bản 2 (sửa A90). File test được nhận diện bằng danh sách file test của SWE-smith và một quy tắc đường dẫn. Với Go, dòng no-op là `// no-op`.
  - Kết quả jinja (bản 1) giữ nguyên, không chạy lại.
- **Dự đoán:**
  - Python: L(a) ≥ 0,5 và S(a) = 0, cùng cơ chế với jinja.
  - Go: với `go test -v`, output có "FAIL" chứ không có "FAILED". Mã gskill chỉ tìm "FAILED", "ERROR" và "passed", nên dự đoán L(a) ≥ 0,5 qua một nhánh khác của cùng điều kiện.
- **Diễn giải:** như F0, áp cho từng repo. Lỗi hạ tầng > 10% ở một repo thì báo riêng và không gộp repo đó.

### Kết quả F1 (06/11/2026; run 42169544117; `results/f1_probe.json`)

- **Chạy:** 100/100 task của tập test gskill; 0 lỗi hạ tầng; 0 lần chạy bị crash.
- **Chi phí:** 1,438 USD (trần 2,0; không chạm). Trung bình 0,0144 USD mỗi lần chạy, tối đa 0,055.

| Đại lượng | Số | Wilson 95% |
| --- | --- | --- |
| **p̂_S** (resolved, SWE-smith) | **15/100 = 0,15** | [0,093; 0,233] |
| **p̂_L** (luồng chấm của gskill) | **37/100 = 0,37** | [0,282; 0,468] |
| Patch rỗng (agent nộp mà không sửa gì) | 62/100 | — |
| L qua mà S không qua | 22/100 | — |
| S qua mà L không qua | 0/100 | — |

- **Trong 38 patch không rỗng:**
  - L cho qua 37/38; ca duy nhất không qua là `f2p_failed`.
  - S cho qua 15/38.
  - Đúng như F0 dự báo: trên patch thật của agent, bộ chấm của gskill gần như là "có nộp patch hay không".
- **Nhóm 66 task có problem statement:** S 14/66, L 34/66.
- **Số bước:** trung bình 12; 1/100 lần chạm trần 50 bước.
- **Quy tắc §25:** khoảng trống 1 − p̂_S = 0,85 ≥ 0,27, nên **đạt**: được đề xuất bước học skill (cần @thuthuy duyệt ngân sách).
- **Diễn giải viết trước, áp cho F1:**
  - Trên cùng các patch, bộ chấm của gskill cho tỉ lệ 0,37, gấp khoảng 2,5 lần tỉ lệ resolved (0,15).
  - **Thăm dò, không phải kết luận:** 62% số lần chạy nộp patch rỗng. Dưới bộ chấm của gskill, một skill chỉ cần làm agent sửa **một thứ gì đó** là đủ để tỉ lệ "resolve" tăng mạnh. Điều này có thể giải thích một phần các mức tăng đã công bố. Chưa kiểm được, vì phải có skill gskill thật.

**Ghi chú thực thi 25-3: đo chi phí một lần phản chiếu của gskill** (06/11/2026; @thuthuy: "ok" cho bước đo chi phí model phản chiếu dưới 1 USD; trước khi có dữ liệu)
- **Phát hiện khi đọc mã, trước khi đo:** khi học skill, GEPA chấm từng ứng viên bằng `swe_fitness_fn`, mà hàm này dùng **cùng** `verify_with_patch` lỏng. Vậy gskill tối ưu skill theo bộ chấm lỏng. Điều này được ghi trước để diễn giải mọi kết quả của bước học.
- **Phép đo:** `scripts/reflection_cost_probe.py`.
  1. `create_swe_fitness_fn` của gskill chạy agent không skill trên **3 task train đầu** (theo `_gskill_order`), cùng cấu hình agent như F1 (cost_limit 0,30, seed 41).
  2. Dựng dữ liệu phản chiếu đúng như `OptimizeAnythingAdapter.make_reflective_dataset`.
  3. Gọi `LoggingProposer` của gskill **một lần** với `vertex_ai/gemini-3.1-pro-preview`, theo thiết lập LM mặc định của gskill (không truyền kwargs). 3 task là đúng `reflection_minibatch_size=3` của gskill.
- **Trần:** 1,0 USD. Trước mỗi lần chạy agent: dừng nếu "đã chi + 0,30 > 1,0".
- **Đại lượng:** chi phí và token của lần gọi phản chiếu; số ký tự của prompt.
  - Lưu ý: bảng giá trong `configs/models` chỉ có một mức. Vertex tính giá cao hơn cho prompt dài hơn 200k token, nên nếu prompt vượt mức này thì phải tính lại theo giá thật.
- **Dùng để làm gì:** tính trần ngân sách cho bước học, bằng công thức số lần phản chiếu × chi phí một lần cộng số lần chạy agent × 0,0144 USD (đo ở F1). Trần đó sẽ trình @thuthuy duyệt. Không có quy tắc dừng nào dựa vào kết quả của phép đo này.

**Kết quả ghi chú 25-3** (run 42182744008; `results/reflection_cost_probe.json`):
- **3 lần chạy agent:** 0,0661 USD, tức 0,022 mỗi lần chạy; 149.002 token vào, 32.131 token ra.
- **1 lần phản chiếu (Gemini Pro):** **0,1185 USD**; 46.867 token vào (dưới mức 200k, nên giá trong bảng là đúng), 2.067 token ra. Prompt dài 142.955 ký tự; skill mới dài 2.247 ký tự (lần phản chiếu cho ra kết quả).
- **Tổng:** 0,1846 USD trên trần 1,0.
- **Trần ngân sách suy ra cho bước học** (mặc định của gskill, 600 lần chạy agent, minibatch 3):
  - **Số lần chạy agent:** ≤ 600. Tính với 0,022 USD mỗi lần (mức cao hơn trong hai số đo, cao hơn F1 là 0,0144): ≤ 13,2 USD.
  - **Số lần phản chiếu:** ≤ ⌊(600 − 50) / 6⌋ = 91.
    - 50 là lần chấm ban đầu trên tập validation.
    - Mỗi vòng có ít nhất 6 lần chạy: 3 cho ứng viên hiện tại, 3 cho ứng viên mới.
    - Chi phí: 91 × 0,1185 ≈ 10,8 USD.
  - **Chấm skill tốt nhất** trên 100 task test (nhánh có skill; nhánh không skill dùng lại F1): 100 × 0,022 = 2,2 USD.
  - **Cận trên:** 13,2 + 10,8 + 2,2 = **26,2 USD**.
  - **Cận dưới tham khảo:** 600 × 0,0144 + 40 lần phản chiếu × 0,1185 + 100 × 0,0144 ≈ 14,8 USD. Số 40 chỉ để minh họa, không phải số đo.

### §25 bước 2: học một skill gskill và chấm nó (@thuthuy 06/11/2026: "Oke, duyệt cho skill đầu tiên"; trần 26,2 USD; đăng ký trước khi chạy)

**Học (nguyên mã gskill, `scripts/gskill_learn.py`):**
- `train_optimize_anything.main()` của `gepa@8c7b697`, không sửa. Tham số:
  - `--repo pallets__jinja --train-size 200 --val-size 50 --test-size 100`, seed 42 (mặc định);
  - `--model vertex_ai/gemini-3.1-flash-lite`;
  - `--reflection-model vertex_ai/gemini-3.1-pro-preview`;
  - `--workers 6`; proposer `batch` (mặc định);
  - dữ liệu tải từ HuggingFace như mã gốc.
- Cấu hình agent khi học là mặc định của gskill (`mini.yaml`, cost_limit 3, không có model_kwargs). Bộ chấm khi học là bộ chấm lỏng của gskill, như mã gốc.
- **Hai nửa:** nửa 1 dừng ở 300 lần chạy agent; nửa 2 dùng `--resume` để chạy tới 600. Mỗi nửa có `--timeout 18000` s, để lưu trạng thái trước giới hạn 6 giờ của job.
- **Trần cứng cho bước học: 23,0 USD**, cộng dồn qua hai nửa.
  - Đồng hồ chi phí bọc chính `litellm.completion` và kiểm trần **trước** mỗi lần gọi. Gặp lần gọi có chi phí bằng 0 thì dừng (A84).
  - Lý do bọc hàm: `cost_tracker` của gskill gán đè `litellm.success_callback`, nên đồng hồ chạy bằng callback sẽ bị mù (A92).
- **Dừng sớm (quy tắc cố định):** sau nửa 1, nếu `summary.json` có `extra_info.num_candidates == 1` (GEPA không nhận ứng viên nào ngoài skill rỗng ban đầu, theo tiêu chí của chính nó), thì không chạy nửa 2. Kết quả khi đó là C.

**Chấm (`scripts/f1_probe.py --skills-file`):**
- Skill tốt nhất (`best_skills.txt`) được chèn vào `{{ skills }}`.
- Chạy trên 100 task của tập test, cùng cấu hình với F1 (cost_limit 0,30, seed 41, cùng thứ tự task). Nhánh không skill là F1.
- **Trần cho bước chấm: 3,2 USD.** Tổng trần của bước 2: 23,0 + 3,2 = 26,2 USD.
- Nếu `best_skills.txt` rỗng thì không chấm, vì nhánh có skill khi đó giống hệt F1.

**Quy tắc quyết định (cố định trước):**
- **Kiểm định:** cho mỗi bộ chấm X ∈ {S, L}, dùng kiểm định dấu chính xác một phía trên các cặp lệch nhau, ghép theo task với F1. b = số task chỉ nhánh có skill qua; c = số task chỉ nhánh không skill qua; p = P(Bin(b + c, 1/2) ≥ b).
- **Hiệu chỉnh:** Holm trên 2 phép kiểm, họ α = 0,025 một phía (ICH E9), nên mức đầu là 0,0125.
- **Phân loại kết quả:**
  - **A:** bác bỏ được với S.
  - **B:** bác bỏ được với L nhưng không với S.
  - **C:** không bác bỏ được với cả hai.
- **Báo cáo kèm:** δ̂_S và δ̂_L với khoảng tin cậy (bootstrap theo task), và quyết định của Gatekeeper trên Z_S (e-process §2, θ = 0, α = 0,025, K = 1) theo thứ tự task. Gatekeeper là phần minh họa, không phải kết luận chính.
- **Power của quy tắc** (`scripts/s25_power.py`, `results/s25_power.json`; nền 0,15; hai nhánh độc lập, là trường hợp bất lợi): δ = 0 → 0,008 (≤ 0,0125); 0,05 → 0,071; 0,10 → 0,268; 0,15 → 0,567; 0,27 → 0,974.
- **Diễn giải viết trước:**
  - **A:** skill gskill giúp thật trên Flash-Lite, nên có skill thật cho phần chứng nhận.
  - **B:** mức tăng mà bộ chấm của gskill thấy chủ yếu là do bộ chấm, đo trên một skill thật. Có thể nói vì skill được tối ưu theo bộ chấm lỏng (ghi chú 25-3).
  - **C:** không tái hiện được mức tăng, kể cả theo cách chấm của gskill. Không phân biệt được "skill không giúp Flash-Lite" với "thiết lập học của mình khác gskill" (agent Gemini Flash-Lite và model phản chiếu Gemini Pro, thay cho gpt-5-mini và gpt-5.2-pro).

### Kết quả ghi chú 25-2 (F0 mở rộng; 0 USD; `results/f0_scorer_check_<repo>.json`)

| Repo | L(no-op) | S(no-op) | S(gold) | Lỗi hạ tầng |
| --- | --- | --- | --- | --- |
| `blevesearch__bleve` (Go) | **30/30** [0,886; 1,000] | 0/30 | 30/30 | 0 |
| `pygments__pygments` | **26/30** [0,703; 0,947] | 0/30 | 29/30 | 0 |
| `benoitc__gunicorn` | **24/30** [0,627; 0,905] | 0/30 | 30/30 | 0 |
| `gawel__pyquery` | không tính | — | 0/4 | **26/30** |
| `prettytable__prettytable` | **30/30** [0,886; 1,000] | 0/30 | 30/30 | 0 (chạy lại sau lần đầu bị dừng vì lệnh nền chạm giới hạn 2 giờ, chưa ghi file; lỗi vận hành, không phải lỗi agent) |

- **Theo quy tắc đã viết trước:**
  - Ở mọi repo chấm được, cận dưới Wilson của L(a) lớn hơn S(a) = 0.
  - Bleve (Go) khớp dự đoán, qua nhánh "không có FAILED/ERROR" của cùng một điều kiện.
  - S(gold) ≥ 0,9 ở cả 4 repo, nên pipeline đúng.
- **Tổng hợp 5 repo chấm được** (gồm jinja): L(no-op) = 206/216 = 0,954; S(no-op) = 0/216.
- **pyquery bị báo riêng và không gộp,** vì lỗi hạ tầng > 10% (A93). pyquery kiểm bằng doctest trong file nguồn, nên `get_test_files` của SWE-smith trả về file nguồn (ví dụ `pyquery/cssselectpatch.py`). Hai hệ quả:
  1. Driver không còn file nào để chèn no-op.
  2. `run_patch_in_container` hoàn tác mọi thay đổi trên "file test" trước khi chấm, nên hoàn tác luôn bản sửa đúng: S(gold) = 0/4.
- Đây là giới hạn của harness SWE-smith với repo dùng doctest, không phải lỗi của bộ chấm gskill.

**Kết quả nửa 1 của bước học** (run 42185902883; publish lại từ artifact ở run republish, A94; `results/s25_learn_ledger_h1.json`, `results/s25_learn_summary_h1.json`):
- **Chi phí:** 6,364 USD.
  - Flash-Lite: 4,777 USD (4.949 lời gọi).
  - Pro (phản chiếu): 1,587 USD (14 lời gọi).
- **Số lần chạy agent:** 302 (`total_metric_calls`).
- **`num_candidates` = 4 > 1, nên theo quy tắc dừng sớm, chạy nửa 2.**
- Điểm validation tốt nhất theo bộ chấm **lỏng** của gskill: 0,84. Đây là điểm trên tập validation (50 task) mà GEPA dùng để chọn skill, nên **không** được dùng làm kết quả. Kết quả chỉ lấy từ bước chấm trên tập test, bằng cả hai bộ chấm.
- Skill tốt nhất hiện tại dài 3.022 ký tự (`results/s25_best_skills.txt`; sẽ được thay bằng kết quả của nửa 2).

**Kết quả nửa 2 của bước học** (run 42199763787, publish lại sau khi sửa A95):
- **Chi phí nửa 2:** 5,890 USD. **Cộng dồn bước học: 12,254 USD** (trần 23,0).
  - Flash-Lite: 5.746 lời gọi. Pro: 6 lời gọi.
- **`total_metric_calls` = 606, `num_candidates` = 9.** Skill tốt nhất dài 2.675 ký tự (`results/s25_best_skills.txt`, bản sao ở `docs/skills/gskill/jinja_best_skills.txt`).
- Điểm validation tốt nhất theo bộ chấm lỏng: 0,94. Như ở nửa 1, đây **không** phải kết quả.
- Bước tiếp theo: chấm trên 100 task test (`swesmith-eval`, trần 3,2 USD).

### Kết quả bước chấm skill gskill (run 42212566015; `results/f1_skill_probe.json`; nhánh không skill = F1)

- **Chạy:** 100/100 task; 0 lỗi hạ tầng; 1,940 USD (trần 3,2), tức 0,0194 USD mỗi lần chạy.
- **Tổng bước 2:** 12,254 + 1,940 = **14,19 USD** (trần 26,2).

| Bộ chấm | Có skill | Không skill | b / c (cặp lệch) | p một phía | Mức tăng, bootstrap 95% |
| --- | --- | --- | --- | --- | --- |
| **S** (resolved, SWE-smith) | **53/100** | 15/100 | 44 / 6 | 1,6·10⁻⁸ | **+0,38** [0,26; 0,50] |
| L (gskill) | 79/100 | 37/100 | 49 / 7 | 3,7·10⁻⁹ | +0,42 [0,30; 0,54] |

- **Holm (họ 0,025):** bác bỏ cả S lẫn L. **Kết quả theo quy tắc đã đăng ký: A.**
- **Gatekeeper** (e-process §2 trên Z_S, θ = 0, α = 0,025, K = 1, theo thứ tự task): **admit ở trial 29**.
- **Mô tả thêm:**
  - patch rỗng giảm từ 62 xuống 21;
  - số bước trung bình tăng từ 12,0 lên 18,4;
  - trong 79 patch không rỗng của nhánh có skill, L cho qua 79, S cho qua 53, nên bộ chấm lỏng vẫn thổi phồng thêm 26 điểm.

**Phân tích thêm sau khi có dữ liệu (thăm dò, KHÔNG đăng ký trước; R5):**
- **Lộ đáp án trong môi trường SWE-smith:**
  - Nhánh task mà agent làm việc có lịch sử `Initial commit` → `Bug Patch` → `Remove F2P Tests`, tức commit gây lỗi nằm ngay dưới HEAD. Đã kiểm trên mirror `swesmith/pallets__jinja.ada0a9a6`.
  - Skill học được viết rõ: *"Check Git History: If the issue description is empty … Run `git log -n 5` to identify suspicious recent commits (e.g., "Bug Patch"), then use `git show <commit_hash>` … Revert or fix these specific regressions."*
- **Đo:**
  - Trong 53 patch resolved của nhánh có skill, **29** là bản hoàn tác đúng từng dòng của commit "Bug Patch". Nhánh không skill có 6/15. ~~Đây là cận dưới của việc dùng chỗ lộ.~~ **Sai, xem A96 ở kết quả bước 3: bản hoàn tác đúng từng dòng xuất hiện cả khi không có chỗ lộ.**
  - Phần resolved **không** phải hoàn tác đúng từng dòng: 24 (có skill) so với 9 (không skill).
  - Đây là cận dưới của việc dùng chỗ lộ, vì agent có thể dùng một phần. Trajectory của bước chấm không được lưu, nên không đo được việc gọi `git log`/`git show`.
- **Diễn giải (thăm dò):**
  - Ít nhất một phần lớn mức tăng trong scope đến từ việc skill học cách khai thác một đặc điểm của môi trường đánh giá (commit gây lỗi bị lộ), chứ không phải tri thức về jinja.
  - Phần còn lại gồm sửa định dạng của agent (ít patch rỗng hơn) và tri thức thật về repo (mục 4 của skill).
  - Hệ quả có thể kiểm: trên task tự nhiên (không có commit "Bug Patch"), phần khai thác chỗ lộ không thể chuyển giao. Điều này phải đăng ký trước khi đo.

### §25 bước 3: cùng skill, ngoài scope (môi trường không lộ commit gây lỗi) (@thuthuy 06/11/2026: "Ok, duyệt ngoài scope"; khoảng 3,5 USD; đăng ký trước khi chạy)

**Lý do:** phân tích thăm dò của bước 2 cho thấy ít nhất 29/53 bản vá resolved là bản hoàn tác commit "Bug Patch" bị lộ trong lịch sử git. Bước 3 kiểm điều đó bằng một thí nghiệm, thay cho phân tích sau khi có dữ liệu.

**Thiết kế:**
- **Can thiệp duy nhất: lịch sử git.** Ngay sau `setup_task` của gskill, trong container **của agent**, chạy `LEAK_FREE_SH` (`scripts/f1_probe.py --leak-free`):
  - thay lịch sử bằng **một commit không có cha**, chứa đúng cây có lỗi;
  - xóa mọi ref khác, remote `origin`, `/opt/mirror.git` và reflog; chạy `git gc --prune=now`.
- **Kiểm sau khi viết lại** (bắt buộc; sai thì ghi `infra_error`): `commits=1 refs=1 remotes=0 objects_with_bug_msg=0`.
- **Container chấm điểm** vẫn mới cho mỗi lần chấm, như cũ. Chạy thử: bản gold tạo trong môi trường này được S cho resolved và L cho qua.
- **Hai nhánh mới**, cùng 100 task test, seed 41, cùng cấu hình F1 (cost_limit 0,30):
  - `none`: không skill;
  - `skill`: đúng skill của bước 2. Workflow kiểm `cmp` với `docs/skills/gskill/jinja_best_skills.txt`.
- **Trần:** nhánh none 1,9 USD; nhánh skill 2,4 USD.
  - Chi phí dự kiến: 1,44 + 1,94 ≈ 3,4 USD (theo F1 và bước 2).
  - Trần là chặn trường hợp xấu nhất ("đã chi + 0,30 > trần"). Nếu tổng thực tế vượt 3,5 USD thì báo @thuthuy.

**Đại lượng và quy tắc (cố định trước):**
- **δ_S^LF** = p_S(skill, LF) − p_S(none, LF), trong đó LF là môi trường không lộ (leak-free). Kiểm định dấu chính xác một phía trên cặp lệch, cho S và L; Holm, họ α = 0,025 (như bước 2).
- **Phần do chỗ lộ:** Δ_leak = δ_S(bước 2, có lộ) − δ_S^LF, kèm bootstrap 95% theo task (4 nhánh trên cùng 100 task). Báo cáo, không kiểm định.
- **Gatekeeper** trên Z_S^LF (θ = 0, α = 0,025, K = 1, theo thứ tự task): báo cáo có admit hay không, và ở trial nào.
- **Dự đoán viết trước (chỉ hướng):** δ_S^LF < 0,38; p_S(none, LF) ≤ 0,15.
- **Diễn giải viết trước:**
  - **LF1:** Holm bác bỏ được với S trong môi trường LF. Skill có tác dụng thật ngoài chỗ lộ; Δ_leak cho biết phần do chỗ lộ.
  - **LF2:** không bác bỏ được với S. Chứng nhận trong scope (bước 2, admit ở trial 29) **không chuyển** sang scope không lộ. Đây là một ví dụ đo được của "Scope before Reuse" trên skill thật.
- **Giới hạn ghi trước:** môi trường LF xóa luôn lịch sử thật của repo (commit `Initial commit` ban đầu), nên khác repo thật, vốn có lịch sử. Skill có mục "Check Git History"; trong LF, mục đó chỉ còn thấy 1 commit.

### Kết quả §25 bước 3: ngoài scope, không lộ commit gây lỗi (runs 42244574979, 42244580170; `results/s25_leakfree_{none,skill}.json`)

- **Chạy:** 100/100 task ở mỗi nhánh; 0 lỗi hạ tầng; kiểm môi trường không lộ đạt **200/200**.
- **Chi phí:** none 1,461 + skill 1,867 = **3,33 USD** (≤ 3,5 đã duyệt).

| Nhánh | Môi trường có lộ (bước 2 / F1) | Môi trường không lộ (bước 3) |
| --- | --- | --- |
| Không skill, S | 15/100 | 14/100 |
| Có skill, S | 53/100 | **35/100** |
| Không skill, L | 37/100 | 40/100 |
| Có skill, L | 79/100 | 66/100 |
| Patch rỗng (không skill / có skill) | 62 / 21 | 59 / 34 |

- **Kiểm định trong môi trường không lộ:**
  - S: b = 21, c = 0, p = 4,8·10⁻⁷.
  - L: b = 33, c = 7, p = 2,1·10⁻⁵.
  - **Holm bác bỏ cả hai, nên theo quy tắc đã đăng ký là LF1:** skill có tác dụng thật ngoài chỗ lộ.
- **Mức tăng S (bootstrap 95% theo task):**
  - có lộ: δ_S = +0,38 [0,26; 0,49];
  - không lộ: **δ_S^LF = +0,21 [0,13; 0,29]**;
  - **phần do chỗ lộ: Δ_leak = +0,17 [0,06; 0,28]**, tức khoảng 45% mức tăng trong scope.
- **Gatekeeper trên Z_S^LF:** admit ở **trial 50**; trong môi trường có lộ là trial 29.
- **Phân tích phụ theo problem statement** (đã đăng ký ở ghi chú 25-1):

  | Nhóm | Không skill (lộ / không lộ) | Có skill (lộ / không lộ) |
  | --- | --- | --- |
  | 66 task có problem statement | 14 / 14 | 38 / 35 |
  | 34 task problem statement rỗng | 1 / 0 | **15 / 0** |

  - Toàn bộ mức tăng trên 34 task không có mô tả lỗi đến từ chỗ lộ: 15 → 0 khi bỏ chỗ lộ.
  - Trên 66 task có mô tả, mức tăng gần như giữ nguyên (+24 → +21) khi bỏ chỗ lộ.

**Sửa một nhận định thăm dò của bước 2 (A96):** câu "ít nhất 29/53 bản vá resolved là bản hoàn tác commit bị lộ, nên là cận dưới của việc dùng chỗ lộ" là **sai**. Trong môi trường không lộ, 18/35 bản vá resolved của nhánh có skill (và 7/14 của nhánh không skill) vẫn là bản hoàn tác đúng từng dòng, vì lỗi SWE-smith là thay đổi nhỏ và sửa đúng thì trùng với hoàn tác. Chỉ số này vì vậy không đo được việc dùng chỗ lộ. Con số đúng là Δ_leak đo bằng thí nghiệm ở trên.

### §25 bước 4: lặp lại toàn bộ chuỗi cho repo thứ hai, Bleve (Go) (@thuthuy 06/11/2026: "Chọn cả bleve và Memgovern, ngân sách mới là 40 đô"; đăng ký trước khi chạy)

**Lý do:** vá điểm yếu "gskill mới làm trên một repo". Bleve là repo thứ hai trong blog của gskill, với mức tăng lớn nhất được báo (24% → 93%). F0 trên Bleve đã có: L(no-op) = 30/30, S(no-op) = 0/30.

**Thiết kế:** giống hệt jinja (§25 F1, bước 2, bước 3); chỉ đổi repo:
- `--repo blevesearch__bleve`; cách chia của gskill (seed 42, 200/50/100), dữ liệu `swesmith_blevesearch__bleve.jsonl.gz`;
- image `swebench/swesmith.x86_64.blevesearch_1776_bleve.f2876b5e`, kèm mirror các nhánh task.
- 42/100 task test có problem statement rỗng (jinja: 34/100).
- Các file kết quả có tiền tố `s25bleve_`, nên không ghi đè kết quả jinja.

**Các bước và trần** (mỗi bước chạy với `--cap`; cộng dồn cả track Bleve ≤ 25,5 USD; dự kiến khoảng 20 USD theo số đo của jinja):

| Bước | Nội dung | Trần |
| --- | --- | --- |
| 4a | Nhánh không skill, môi trường có lộ (như F1) | 2,0 |
| 4b | Học skill (mã gskill, hai nửa, dừng sớm nếu `num_candidates == 1`) | 16,0 cộng dồn |
| 4c | Chấm skill, môi trường có lộ | 3,2 |
| 4d | Môi trường không lộ: none / skill | 1,9 / 2,4 |

**Quy tắc:** như jinja.
- Bước 4c: A/B/C, theo kiểm định dấu chính xác một phía và Holm, họ α = 0,025.
- Bước 4d: LF1/LF2.
- Ngoài ra: Δ_leak có bootstrap, Gatekeeper với θ = 0, α = 0,025, K = 1, và phân tích phụ theo problem statement.
- **Không gộp** với jinja trong kiểm định; báo cáo theo từng repo.

**Ngân sách 40 USD:** Bleve chạy trước. MemGovern dùng phần còn lại = 40 − (chi thật của Bleve). Nếu phần còn lại không đủ cho thiết kế MemGovern đã ước, thì báo @thuthuy trước khi chạy MemGovern.

**Chạy thử miễn phí trên Bleve** (06/11):
- `setup_task` → môi trường không lộ (`commits=1 refs=1 remotes=0`) → agent giả lập → `no_patch`, chi phí được ghi.
- Bản gold tạo trong môi trường không lộ: S resolved, L qua.
- Phần đặt biến theo repo của workflow được chạy thử cho cả jinja và bleve.

### Ô memgovern: ghi chú thực thi M-1 (06/11/2026; @thuthuy: "Chọn cả bleve và Memgovern, ngân sách mới là 40 đô", "Xác nhận để trial chạy"; trước mọi lần chạy có phí của ô này)

- **Thiết kế giữ nguyên như đã đăng ký** (§3, §4, §5, §11e):
  - bản gốc (agent tự gọi `exp_search`/`exp_read`; F1–F6 và F4b đạt ở lần thử 7);
  - 109 task E2, theo thứ tự seed 41 của E2;
  - ghép với nhánh `none` seed 41 của E2 **nếu** §5 đạt;
  - Gatekeeper với α_ô = 0,025/9 (K = 9), kiểm sau mỗi lô và dừng ngay khi admit;
  - kiểm chi phí sau 10 trial đầu.
- **Chỉ thay ngân sách:** trần của ô = 40 USD − (chi thật của track Bleve), thay cho 20 USD. Quy tắc kiểm chi phí: sau 10 trial, nếu chi phí trung bình × 109 vượt phần trần còn lại thì dừng ô.
- **§5 viết lại** (`scripts/model_unchanged_check.py`), vì script của ngày 04/11 không còn trong lịch sử repo (repo được tạo lại ngày 06/11):
  - gửi lại lời gọi đầu tiên của agent cho 109 task bằng `LitellmModel` của mini-swe-agent 2.4.6, với `model_name` và `model_kwargs` ghi trong trajectory E2, **hai lần**;
  - so tên và đối số của tool call cùng nội dung, và trường `model` của phản hồi;
  - quy tắc như draft §10: ghép chỉ khi **mọi** task đạt cả hai bước.
  - Trajectory lấy từ `raw-archive` (`g2-e2-s41-*`, nhánh `none`). Chi phí ước khoảng 0,1 USD (218 lời gọi, khoảng 1.400 token vào mỗi lời gọi).
- **Nếu §5 không đạt:** theo §5 phải chạy cả hai nhánh mới, ước khoảng 21 USD, có thể vượt phần trần còn lại. Khi đó báo @thuthuy trước khi chạy.

### Ô memgovern: kết quả §5 (06/11/2026)

- **Hai lần chạy đầu không ra kết quả:**
  - run 42294432522 thiếu gói `mcp` (A97, không tốn tiền);
  - run 42296379214 chọn sai quỹ đạo của 3 task được chạy lại (A98, tốn 0,0118 USD).
- **Run 42297492582** (`results/model_unchanged_check_run42297492582.json`) trên 109 task:
  - bước 1 (hai lần gọi mới giống nhau): 107/109;
  - bước 2 (trùng E2): 75/109;
  - trường `model`: 109/109;
  - **`pair_with_e2 = false`**; chi phí 0,104 USD.
- **Run thứ 4** (`results/model_unchanged_check.json`) có lưu kèm các câu trả lời được so (`sig_e2`, `sig_new`):
  - bước 1: 107/109; bước 2: 74/109; trường `model`: 109/109; `pair_with_e2 = false`; chi phí 0,095 USD;
  - 108/109 task giữ cùng trạng thái trùng hay lệch E2 như ở run 42297492582;
  - cả 35 task lệch đều gọi một **lệnh khác**, không chỉ khác khoảng trắng. Ví dụ, E2 gọi `find . -maxdepth 2 -not -path '*/.*'`, nay model gọi `ls -R`.
- **Phán quyết theo quy tắc đã đăng ký (R5): không ghép với E2.** Nếu chạy ô memgovern thì phải chạy cả hai nhánh mới.
- **Diễn giải:**
  - Với cùng tên model, cùng seed và cùng prompt, model ngày 06/11 vẫn gần như tất định (107/109). Nhưng nó khác hành vi của model ở E2 trên khoảng 32% câu trả lời đầu tiên (35/109).
  - Trường `model` của phản hồi **không** phát hiện được thay đổi này (109/109 trùng).
  - Hệ quả cho paper: ghép một nhánh mới với một nhánh cũ chỉ dựa trên tên model là không an toàn. Phép kiểm §5 cần thiết, và đã bắt được sự thay đổi.
- **Ngân sách:** chạy cả hai nhánh ước khoảng 21 USD. Theo M-1, trước khi chạy phải báo @thuthuy, kèm số Bleve chi thực tế.
- **Quyết định của @thuthuy (06/11):** "Có thể bổ sung từ 7 đến 10 đô nếu thiếu". Trần của ô = 50 USD − (chi thật của track Bleve). Phần vượt 40 USD chỉ dùng khi cần. Thiết kế giữ nguyên: hai nhánh mới (`none` và memgovern) trên 109 task theo thứ tự E2, cùng seed 41 và cấu hình như E2, Gatekeeper α_ô = 0,025/9.

### Ô memgovern: ghi chú thực thi M-3 (06/11/2026, trước mọi lần chạy có phí của ô; chưa xem kết quả nào của ô)

- **Hai nhánh mới**, theo §5 khi phép kiểm không đạt:
  - `none` và `memgovern` (bản gốc) trên 109 task E2, theo thứ tự seed 41 của E2 (`model_unchanged_check.e2_tasks`);
  - cấu hình như E2: mini-swe-agent 2.4.6, seed model 41, `cost_limit` 1 USD, 250 bước, harness SWE-bench-Live `ad79b85`, 2 worker, chạy song song 2 nhánh;
  - server của MemGovern loại thẻ của mọi repo trong pool E2, như lần thử 7;
  - ghim chromadb 1.5.9 và Qwen3-Embedding-0.6B bản `97b0c614`, đúng phiên bản lần thử 7 đã ghi lại (đạt F1–F6 và F4b).
- **Trial và Z:**
  - Z = 1[không giải | memgovern] − 1[không giải | none] (`analyze_g1_final.z_resolved`);
  - e-process BettingEProcess với θ = 0, c = 0,5, α_ô = 0,025/9;
  - đưa Z vào theo thứ tự E2, trên **tiền tố dài nhất đã chạy xong** của thứ tự đó. Thứ tự đặt cược vì vậy cố định trước, không phụ thuộc shard nào xong trước;
  - task đã chạy nhưng không có cặp (lỗi hạ tầng) bị bỏ qua, như ở E1/E2 (`scripts/memgovern_cell.py`).
- **Lô và quy tắc dừng** (như đã đăng ký: kiểm sau mỗi lô, dừng ngay khi admit; kiểm chi phí sau 10 trial):
  - lô 1 là task 0–9 (10 task). Sau lô 1 kiểm chi phí: nếu chi tới lúc đó + (chi trung bình mỗi task × số task còn lại) > trần của ô thì dừng ô và báo @thuthuy;
  - các lô sau mỗi lô 20 task: 10–29, 30–49, 50–69, 70–89, 90–108 (lô cuối 19 task). Sau mỗi lô tính lại cả hai quy tắc dừng;
  - **Lý do chọn 20 task mỗi lô** (vận hành, không phải con số khoa học): đó là số job chạy song song tối đa của GitHub Actions gói Free, đã dùng cho E2 (`e2-shards.yml`). Mỗi shard chạy đúng 1 task, nên khi chạy tiếp, task nào thuộc shard nào không đổi.
  - Kích thước lô chỉ ảnh hưởng chi phí khi dừng sớm (tối đa thừa một lô). Nó không ảnh hưởng tính hợp lệ: theo bất đẳng thức Ville, dừng ở bất kỳ thời điểm nào vẫn giữ mức sai ≤ α_ô.
- **Trần ngân sách và chạy song song với Bleve:**
  - trần của ô (`cap_usd`) = 50 − 25,5 = **24,5 USD**;
  - 25,5 USD là chi tối đa của track Bleve nếu chạm mọi trần (4a 2,0 + 4b 16,0 + 4c 3,2 + 4d 1,9 + 2,4), nên tổng hai track luôn ≤ 50 USD, kể cả khi hai track chạy cùng lúc;
  - mỗi task giữ trước chi phí xấu nhất (2 nhánh × 1 USD) trong sổ cái `mg-ledger` (cơ chế của E2, A60);
  - phép kiểm §5 (0,21 USD) tính vào phần 40 USD.
- **Không phân phối lại nội dung MemGovern:**
  - `scripts/redact_memgovern.py` thay hướng dẫn của MemGovern và mọi quan sát chứa thẻ bằng dấu `<<MEMGOVERN_TEXT sha256=…>>`;
  - sau đó script kiểm rằng không file nào còn cửa sổ 60 ký tự của thẻ nào được tham chiếu. Nếu còn, file gốc không được tải lên (fail closed).
- **Bộ lọc thẻ cùng repo (kiểm 06/11, A100):** 48 repo của MemGovern không trùng repo nào trong 61 repo của pool E2, nên bộ lọc không loại thẻ nào (121.475 thẻ). Quy tắc vẫn giữ nguyên; điều này ghi vào paper như một sự thật về dữ liệu, không phải một thay đổi.

### Ô memgovern: sai lệch M-4 (07/11/2026 UTC, sau lô có phí 1, trước mọi phân tích Gatekeeper của ô)

- **Đã thấy gì** (chỉ dữ liệu vận hành, chưa tính Z hay E):
  - ở lô 1 (task 0–9, nhánh memgovern bản 1), model gọi `exp_search`/`exp_read` 0 lần trên 10/10 task (A102);
  - chi phí lô 1 là 2,19 USD theo litellm.
- **Thay đổi:** nhánh memgovern **bản 2** (`configs/skills/memgovern-orig-wf.json`).
  - Cùng đoạn văn bản của MemGovern (bước 3 của cấu hình gốc và docstring của 2 công cụ), cùng server, cùng công cụ, cùng bộ lọc thẻ.
  - Nhưng đoạn đó được chèn làm **bước 3 của "Recommended Workflow" của mini-swe-agent**, và bước sửa mã thêm "(Apply insights from step 3 if available)". Đây đúng là vị trí và lời của cấu hình gốc (`config/dsv31t_agenticMemSearch_1220_13w.yaml`, các bước 1–6).
  - Mô tả issue giữ nguyên như nhánh `none`.
- **Lý do:** §11e định nghĩa "bản gốc" là dùng đúng đoạn hướng dẫn trong cấu hình agent của MemGovern, với agent tự gọi công cụ. Bản 1 đặt đoạn đó sai chỗ so với bản gốc. Vậy đây là sửa một lỗi hiện thực (A102) về phía thiết kế đã đăng ký, không phải đổi câu hỏi.
- **Thiết kế của ô bản 2:**
  - chạy lại từ task 0, **cả hai nhánh mới** (tên lô `mg2-s41-*`), cùng thứ tự, cùng các quy tắc dừng của M-3;
  - không dùng lại nhánh `none` của lô 1. Lý do: §5 vừa cho thấy model thay đổi theo thời gian, nên hai nhánh của một cặp phải chạy cùng lúc. Dùng lại sẽ rẻ hơn khoảng 1,1 USD nhưng hai nửa của cặp chạy ở hai thời điểm.
- **Quy tắc báo cáo (R5):** lô 1 (bản 1, 10 cặp) được giữ và báo cáo riêng, như một bằng chứng về độ nhạy với vị trí của hướng dẫn. Nó không vào e-process của ô bản 2.
- **Phép kiểm thao tác (chốt trước khi thấy dữ liệu bản 2):**
  - sau lô đầu của bản 2 (task 0–9), nếu **0/10** task có ≥ 1 lệnh `exp_search` thì dừng ô và báo @thuthuy, vì nhánh vẫn không phân biệt được với "hướng dẫn không được dùng";
  - nếu ≥ 1/10, chạy tiếp theo M-3;
  - tỉ lệ dùng công cụ được báo cáo cho mọi task.
- **Trần:**
  - phép kiểm §5 (0,21 USD) và lô 1 (2,19 USD, đã ghi trong sổ cái `mg-ledger`) tính vào trần;
  - `cap_usd` của sổ cái = 24,5 − 0,21 = **24,29 USD**. Sổ cái đã có 2,19 USD của lô 1, nên tổng của track MemGovern ≤ 24,5 USD;
  - khi Bleve xong, trần được tính lại theo M-3: 50 − chi thật của Bleve.

### Ô memgovern: kết quả phép kiểm thao tác M-4 (07/11/2026 UTC), ô dừng

- **Lô 1 của bản 2** (run 42315998541, task 0–9, `mg2-s41-*`):
  - bước MemGovern nằm đúng trong workflow của agent ở 10/10 task, và không nằm trong mô tả issue;
  - **0/10 task có lệnh `exp_search` hay `exp_read`**; server ghi 0 lời gọi;
  - trong các tin nhắn của agent không có lần nào nhắc "exp_search", "exp_read" hay "experience";
  - bước che nội dung không thay tin nhắn nào của agent;
  - lệnh đầu tiên luôn là `ls` hoặc `find`, tức bước 1 của workflow.
- **Cộng cả bản 1:** 0/20 lượt chạy của nhánh memgovern dùng công cụ, ở hai vị trí đặt hướng dẫn.
- **Theo quy tắc chốt trước ở M-4: ô dừng.** Chưa tính Z hay e-process nào của ô.
- **Token** (đếm từ `usage` của API, cả hai nhánh, trên 10 task mỗi bản):

  | Bản | Nhánh | Input | Cache | Output |
  | --- | --- | --- | --- | --- |
  | 1 | memgovern | 14.412.115 | 13.216.858 | 54.732 |
  | 1 | none | 34.097.461 | 32.042.944 | 84.492 |
  | 2 | memgovern | 29.315.599 | 27.208.694 | 78.741 |
  | 2 | none | 32.729.242 | 29.886.393 | 88.605 |

- **Chi phí** (USD, chỉ để kiểm soát ngân sách): phép kiểm §5 0,21; bản 1 2,15; bản 2 2,92. Tổng track MemGovern **5,28 USD**.
- **Diễn giải:**
  - Với model của thí nghiệm, bước tìm kinh nghiệm "optional, as needed" của MemGovern **không bao giờ được dùng** trong 20 lượt chạy. Vậy trên harness này, nhánh MemGovern gốc không khác nhánh không skill ở hành vi dùng công cụ.
  - Gatekeeper trên ô này không có thông tin: Z chỉ phản ánh tác động của phần văn bản thêm vào prompt.
  - Hướng đi tiếp theo là việc thêm hoặc đổi thí nghiệm, thuộc quyền @thuthuy.
- **Quyết định của @thuthuy (07/11/2026): "Dừng memgorven".**
  - Ô memgovern đóng ở đây; không chạy B-M, không chạy bản bắt buộc tìm kinh nghiệm.
  - Báo cáo trong paper: 0/20 lượt chạy dùng công cụ, kèm token, và lô bản 1 riêng.
  - Track MemGovern đã chi 5,28 USD. Phần bổ sung 7–10 USD (dành cho MemGovern) không dùng.
  - Track Bleve giữ các trần của §25 bước 4 (tối đa 25,5 USD), trong phần 40 − 5,28 = 34,72 USD.

### §25 bước 4 (Bleve): kết quả 4a và 4b nửa 1 (07/11/2026)

- **4a** (run 42292893852, nhánh không skill, 100 task test của gskill):
  - S (thang chấm SWE-smith) 13/100; L (thang chấm gskill) 30/100;
  - 70 task không có patch;
  - 0 lỗi hạ tầng, 0 lần crash;
  - chi 0,786 USD (trần 2,0).
- **4b nửa 1** (run 42292899150):
  - `num_candidates` = 6, `total_metric_calls` = 354, `best_score` 0,86 (điểm của chính gskill trên tập val);
  - skill tốt nhất dài 3.009 ký tự;
  - chi 5,701 USD (trần cộng dồn 16,0).
  - **Theo quy tắc dừng sớm (6 > 1): chạy nửa 2.** Run được dispatch ngày 07/11 với `--resume` và trần cộng dồn 16,0.
- **4b nửa 2** (run 42328337599):
  - `num_candidates` = 10, `total_metric_calls` = 626;
  - `best_score` vẫn 0,86: skill tốt nhất **không đổi** so với nửa 1 (3.009 ký tự, `docs/skills/gskill/bleve_best_skills.txt`);
  - chi nửa 2 4,745 USD. **Cộng dồn bước học 10,446 USD** (trần 16,0).
- **Quan sát về skill học được** (đọc văn bản, chưa chấm):
  - dòng 36 của skill viết: "If the issue description is missing or vague, inspect the target file carefully for obvious logical errors or look at recent git commits (`git log -p -n 3`) to deduce what broke";
  - đây là cùng loại chỉ dẫn như skill jinja ("Check Git History… 'Bug Patch'"), xuất hiện lại trên một repo khác, viết bằng ngôn ngữ khác (Go);
  - bước 4c và 4d sẽ đo xem chỉ dẫn này có được dùng không, và đóng góp bao nhiêu.
- **Tiếp theo:** 4c (chấm skill trên 100 task test, trần 3,2 USD), rồi 4d.

## 26. Mục 2.3: chọn model thứ hai (07/11/2026, trước mọi lần chạy agent với model này)

- **Quy tắc chọn** (nêu trước khi có giá hay số đo nào):
  1. **Điều kiện bắt buộc:** kênh gọi tính theo token (MaaS, serverless), không thuê máy chủ theo giờ; gọi tool song song.
  2. **Ưu tiên** model có trọng số mở.
  3. **Phá hòa** bằng giá đã kiểm trên trang chính thức, tính theo hồ sơ token đo được (91% input là cache, output khoảng 0,3% so với input).
- **Hai điều chỉnh trước khi có dữ liệu agent nào:**
  - "Nhận seed" không còn là điều kiện bắt buộc, theo `docs/model_switch_checklist.md` mục B4: nếu API bỏ qua seed, paper phải ghi seed chỉ là nhãn của lần lặp.
  - "Ngữ cảnh ≥ 131k token" chuyển thành điều kiện phải báo cáo, theo mục B6: lời gọi lớn nhất đo được trên 2.748 lời gọi gần nhất là 77.997 token, và chỉ 1/1.071 lượt chạy pilot vượt 128k.
- **Kiểm tài khoản** (`vertex-check.yml`, ngày 07/11, tổng chi phí < 0,01 USD):
  - Qwen, DeepSeek, Llama: chỉ có dạng thuê máy chủ theo giờ trên project này. **Loại.**
  - Claude Haiku 5.5: bật được, nhưng hạn mức `global_online_prediction_requests_per_base_model` (anthropic-claude-haiku) bằng 0, và Google **từ chối** yêu cầu tăng. **Loại.** Ghi thêm: API không nhận seed.
  - Grok 4.1 Fast: Google đã ngừng phục vụ từ 20/08/2026. **Loại.**
  - Codestral 2: LiteLLM không hỗ trợ tool cho model này. **Loại.**
  - Grok 4.20 Non-Reasoning: gọi được và gọi được 2 tool song song. Nhưng đang ở trạng thái EXPERIMENTAL, và khoảng 0,97 USD mỗi lượt (input 1,25, cache 0,20, output 2,50). Riêng mục 2.4 đã khoảng 200 USD. **Không chọn.**
  - Mistral Small 3.1 (25.03): trọng số mở; input 0,10, output 0,30, không ghi giá cache, nên khoảng 0,33 USD mỗi lượt. Hiện báo 404 (chưa có quyền truy cập).
- **Quyết định của @thuthuy (07/11): "theo lời khuyên của bạn".**
  - Xin quyền Mistral Small 3.1 (phương án A).
  - Nếu bị từ chối: dùng Gemini Flash (phương án C). Khi đó paper chỉ được viết "trong họ Gemini".
- **Ngân sách mục 2.3:** đã duyệt khoảng 1 USD. Ước tính 5 task × 2 nhánh với Mistral là khoảng 3,3 USD. Đề xuất nâng lên 3,5 USD, đang chờ @thuthuy.

## 27. Ba phép thử trên skill jinja: placebo, dùng lại ở repo khác, quỹ đạo (đăng ký 07/11/2026, trước mọi lần chạy có phí; trần 7 USD)

**Quyết định của @thuthuy (07/11):**
- "Ok, lên 7usd vẫn được, chọn phương án tốt nhất cho paper".
- "lưu ý là dùng của người ta không chỉnh sửa gì để chắc chắn mình k can thiệp vào chiến thắng".

**Quy tắc chung rút từ yêu cầu thứ hai:**
- Mọi nhánh chạy trong **môi trường gốc của gskill**: không dùng `--leak-free`, không đổi image hay lịch sử git.
- Skill jinja học được và skill placebo được dùng **nguyên văn**, kiểm bằng `cmp` và `sha256sum -c` trước khi chạy.
- Vì vậy thí nghiệm bỏ một phần skill (P24, cắt một dòng khỏi skill của gskill) **bị bỏ**.
- Phần đổi duy nhất, áp như nhau cho mọi nhánh: seed 41 và trần 0,30 USD mỗi lượt (`docs/reviewer_fidelity.md` A2, A3).

### 27a. Đối chứng placebo cùng độ dài (2a), trần 2,2 USD
- **Can thiệp (R2, nhóm "định nghĩa can thiệp" có nguồn):** đối chứng C2 của WebDev-Skills-Bench (arXiv 2608.23067): thay skill bằng một skill **không liên quan** có độ dài byte trong ±5%.
  - Nguyên văn (bản chụp `sources-snapshots`, `webdev_skills_bench_2026`): *"C2 (length-matched irrelevant Skill) replaces the target SKILL.md with a skip-tier Skill of approximately equal byte length (±5%), which separates the target-content effect from the effect of adding a length-matched Skill block and gives ∆Length = C2−C0 and ∆Content = C1−C2."*
  - Ánh xạ sang §27: C0 là `f1_probe` (không skill), C1 là `f1_skill_probe` (skill jinja), C2 là nhánh placebo. **P27a đo ∆Content; phép phụ đo ∆Length.**
- **Chọn skill placebo bằng quy tắc, không có lựa chọn tự do:**
  - nguồn: 98 skill công khai của SWE-Skills-Bench@4d3450d (MIT);
  - điều kiện: độ dài trong ±5% của skill jinja (2.681 byte, tức 2.547–2.815);
  - **đúng một skill thỏa:** `skills/go-concurrency-patterns/SKILL.md` (2.771 byte; Go, không liên quan tới jinja);
  - sha256 `a66d04f2…b36b2`, lưu ở `docs/skills/swe_skills_bench/`.
- **Thiết kế:** 100 task test của jinja, theo thứ tự `_gskill_order`, cấu hình như §25.
- **So sánh:**
  - skill thật: `results/f1_skill_probe.json` (S 53/100);
  - không skill: `results/f1_probe.json` (S 15/100);
  - cả hai cùng môi trường gốc, chạy ngày 06/11.
- **Phép kiểm chính P27a** (một phía, α = 0,025): skill thật > placebo. Kiểm định dấu chính xác trên cặp lệch theo task, endpoint S.
- **Phụ:**
  - placebo so với không skill (hai phía, mô tả);
  - cùng phép kiểm P27a trên **nhóm có mô tả issue** (66 task), nơi rò rỉ gần như không có tác dụng (§25: 15 → 0 chỉ ở nhóm không có mô tả).
- **Giới hạn đã biết:** nhánh placebo chạy sau hai nhánh so sánh khoảng 1 ngày. §5 cho thấy model có thể đổi theo thời gian. Phép thử 27c đo trực tiếp mức lặp lại của nhánh skill sau 1 ngày, để báo cáo kèm.

### 27b. Dùng lại skill jinja ở repo khác (2b), trần 3,6 USD
- **Chọn repo bằng quy tắc:** `pygments__pygments`, là repo mặc định trong README của gskill (§25, mục F0).
  - F0 trên repo này: patch không làm gì đạt S 0/30; bản sửa gốc đạt S 29/30; 0 lỗi hạ tầng.
- **Thiết kế:**
  - 100 task test của pygments, chia theo đúng cách của gskill (`data/instances/swesmith_pygments__pygments.jsonl.gz`, seed 42);
  - hai nhánh, không skill và skill jinja nguyên văn, **chạy song song trong cùng một job**, để hai nửa của mỗi cặp chạy cùng thời điểm;
  - mỗi nhánh trần 1,8 USD.
- **Phép kiểm chính P27b** (hai phía, α = 0,025, vì cả "có hại" và "có ích" đều là kết quả có ý nghĩa): skill jinja khác không skill. Kiểm định dấu chính xác trên cặp lệch, endpoint S.
- **Phụ:**
  - Gatekeeper trên ô (skill jinja, pygments) với θ = 0, c = 0,5, α = 0,025: admit hay không;
  - nhóm có mô tả issue (92 task); pygments chỉ có 8 task không có mô tả.

### 27c. Quỹ đạo của skill jinja trên 34 task không có mô tả issue (2c), trần 0,8 USD
- **Thiết kế:** 34 task test của jinja có `problem_statement` rỗng; skill jinja nguyên văn; môi trường gốc; lưu mọi tin nhắn (A104).
- **Đại lượng** (định nghĩa trước khi xem quỹ đạo):
  - **G1:** số task có ít nhất một lệnh agent chạy chứa `git log` hoặc `git show`;
  - **G2:** số task có quan sát chứa chuỗi "Bug Patch";
  - **G3:** tỉ lệ giải (S) khi có G2 và khi không có G2.
- **Độ lặp lại** (thay cho phép kiểm drift, vì quỹ đạo cũ đã mất): trên 34 task, so S và patch với `results/f1_skill_probe.json` (06/11), báo số task cùng S và số task có patch giống hệt.

**Họ phép kiểm:** P27a và P27b, Holm ở mức 0,025. 27c chỉ mô tả.
**Tổng trần: 6,6 USD**, trong mức 7 USD. Thứ tự chạy: chạy thử miễn phí (`dryrun`) cho cả ba, rồi 27c, 27a, 27b. Bleve 4c/4d vẫn theo §25.

### §25 bước 4c (Bleve): kết quả chấm skill (run 42342066372; `results/s25bleve_skill_probe.json`; nhánh không skill là 4a)
- **Chạy:** 100/100 task; 0 lỗi hạ tầng; 0 lần crash; chi 1,724 USD (trần 3,2).
- **Phân tích theo quy tắc đã đăng ký** (`scripts/s25_ab.py`). Trước khi dùng, script được kiểm lại trên jinja và tái hiện đúng: 53/15, 44/6, p = 1,6·10⁻⁸, L 49/7, A, admit ở trial 29.

| Bộ chấm | Có skill | Không skill | b / c | p một phía | Mức tăng, bootstrap 95% |
| --- | --- | --- | --- | --- | --- |
| **S** | **43/100** | 13/100 | 34 / 4 | 3,0·10⁻⁷ | **+0,30** [0,19; 0,40] |
| L | 73/100 | 30/100 | 48 / 5 | 3,5·10⁻¹⁰ | +0,43 [0,31; 0,54] |

- **Holm (họ 0,025):** bác bỏ cả S lẫn L. **Kết quả: A.** **Gatekeeper admit ở trial 34.**
- **Nhóm theo mô tả issue (mô tả, không phải phép kiểm đăng ký):**
  - không có mô tả (42 task): S 11 so với 0 (b/c 11/0);
  - có mô tả (58 task): S 32 so với 13 (b/c 23/4).
  - Cùng hình mẫu với jinja (nhóm không có mô tả: 15 so với 1): skill lại chứa chỉ dẫn đọc git (`git log -p -n 3`).
- **Chi phí Bleve đến giờ:** 4a 0,786 + học 10,446 + 4c 1,724 = **12,956 USD.**
- **4d giữ nguyên như đã đăng ký** (07/11, sau trao đổi với @thuthuy: "số tiền đó tôi không tiếc nhưng nếu không làm paper mạnh thêm thì thôi").
  - Lý do giữ: phân tích theo nhóm "có / không có mô tả issue" ở trên chỉ là quan sát, có thể bị nhiễu bởi độ khó khác nhau giữa hai nhóm. 4d là can thiệp trên cùng 100 task, cho Δ_leak đo trực tiếp trên repo thứ hai. Lần này có lưu quỹ đạo (A104).
  - 4d không đổi gì của gskill: skill, mã và cấu hình giữ nguyên; môi trường được đổi như nhau cho cả hai nhánh. Kết quả chính vẫn là kết quả trong môi trường gốc (4c); 4d báo cáo riêng (`docs/reviewer_fidelity.md` A5).
  - Thứ tự: chạy sau §27.

### §27: ghi chú thực thi 27-1 (07/11/2026)
- 27c dừng ở 25/34 task vì đặt trần thiếu (A107). 9 task còn lại chạy bằng nhánh `trace34b` (`--skip-done`, cùng cấu hình), trần 0,6 USD. Kết quả 27c là hợp của hai file.
- Tổng trần §27 thành 0,505 (đã chi) + 0,6 + 2,2 + 3,6 = 6,9 USD, vẫn trong mức 7 USD.
- **Kiểm trần cho các nhánh còn lại:** 27a cần khoảng 1,94 + 0,30 = 2,24 USD, nên nâng trần từ 2,2 lên **2,3**. 27b cần mỗi nhánh khoảng 1,4–1,9 + 0,30 ≤ 2,2 USD, nên nâng trần từ 3,6 lên **4,4**, tức 2,2 USD cho mỗi nhánh. Tổng trần §27 thành 0,505 + 0,6 + 2,3 + 4,4 = **7,8 USD**, vượt 7 USD. Nhưng chi dự kiến chỉ khoảng 0,505 + 0,18 + 1,94 + 3,3 ≈ **5,9 USD**: phần vượt chỉ là khoảng đệm cho lượt xấu nhất, không phải tiền dự kiến chi. Chi thật sẽ được báo, và dừng ngay nếu tổng chi thật của §27 sắp vượt 7 USD.

### Kết quả 27c (run 42362204332 cho 25 task và 42365104656 cho 9 task; `results/s27_trace34*.json`, `*.traces.jsonl.gz`)
- 34/34 task không có mô tả issue của tập test jinja; môi trường gốc của gskill; skill jinja nguyên văn; 0 lỗi hạ tầng; chi 0,753 USD.
- **G1 = 34/34:** agent chạy `git log` hoặc `git show` ở mọi task.
- **G2 = 34/34:** quan sát của agent chứa "Bug Patch" ở mọi task.
- **G3:** không tính được, vì không có task nào thiếu G2. S = 15/34 (đều có G2).
- **So với 06/11** (`f1_skill_probe`, cùng 34 task):
  - S 15/34 lúc đó, 15/34 bây giờ;
  - 30/34 task cùng kết quả S; 22/34 task có patch giống hệt;
  - nhánh không skill (F1) trên 34 task này: S 1/34.
- **Diễn giải (mô tả):**
  - Trên mọi task không có mô tả issue, skill học được dẫn agent tới đọc commit "Bug Patch". Đây là bằng chứng trực tiếp cho cơ chế mà §25 bước 3 suy ra từ Δ_leak.
  - Mức lặp lại 30/34 sau 1 ngày được báo cáo kèm phép so khác thời điểm của 27a.

### Kết quả 27a (run 42366671200; `results/s27_placebo.json`; phân tích `results/s27a_content.json`, `results/s27a_length.json`)
- 100/100 task; 0 lỗi hạ tầng; chi 1,051 USD. Placebo: S 24/100; 54 patch không rỗng.
- **P27a, ∆Content** (skill thật so với placebo, một phía): S 53 so với 24; b/c = 35/6; **p = 2,4·10⁻⁶**; +0,29 [0,18; 0,40].
  - p ≤ 0,0125 (mức đầu của Holm trên P27a và P27b), nên **bác bỏ H₀ bất kể P27b**.
- **Phụ:**
  - ∆Length (placebo so với không skill, hai phía): 24 so với 15; b/c = 16/7; p = 0,093; +0,09 [0,00; 0,18]. Không bác bỏ ở mức 0,025.
  - Nhóm có mô tả issue (66 task): ∆Content 38 so với 24 (b/c 20/6, p một phía 0,0047); ∆Length 24 so với 14 (b/c 16/6).
  - Nhóm không có mô tả (34 task): skill thật 15, placebo 0.
- **Diễn giải:**
  - Trong mức tăng +0,38 của skill gskill trên jinja, phần do "thêm một đoạn hướng dẫn dài" nhỏ và chưa có ý nghĩa thống kê (+0,09). Phần do nội dung là +0,29.
  - Phần nội dung vẫn có ý nghĩa trên nhóm có mô tả issue, nơi rò rỉ gần như không có tác dụng.
  - Ở nhóm không có mô tả, toàn bộ mức tăng đi cùng chỉ dẫn đọc git (27c: 34/34 task đọc "Bug Patch"); placebo đạt 0/34.
- **Giới hạn:** nhánh placebo chạy ngày 07/11, các nhánh so sánh chạy ngày 06/11. 27c cho thấy 30/34 task cùng kết quả khi chạy lại sau 1 ngày.

### Kết quả 27b (run 42374323315 cho cặp, 42393651143 cho 14 task bù, 42397649759 cho 7 task bù; `results/s27pyg_*_all.json`, `results/s27b_reuse.json`)
- **Hoàn tất:** 100/100 task ở cả hai nhánh.
  - Nhánh skill dừng sớm hai lần vì đặt trần thiếu (A108). 21 task được chạy bù bằng `--skip-done`, cùng cấu hình, cùng ngày; với các task này, hai nửa của cặp không chạy cùng lúc.
  - 4 lần bộ chấm báo `timeout` (A108) được chấm lại tại máy (`results/s27pyg_timeouts_rescore.jsonl`): 3 lần chấm xong, đều không giải được. 1 patch của nhánh không skill vẫn timeout, nên tính là không giải được trong phân tích chính (theo SWE-bench, A56) và bị bỏ ra trong phân tích độ nhạy.
- **Chi:** 1,324 + 1,902 + 0,607 + 0,135 = 3,968 USD. **Tổng §27: 0,753 + 1,051 + 3,968 = 5,772 USD** (mức duyệt 7 USD).
- **P27b** (skill jinja so với không skill trên pygments, hai phía, endpoint S): 6 so với 5; b/c = 2/1; **p = 1,0; không bác bỏ.** Mức chênh +0,01 [−0,02; 0,05].
- **Holm trên họ {P27a, P27b} ở mức 0,025:** P27a bác bỏ (p = 2,4·10⁻⁶ ≤ 0,0125). P27b không bác bỏ (p = 1,0 > 0,025).
- **Gatekeeper** (θ = 0, c = 0,5, α = 0,025): **không admit.** Cùng skill đó được admit trên jinja ở trial 29.
- **Bộ chấm L của gskill** (mô tả): 70 so với 42; b/c = 34/6; +0,28 [0,17; 0,39]. Theo bộ chấm lỏng, skill "mang sang được" pygments; theo bộ chấm SWE-smith thì không.
- **Phân tích độ nhạy** (bỏ task timeout, n = 99): S 6 so với 5, không đổi.
- **Nhóm theo mô tả issue:** có mô tả 92 task (6 so với 5); không có mô tả 8 task (0 so với 0).
- **Giới hạn:** tỉ lệ giải nền trên pygments rất thấp (5/100), nên phép kiểm có ít power để phát hiện tác hại.
- **Diễn giải:** một skill được chứng nhận ở scope của nó (jinja) không cho mức tăng đo được khi dùng lại ở repo khác (pygments), và Gatekeeper không chứng nhận nó ở đó. Bộ chấm lỏng của gskill sẽ báo sai một mức chuyển giao +0,28. Đây là một ví dụ trên skill thật của "Scope before Reuse".

### §25 bước 4d (Bleve): kết quả nhánh không rò rỉ (run 42399244153 cho nhánh none; 42414050530 và 42442262299 cho nhánh skill)
- **Hoàn tất:** 100/100 task ở cả hai nhánh. Kiểm rò rỉ cho "commits=1 refs=1 remotes=0 objects_with_bug_msg=0" ở mọi task.
  - Nhánh skill dừng ở 98 task vì trần (A109); 2 task chạy bù bằng `--skip-done`.
  - 1 lần bộ chấm báo `timeout`. Chấm lại tại máy vẫn timeout, nên tính là không giải được trong phân tích chính (A56).
- **Chi:** 0,773 + 2,124 + 0,023 = **2,920 USD** (trần 4,3). **Track Bleve tổng cộng: 12,956 + 2,920 = 15,876 USD.**
- **Kết quả** (`results/s25bleve_leakfree_ab.json`):

| Bộ chấm | Có skill | Không skill | b / c | p một phía | Mức tăng, bootstrap 95% |
| --- | --- | --- | --- | --- | --- |
| **S** | **31/100** | 14/100 | 19 / 2 | 1,1·10⁻⁴ | **+0,17** [0,09; 0,25] |
| L | 59/100 | 31/100 | 32 / 4 | 9,7·10⁻⁷ | +0,28 [0,18; 0,38] |

- **Holm:** bác bỏ cả S lẫn L. **Kết quả: A.** **Gatekeeper admit ở trial 61** (môi trường có rò rỉ: trial 34).
- **Δ_leak** (mức tăng có rò rỉ trừ mức tăng không rò rỉ, ghép cặp theo task): **+0,13 [0,03; 0,23]**, khoảng 43% của +0,30. Jinja: +0,17 [0,06; 0,28], khoảng 45%.
- **Nhóm theo mô tả issue:**
  - không có mô tả (42 task): 0 so với 0 (có rò rỉ: 11 so với 0);
  - có mô tả (58 task): 31 so với 14 (có rò rỉ: 32 so với 13).
- **Quỹ đạo** (A104): agent chạy `git log`/`git show` ở 31/100 task, và thấy "Bug Patch" ở 0/100 task.
- **Diễn giải:** trên một repo thứ hai, viết bằng ngôn ngữ khác (Go):
  - skill học được giúp thật khi không có rò rỉ;
  - khoảng 43% mức tăng đo trong môi trường gốc đến từ commit "Bug Patch";
  - toàn bộ phần đó nằm ở các task không có mô tả issue.
  - Cả hai đều lặp lại kết quả của jinja.


### Kết quả §23b sau D-M11 (06/11/2026; `results/sskb_s23b-flash-screen.json`)

- **Dừng theo cổng chi phí đã đăng ký:** sau 4 ô, trung bình 0,392 USD/ô > 0,15. Sàng lọc chưa đủ (1/6 cặp mỗi skill cho 2/5 skill), nên **không chọn skill và không xác nhận**. `select_confirm` dừng đúng với thông báo "screen incomplete".
- **Mô tả 2 cặp có được** (không kết luận):
  - `go-fx-di` b1: 1,00 so với 1,00;
  - `langsmith-fetch` b1: 1,00 so với 1,00.
  - Nhánh không skill đã đạt trần ở cả hai.
- **Kiểm sau khi chạy:** 4/4 `Submitted`, 0 lỗi hạ tầng.
- **Chi và token:** 1,568 USD; 6.011.743 token vào (5.074.200 cache), 129.006 token ra.
- **Bài học cho ước tính:** ước tính 0,075 USD/ô (token của §22 × giá) thấp hơn thật 3–10 lần. Với Flash, agent dùng nhiều lời gọi hơn và token suy luận chiếm phần lớn token ra.
- **Giai đoạn bỏ dở trước D-M11:** `viper` b1 nhánh không skill trên Flash, 0,480 USD (`runs/sskb-s23a/`); `go-fx-di` b1 nhánh không skill trên Flash-Lite, 0,030 USD (`runs/sskb-s23b/`). Không gộp vào giai đoạn nào.
- **Tổng §23:** 4,059 (23a Pro) + 1,568 (23b Flash) + 0,510 (bỏ dở) = **6,136 USD**.

## 26m. Kiểm bộ chấm: test PASS_TO_PASS hỏng do môi trường (đăng ký 06/11/2026, trước khi tính lại tác dụng nào; 0 USD)

**Đánh số:** §24 và §25 đã được dùng trên nhánh `trial`, nên mục này là §26 để không trùng. Sau đó nhánh `trial` cũng dùng §26 và §27, nên khi gộp (08/11/2026) các mục của nhánh này được đổi thành §26m, §27m, §28m (các ghi chú thực thi tương ứng: 26m-2, 27m-1, 27m-2, 28m-1, 28m-2). Tên file (`s28_*`) giữ nguyên.

**Đã thấy trước khi đăng ký** (chỉ số đếm, không phải tác dụng):
- Quét 1.911 báo cáo chấm điểm cục bộ (E1, pilot, T4): 76 lần chấm có mọi FAIL_TO_PASS qua nhưng không resolved, thuộc 26 instance.
- 17 instance có ít nhất một test PASS_TO_PASS trượt ở mọi lần chấm.
- T4 `conan-15705` (bản vá giống hệt bản gốc): FAIL_TO_PASS 1/1 qua; PASS_TO_PASS 5/3.650 trượt, cả 5 trong `list_test.py::TestListPrefs`.

**Vì sao:** endpoint resolved đòi **mọi** PASS_TO_PASS qua. Một test hỏng do môi trường của mình (mạng, thời gian, file hệ thống) làm task không thể giải ở **cả hai nhánh**. Hệ quả:
- tác dụng bị pha loãng;
- reviewer có thể nói kết quả null là lỗi harness.

**Ba endpoint (độ nhạy; phán quyết đã đăng ký giữ nguyên theo endpoint S):**
1. **S (strict):** `resolved` của harness, như đã đăng ký.
2. **F (chỉ FAIL_TO_PASS):** bản vá áp được, test đã chạy, và mọi FAIL_TO_PASS qua.
3. **B (bỏ test hỏng):** như S, nhưng bỏ các test PASS_TO_PASS **trượt ở mọi lần chấm** của instance đó (mọi nhánh, mọi seed). Chỉ áp cho instance có ≥ 3 lần chấm. Test hỏng được xác định không phụ thuộc nhánh, nên quy tắc không ưu ái nhánh nào.

**Đại lượng:** với E1 (từng skill), E2 (`xreposkill`) và T4 (`control-oracle-patch`): trung bình hiệu số resolved (có skill − không skill) trên các cặp cùng instance, cùng seed, theo S, F, B. CI 95% bootstrap theo task, 10.000 lần. Endpoint S phải khớp số đã báo; đây là phép kiểm cách đọc log.

**Chấm lại bản vá gốc (gold patch):**
- Áp cho các instance thuộc hợp của hai nhóm ở trên.
- Chạy harness 3 lần mỗi instance, bằng CPU, không gọi LLM. Con số 3 là vận hành: đủ để tách lỗi xác định (3/3) khỏi lỗi chập chờn (1–2/3) với chi phí CPU nhỏ.
- **Nhãn:** "môi trường hỏng" nếu gold trượt 3/3; "chập chờn" nếu 1–2/3; "ổn" nếu 0/3.
- **Giới hạn:** 3 lần không phát hiện được chập chờn hiếm.

**Diễn giải đặt trước:**
- Nếu tác dụng theo F hoặc B khác S về chiều hoặc ý nghĩa thống kê thì báo cáo là threat lớn. Phán quyết cũ vẫn giữ (R5), kèm cảnh báo.
- Nếu không khác thì kết luận null chắc chắn với lỗi bộ chấm.

### Kết quả §26m, phần 1: tác dụng theo ba endpoint (06/11/2026; `results/harness_audit.json`, `scripts/harness_audit.py`)

- **Kiểm cách đọc log:**
  - 1.194/1.194 cặp đã đăng ký được nối đúng với báo cáo chấm của nó, theo giá trị loss.
  - Cặp không có báo cáo (không nộp, bản vá không áp, quá giờ) có loss 2/3 và được tính là không resolved.
  - Endpoint S **khớp đúng** số đã đăng ký: E1 +0,019 / 0,000 / −0,013 (53 task); E2 +0,021 (109 task); T4 +0,55.
- **Lỗi của tôi khi viết script (sửa trước khi dùng số):** bản đầu coi cặp không có báo cáo là "không nối được" khi loss < 1, trong khi loss của cặp đó là 2/3. Phép kiểm S phát hiện lỗi này (37 task thay vì 53).
- **Tác dụng** (resolved, có skill − không skill; CI 95% bootstrap theo task):

  | Thí nghiệm | S (đăng ký) | F (chỉ FAIL_TO_PASS) | B (bỏ test hỏng) |
  | --- | --- | --- | --- |
  | E1 `null-guard` | +0,019 [−0,031; +0,075] | +0,019 [−0,025; +0,069] | +0,013 [−0,044; +0,069] |
  | E1 `type-guard` | 0,000 [−0,050; +0,057] | −0,013 [−0,075; +0,050] | 0,000 [−0,050; +0,057] |
  | E1 `exception-handling` | −0,013 [−0,063; +0,038] | −0,006 [−0,057; +0,044] | −0,013 [−0,063; +0,038] |
  | E2 `xreposkill` | +0,021 [−0,009; +0,052] | +0,012 [−0,021; +0,046] | +0,015 [−0,015; +0,049] |
  | T4 `control-oracle-patch` | +0,55 [0,35; 0,75] | **+0,65 [0,40; 0,90]** | +0,55 [0,35; 0,75] |

- **Diễn giải theo quy tắc đặt trước:**
  - E1 và E2 không đổi chiều hay ý nghĩa thống kê ở cả F lẫn B, nên **kết luận null chắc chắn với lỗi bộ chấm**.
  - T4: endpoint S đo thấp tác dụng của đối chứng dương khoảng 0,10. Đó là các task mà bản vá đúng làm qua FAIL_TO_PASS nhưng một vài PASS_TO_PASS trượt.
  - B không bắt được các trường hợp T4, vì mỗi instance T4 chỉ có 2 lần chấm (< 3).
- **Thăm dò, không thuộc họ phép kiểm đã đăng ký:** ba skill gây hại của E1 theo F là −0,067 / −0,067 / −0,092. Hai trong ba có CI không chứa 0; theo S thì cả ba CI đều chứa 0. Chỉ báo cáo mô tả.
- **Test hỏng theo quy tắc B:** 2 instance ở E1, 6 ở E2.

## 27m. Đối chứng bản vá rỗng cho harness của mình, và tỉ lệ chuyển giao trên SSKB (đăng ký 06/11/2026, trước khi có dữ liệu của (a); 0 USD)

**Vì sao:** §26m kiểm harness có từ chối bản vá **đúng** không (bản vá gốc). Nửa còn lại là harness có nhận bản vá **không sửa gì** không. Nhánh `trial` (§25 F0) cho thấy bộ chấm công khai của gskill nhận bản vá rỗng ở 96/96 task. Paper cần cùng phép kiểm đó cho chính harness mà E1, E2 và T4 đã dùng.

**(a) Bản vá rỗng trên harness SWE-bench (Verified) và SWE-bench-Live:**
- **Bản vá:** tạo một file mới `gk_noop.py` chứa đúng một dòng comment. Bản vá áp được nhưng không đổi hành vi nào. Cách này khác cách của §25, vốn thêm dòng vào file có sẵn, vì mình không cần đọc nội dung file gốc.
- **Task:**
  - T4: toàn bộ 20 task (Live);
  - E1: 20 task rút bằng `random.Random(27).sample` từ 53 task của E1 (Verified), sắp theo tên trước khi rút.
  - Con số 20 là vận hành: với 0/20, cận trên Wilson 95% là 0,161. Đủ để phát hiện một bộ chấm nhận bản vá rỗng ở tỉ lệ cỡ của gskill (≈ 1,0), với chi phí CPU nhỏ.
- **Một lần chấm mỗi task.** Chạy **sau khi** §26m chấm xong, để hai việc không tranh CPU và làm test quá giờ.
- **Đại lượng:** tỉ lệ resolved của bản vá rỗng, kèm Wilson 95%.
- **Dự đoán:** 0, vì FAIL_TO_PASS phải fail khi không sửa gì.
- **Diễn giải đặt trước:** nếu có task resolved với bản vá rỗng thì task đó có test FAIL_TO_PASS không bắt được lỗi. Liệt kê các task đó, và tính lại E1/E2/T4 khi bỏ chúng (độ nhạy).

**(b) Tỉ lệ tác dụng chuyển giao giữa các cấu hình SSKB (thăm dò; đã thấy số điểm ở `results/sskb_transfer_power.json`):**
- **Đại lượng:**
  1. ρ = (trung bình hiệp phương sai giữa 6 cặp cấu hình) / (trung bình phương sai trong từng cấu hình), trên 98 skill chung;
  2. trong các (cấu hình, skill) có |Δ| ≥ 6 điểm: tỉ lệ cấu hình khác cùng chiều và |Δ| ≥ 6, và tỉ lệ ngược chiều và |Δ| ≥ 6.
- **CI:** bootstrap theo skill, 10.000 lần.
- **Giới hạn:** dữ liệu một lần chạy không tách được "do scope" và "do nhiễu". Kết luận chỉ là "nhãn và cỡ tác dụng không lặp lại giữa các cấu hình".

**Ghi chú thực thi 27m-1** (06/11/2026, trước khi chạy (a)):
- "53 task của E1" ở trên là chưa chính xác. Mỗi skill có tập 53 task kích hoạt riêng; hợp của ba tập là **144 task**.
- 20 task E1 được rút từ hợp 144 task này, sắp theo tên, bằng `random.Random(27).sample` (`scripts/noop_rescore.py::e1_tasks`).

### Kết quả §27m-b (06/11/2026; `results/sskb_transfer.json`; thăm dò)

- **ρ = 0,067, CI 95% [−0,10; 0,25]** (bootstrap theo skill, 98 skill, 4 cấu hình).
  - ρ là phần phương sai tác dụng chung giữa các cấu hình: hiệp phương sai chéo 3,34 điểm², chia cho phương sai trong từng cấu hình 49,7 điểm².
- **Trong 321 (cấu hình, skill) có |Δ| ≥ 6 điểm**, ở cấu hình khác:
  - cùng chiều và |Δ| ≥ 6: **0,249** [0,158; 0,343];
  - **ngược chiều** và |Δ| ≥ 6: **0,187** [0,116; 0,255].
- **Sửa một con số tôi nói trong trao đổi:** "khoảng 22% chuyển giao" là sai mẫu số. Con số 14,9 là phương sai của trung bình 4 cấu hình, không phải phương sai trong từng cấu hình. Số đúng là 0,067.
- **Diễn giải (theo giới hạn đã ghi):** trên dữ liệu công khai của SSKB, nhãn và cỡ tác dụng của một skill gần như không lặp lại khi đổi agent hay model. Dữ liệu một lần chạy không tách được phần do scope và phần do nhiễu.

## 28m. Chấm lại với mạng qua proxy cho các task có test cần mạng (đăng ký 06/11/2026, trước khi chấm lại bản vá nào của agent; 0 USD)

**Phát hiện dẫn tới mục này** (§26m, 8 instance SWE-bench-Live đã chấm lại bản vá gốc):
- 7 instance "hỏng". Ở 6 trong 7, log test có dấu hiệu mạng: `Name or service not known`, `gaierror`, `URLError`, `CERTIFICATE_VERIFY_FAILED`, `Max retries exceeded`. Ví dụ: `pip install` tới pypi.org bị lỗi chứng chỉ; không phân giải được `dl.google.com`.
- Container chấm của harness **không có mạng ra ngoài và không tin CA của proxy** trong môi trường này.
- Môi trường chấm chính thức có mạng, nên kết quả cũ chấm test cần mạng là trượt ở **cả hai nhánh**. Đây là lỗi của môi trường của mình, không phải của agent.

**Thay đổi:**
- Mỗi container chấm được tạo với `network_mode=host`.
- Biến proxy của phiên được truyền vào (`HTTPS_PROXY`, `HTTP_PROXY`, `NO_PROXY` và dạng chữ thường).
- CA của phiên (`/root/.ccr/ca-bundle.crt`) được gắn chỉ đọc. `REQUESTS_CA_BUNDLE`, `SSL_CERT_FILE`, `PIP_CERT`, `CURL_CA_BUNDLE` trỏ tới CA đó.
- Cách làm giống adapter SSKB (§22). Mọi thứ khác của harness giữ nguyên.
- **Thực hiện:** `scripts/harness_net.py` vá `docker.models.containers.ContainerCollection.create` rồi chạy `swebench.harness.run_evaluation` không đổi gì khác.

**Bước 1, kiểm cách sửa:**
- Chấm lại bản vá gốc 1 lần với mạng cho các instance §26m gắn nhãn "hỏng" có dấu hiệu mạng.
- **Đạt** nếu ≥ 1 instance chuyển sang resolved và **không** instance nào khác trước bị đổi kết quả. Không đạt thì dừng §28m và ghi A#.
- **Kiểm âm (§27m-a dùng lại):** bản vá rỗng vẫn phải không resolved khi có mạng, chấm trên 5 task đầu của danh sách §27m-a.

**Bước 2, chấm lại bản vá của agent:**
- **Tập instance (quy tắc cố định):** mọi instance của E1, E2, T4 mà ở ít nhất một lần chấm gốc (mọi nhánh, mọi seed), `test_output.txt` có một trong các dấu hiệu mạng ở trên.
- Với mỗi instance trong tập, chấm lại **mọi** bản vá đã lưu của agent: cả hai nhánh, mọi seed, đúng file `preds_scored.json` đã chấm lần đầu. Mỗi bản vá chấm 1 lần.
- **Không** gọi model, **không** chạy lại agent.

**Phân tích:**
- Thay báo cáo cũ bằng báo cáo mới cho các instance trong tập, rồi tính lại tác dụng (endpoint S, như §26m) cho E1, E2, T4.
- Báo cáo **cả** số cũ (đã đăng ký, phán quyết giữ nguyên theo R5) lẫn số mới.
- **Diễn giải đặt trước:** nếu số mới khác số cũ về chiều hoặc ý nghĩa thống kê thì đưa lên phần kết quả chính, kèm cả hai số. Nếu không khác thì ghi ở threats to validity.

### Kết quả §28m, bước 1 (06/11/2026; `results/harness_gold_net.json`, `results/harness_noop_net.json`)

- **Bản vá gốc, có mạng qua proxy, 1 lần**, trên 6 instance §26m gắn nhãn "hỏng" có dấu hiệu mạng:

  | Instance | Không mạng (§26m) | Có mạng (§28m) | Host bị chặn (proxy: `connect_rejected`, 403) |
  | --- | --- | --- | --- |
  | `ansible-lint-4662` | hỏng 3/3 | **resolved** | — (pypi.org được phép) |
  | `cfn-lint-3508`, `cfn-lint-3607` | hỏng 3/3 | hỏng | `docs.oasis-open.org` |
  | `briefcase-1640`, `-1785`, `-1811` | hỏng 3/3 | hỏng | `dl.google.com` |

- **Kiểm âm:** bản vá rỗng có mạng trên 5 task đầu của §27m-a: **0/5** resolved.
- **Theo quy tắc đặt trước: ĐẠT.** Có ít nhất 1 instance chuyển sang resolved, và bản vá rỗng vẫn không resolved.
- **Phần còn hỏng** là do chính sách mạng của môi trường chặn 2 host. Hai host này chỉ dùng được khi môi trường cho phép, và việc đó cần @thuthuy duyệt.

**Ghi chú thực thi 26m-2 / 27m-2 / 28m-1** (06/11/2026, trước khi có kết quả nào trên GitHub Actions):
- **Lý do:** lượt chấm cục bộ dừng ở giới hạn 2 giờ của tác vụ nền, sau 20/35 instance của §26m. @thuthuy chọn chạy tiếp trên GitHub Actions ("Số 2").
- **Môi trường khác nhau:** container chấm trên runner GitHub **có mạng đầy đủ**, như khi E2 được chấm. Container chấm cục bộ thì không có mạng (§26m, §28m).
- **Vì vậy:**
  1. Chạy **toàn bộ** 35 instance của §26m (bản vá gốc × 3) và 40 task của §27m-a (bản vá rỗng × 1) trên runner. Kết quả ghi vào file **riêng**: `results/harness_gold_gh.json`, `results/harness_noop_gh.json`.
  2. Kết quả cục bộ (20 instance, không mạng) giữ nguyên, báo cáo riêng.
  3. So sánh hai môi trường trên cùng instance là một phép đo trực tiếp cho §28m: môi trường có mạng không bị chặn host nào.
- **Dữ liệu task** lấy từ `data-snapshots` (`verified_pools.jsonl`, `live_blocks_cd.jsonl`). Đã kiểm khớp tuyệt đối với file đã dùng cục bộ: 816 dòng; `patch`, `FAIL_TO_PASS`, `PASS_TO_PASS`, `base_commit` không khác.
- **Phiên bản:** `swebench==5.0.2` cho Verified, bản fork SWE-bench-Live `ad79b85` cho Live, `docker==7.2.0`, như E2.
- **Chia việc:** 10 shard. Shard k nhận instance thứ k, k+10, … của mỗi danh sách. Không gọi LLM, không cần khóa.

### Kết quả §26m phần 2 và §27m-a trên GitHub Actions (06/11/2026; run 42200960814; `results/harness_gold_gh.json`, `results/harness_noop_gh.json`)

- **Bản vá gốc × 3, môi trường runner (có mạng đầy đủ), 35 instance:**
  - **33 ổn**;
  - 1 hỏng (`conan-15705`: 5 test `TestListPrefs`, không có dấu hiệu mạng; hỏng ở cả hai môi trường);
  - 1 chập chờn (`briefcase-1811`: `test_sign_app[True]`, 1 test).
- **So với cục bộ (không mạng) trên 20 instance chấm ở cả hai nơi:**
  - hỏng → ổn: **10**;
  - ổn → ổn: 8;
  - hỏng → hỏng: 1 (`conan-15705`);
  - hỏng → chập chờn: 1.
  - Như vậy **mọi trường hợp hỏng do mạng ở cục bộ đều hết khi có mạng đầy đủ**, kể cả 5 trường hợp cần host bị chặn ở §28m.
- **Bản vá rỗng × 1, môi trường runner, 40 task: 0/40 resolved** (cận trên Wilson 95%: 0,088). Không có lỗi hạ tầng hay thiếu báo cáo.
  - Harness của mình qua cả đối chứng bản vá rỗng lẫn đối chứng bản vá gốc.
  - Đối chiếu: bộ chấm công khai của gskill cho bản vá rỗng qua 206/216 (§25, nhánh `trial`).
- **Hệ quả cho dữ liệu đã có (đối chiếu với nơi chấm):**
  - E2 được chấm trên GitHub Actions (có mạng), nên **không** bị lỗi mạng.
  - T4 được chấm cục bộ trên task SWE-bench-Live, nên **bị** ảnh hưởng.
  - E1 (Verified) chấm cục bộ: mọi instance Verified đã kiểm đều ổn ở cả hai môi trường.
- **Việc kế tiếp (§28m bước 2):** chấm lại bản vá đã lưu của T4 (40 lần chạy) trên runner. Miễn phí, không gọi model.

**Ghi chú thực thi 28m-2** (06/11/2026, @thuthuy "đồng ý"; trước khi có kết quả chấm lại nào của bản vá agent):
- **Tập instance theo đúng quy tắc đã đăng ký** (`results/s28_rescore_set.json`): E1 144/144, E2 6, T4 3.
  - Quy tắc bắt **mọi** instance E1, vì bước `pip install` trong script chấm của SWE-bench in `CERTIFICATE_VERIFY_FAILED` / `Max retries exceeded` ở gần như mọi lần chấm cục bộ.
  - Quy tắc rộng hơn cần thiết nhưng giữ nguyên (R5). Nó chỉ tốn thêm CPU, không làm sai kết quả.
- **Danh sách bản vá** (`scripts/s28_manifest.py`, `results/s28_manifest.json.gz`): 1.200 bản vá (E1 1.164, E2 30, T4 6). Mỗi bản vá là đúng bản trong `preds_scored.json` của lần chạy đã sinh báo cáo được nối với cặp đã đăng ký. 0 bản vá bị thiếu. Cặp không có báo cáo (loss 2/3) không được chấm lại.
- **Môi trường:** GitHub runner có mạng đầy đủ (như ghi chú 28m-1), thay cho wrapper proxy. Lý do: §28m bước 1 cho thấy proxy cục bộ chặn host cần dùng, còn runner thì không (§26m trên runner: 33/35 ổn). 20 shard theo instance (`.github/workflows/s28.yml`).
- **Chạy thử cục bộ (L48):** 1 bản vá Verified và 1 bản vá Live đều có báo cáo. Kết quả thử không dùng.
- **Phân tích (đặt trước):**
  - Thay báo cáo gốc bằng báo cáo mới cho từng bản vá đã chấm lại.
  - Bản vá mà lần chấm mới **không có báo cáo** (quá giờ, lỗi hạ tầng) thì giữ báo cáo gốc, và đếm số trường hợp này.
  - Tính lại tác dụng theo endpoint S như §26m cho E1, E2, T4; báo cáo số cũ và số mới cạnh nhau.

### Kết quả §28m bước 2 (06/11/2026; run 42213980589; `results/s28_rescored.json`, `results/s28_effects.json`)

- **Chấm lại:** 1.200/1.200 bản vá có báo cáo mới. 0 lỗi hạ tầng; 0 trường hợp phải giữ báo cáo gốc.
- **Số mặt cặp (một nhánh của một cặp) đổi kết quả:**
  - E1: 3/1.540, cả 3 từ trượt sang resolved;
  - E2: 0/30;
  - T4: 3/6, cả 3 từ trượt sang resolved.
- **Tác dụng, endpoint S** (số cũ → số mới; CI 95% bootstrap theo task):

  | Thí nghiệm | Cũ | Mới |
  | --- | --- | --- |
  | E1 `null-guard` (53 task) | +0,019 [−0,031; +0,075] | +0,013 [−0,044; +0,069] |
  | E1 `type-guard` (53) | 0,000 [−0,050; +0,057] | 0,000 [−0,050; +0,057] |
  | E1 `exception-handling` (53) | −0,013 [−0,063; +0,038] | −0,013 [−0,063; +0,038] |
  | E1 ba skill gây hại (40 mỗi skill) | −0,058 / −0,050 / −0,058 | không đổi |
  | E2 `xreposkill` (109) | +0,021 [−0,009; +0,055] | +0,021 [−0,009; +0,055] |
  | T4 `control-oracle-patch` (20) | +0,55 [0,35; 0,75] | **+0,60 [0,35; 0,85]** |

- **Theo quy tắc đặt trước:**
  - E1 và E2 không đổi chiều hay ý nghĩa thống kê, nên ghi ở threats to validity. **Phán quyết đã đăng ký giữ nguyên.**
  - T4 tăng 0,05 (1 task trên 20). Đối chứng dương vẫn có ý nghĩa và mạnh hơn một chút.
- **Kết luận của chuỗi §26m–§28m:**
  - Container chấm cục bộ không có mạng làm một số test trượt ở cả hai nhánh.
  - Lỗi này **không** làm sai kết luận nào của E1 hay E2.
  - Nó làm T4 bị đo thấp một chút.
  - Harness, khi có mạng, qua cả đối chứng bản vá gốc (33/35) lẫn bản vá rỗng (0/40).

## 29. Ablation: skill jinja bỏ chỉ dẫn đọc lịch sử (đăng ký 08/11/2026, trước mọi lần chạy)

**Lý do:** câu hỏi Q7 của review bên ngoài (`docs/review_log.md` R-57): khi bỏ chỉ dẫn đọc lịch sử git, phần còn lại của skill có tác dụng bao nhiêu trong chính môi trường gốc. @thuthuy 08/11: "Làm".

**Câu hỏi:** trong môi trường gốc của gskill (còn commit "Bug Patch"), skill jinja đã bỏ chỉ dẫn đọc lịch sử có làm tăng số task giải được so với không skill không?

**Can thiệp (định nghĩa can thiệp, có quy tắc, không chọn tay):**
- Quy tắc: bỏ mọi dòng của skill khớp `commit|history|git log|git show`, không phân biệt hoa thường; mọi byte khác giữ nguyên (`scripts/make_ablation.py`, test `tests/test_make_ablation.py`).
- Áp lên `docs/skills/gskill/jinja_best_skills.txt` (2.681 byte), quy tắc bỏ **đúng 1 dòng**, dòng 7 ("Check Git History… `git log -n 5`… `git show`"). Dòng `git diff` (mục 5) được giữ, vì không nói về lịch sử.
- Kết quả: `docs/skills/gskill/jinja_no_history.txt`, 2.427 byte, sha256 `b90e246f…065078`. Workflow kiểm lại file và sha256 trước khi chạy.
- Skill mới ngắn hơn 254 byte (9,5%). §27a cho thấy tác dụng của độ dài trên jinja nhỏ và không có ý nghĩa thống kê (+0,09, p = 0,093).

**Thiết kế:**
- 100 task test jinja theo `_gskill_order`; môi trường gốc của gskill (không `--leak-free`).
- Agent, model, seed 41, cost_limit 0,30, giới hạn 50 bước: như §25.
- **Hai nhánh chạy song song trong cùng một job:** không skill (`results/s29_none.json`) và skill đã bỏ chỉ dẫn (`results/s29_ablate.json`). Như vậy hai nửa của mỗi cặp chạy cùng thời điểm (§5: model có thể đổi theo ngày).

**Phép thử chính P29** (một phía, α = 0,025, endpoint S):
- skill đã bỏ chỉ dẫn > không skill;
- kiểm định dấu chính xác trên các cặp lệch;
- một phép thử xác nhận duy nhất, nên không cần Holm.

**Phụ (mô tả, không dùng làm bằng chứng xác nhận):**
1. Gatekeeper (θ = 0, c = 0,5, α = 0,025): admit hay không, và sau bao nhiêu task.
2. Bộ chấm L của gskill trên cùng patch.
3. Nhóm 34 task không có mô tả issue: số task giải được ở mỗi nhánh. Dự đoán từ §25 bước 3: skill đã bỏ chỉ dẫn giải gần bằng nhánh không skill ở nhóm này.
4. So với skill đầy đủ trong môi trường một commit (§25 bước 3: +0,21): hiệu số mức tăng, bootstrap theo task. Hai lượt chạy khác ngày.
5. So với skill đầy đủ trong môi trường gốc (`f1_skill_probe`, 06/11): khác ngày; 27c cho thấy 30/34 task giữ kết quả khi chạy lại sau 1 ngày.
6. Quỹ đạo: số lượt chạy của nhánh đã bỏ chỉ dẫn có gọi `git log` hoặc `git show`, và số lượt có quan sát chứa "Bug Patch".

**Diễn giải đặt trước:**
- P29 bác bỏ: phần mức tăng không phụ thuộc chỉ dẫn đọc lịch sử được chứng nhận trong môi trường gốc.
- P29 không bác bỏ: không chứng nhận được phần đó ở n = 100. Kết quả không cho thấy phần đó bằng 0; báo cáo kèm khoảng tin cậy.
- Ở cả hai trường hợp, kết luận của §25 bước 3 (môi trường một commit) không đổi.

**Kiểm sau khi chạy:** `infra_error`, `crashed`, lượt chạm cost_limit, 100/100 task ở mỗi nhánh. Lỗi hạ tầng là dữ liệu thiếu (S-infra, độ nhạy). Không chạy lại lỗi do agent (L1).

**Ngân sách:**
- Dự kiến 1,44 + 1,94 = **3,38 USD**, theo chi phí đo được của hai nhánh tương ứng (`f1_probe`, `f1_skill_probe`).
- Trần mỗi nhánh = chi phí dự kiến + 1 lượt xấu nhất (0,30), theo bài học A107/A108: không skill 1,75; bỏ chỉ dẫn 2,25; tổng **4,00 USD**.
- **Đính chính:** ước tính 2,1 USD báo @thuthuy trước đó là sai, vì lấy chi phí của nhánh placebo (1,05). Chỉ chạy có phí sau khi @thuthuy xác nhận mức 4,00 USD. **@thuthuy xác nhận 08/11/2026: "Duyệt 4 đô".**

**Chạy thử miễn phí:** `dryrun=true`, task đầu tiên, model giả lập (`--mock-response`), cả hai nhánh.
