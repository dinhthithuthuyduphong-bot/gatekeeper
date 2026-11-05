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
