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
