# Rà soát toàn bộ và hướng đi cho ASE 2027 (05/11/2026, chờ @thuthuy duyệt)

**Nguồn đã đọc lại:**
- Paper gốc `docs/01-FSE-2027-13-paper.pdf` và bản tóm tắt `docs/03-…-summary.pdf`;
- to-do bản 2 đã duyệt ngày 01/11 (commit `22159ef`, `TODO.md`);
- mọi file trong `results/`, `docs/paper_argument.md`, `docs/preregistration_main.md` §1–17, `docs/novelty_review.md`.

**Quy ước:** mọi con số dưới đây đều lấy từ file kết quả. Số nào là thăm dò (chưa đăng ký trước) thì ghi rõ.

---

## 1. Paper gốc: kỳ vọng nào khả thi, kỳ vọng nào không

Paper gốc tự ghi mọi kết quả là "projected", tức chưa chạy. Tiền đề ngầm của nó là: skill học được có hiệu ứng **lớn** và **khác nhau theo ngữ cảnh**, có hại ở 20–58% số cặp, có lợi ở 46 cặp. Từ đó cần một cổng để phân biệt.

**Dữ liệu thật cho thấy tiền đề này sai trong thiết lập của mình:**
- E1 (đăng ký trước): Z̄ ∈ [−0,019; +0,013], mọi CI chứa 0.
- E2 (đăng ký trước): mức tăng +2,1 điểm, CI [−1,0; +5,3].
- SWE-Skills-Bench (nguồn ngoài): 92/98 skill không có tác dụng.
- Phân tích dư địa trên 336 lần chạy E1 (thăm dò): 48,5% số lần chạy sửa đúng file nhưng sai cách sửa; chỉ 7,7% sửa sai file.

| Kỳ vọng gốc | Khả thi? | Lý do (bằng số) |
| --- | --- | --- |
| **RQ1:** nhận nhầm giảm 11,5% → 5,1% so với replay + fingerprint, **tại cùng độ phủ** | ❌ **Không**, và một phần đã bị dữ liệu bác | (a) Không có code GSE, nên baseline quyết định đã đổi sang XRepoSkill từ 01/11. (b) Nhãn "có hại" trên skill thật không xác lập được: hiệu ứng khoảng 0,02–0,05 cần hàng trăm cặp mỗi ô (G1 verdict: δ = 0,05 cần 189 task × 3 seed). (c) **§16:** trên nhiễu thật, khi chỉnh ngưỡng cho khớp độ phủ, Gatekeeper **không** có lợi thế (mọi quy tắc ≤ 0,0003) |
| **RQ2:** bắt được 41/46 cặp ghép có hại | ❌ trên skill thật; ✅ trên plasmode và lý thuyết | Không thể dựng 46 cặp ghép có hại khi từng skill riêng lẻ có hiệu ứng ≈ 0. T3 (plasmode): ghép ngây thơ nhận nhầm 98,8%, Gatekeeper 0%. Định lý ghép chứng minh được |
| **RQ3:** khác biệt theo regime A/B/C; so với thử lại cùng ngân sách (B9) | ❌ phần regime; ⚠️ phần B9 | Regime cần nhãn hại thật (như RQ1). B9 chạy được, nhưng khi skill ≈ 0 thì kết quả gần như biết trước |
| **RQ4:** độ trễ thu hồi; điểm hòa vốn | ✅ | T2/T2b đã làm trên nhiễu thật. Điểm hòa vốn tính được từ chi phí đo |
| **Lý thuyết:** cận admission, ghép không bị chặn, không có bảo đảm phi tham số, Prop. 9 ghép cặp | ✅ | Cả bốn chứng minh được. Prop. 9 đã đo: ghép cặp giảm phương sai **3,3–4,6×** |
| **SkillShift-SE:** 180 cặp, 25 repo, 4 dòng version, kappa ≥ 0,7 | ❌ | Mỗi cặp cần hàng trăm trial mới gán được nhãn. Với khoảng 0,08 USD mỗi lần chạy, 180 cặp × 200 trial × 2 nhánh ≈ 5.800 USD |
| **Go/no-go:** giảm ≥ 5 điểm so với replay + fingerprint | ❌ | Không đo được, vì lý do ở RQ1 |

**Kết luận phần 1:** câu hỏi gốc ("cổng nào an toàn khi chuyển skill sang repo mới") vẫn đúng. Nhưng **câu trả lời dạng "Gatekeeper giảm nhận nhầm x điểm trên benchmark skill thật" không khả thi và không đúng**. Lý do: skill thật hầu như không có hiệu ứng nào để phân biệt.

---

## 2. To-do gốc (bản 2, 01/11): phần nào khả thi

| Phase | Nội dung | Trạng thái | Khả thi cho paper? |
| --- | --- | --- | --- |
| H | Hạ tầng, CI, report | ✅ Xong | — |
| 0 | Học nền, harness, e-process khớp `confseq` | ✅ Xong | — |
| 1 | Sửa lý thuyết (Định lý 7, 2ξ_s, sổ α, Prop. 9) | ⚠️ Sửa trong ghi chú, **chưa viết thành chứng minh** | ✅ miễn phí; việc F1 |
| 5a | Lõi Gatekeeper (e-process, sổ α, admission) | ✅ Xong, có test | — |
| 2 | Môi trường, tái hiện baseline | ✅ Một model, một harness. XRepoSkill có; GEPA dùng tiêu chí; MemGovern dựng được, chưa chạy ô | ⚠️ Model thứ hai: chưa có |
| 3 | Pilot và go/no-go **theo khả thi** (R4) | ✅ Đã làm, qua G1, E1, E2. **Kết luận khả thi: không đủ power cho skill thật** | Kết quả này chính là dữ liệu cho hướng mới |
| 4 | SkillShift-SE: 25 repo, induce skill, 180 cặp, 46 cặp ghép, nhãn kappa | ❌ Không khả thi (phần 1) | **Bỏ.** Thay bằng plasmode trên nhiễu thật, cùng đối chứng dương và âm trên agent thật |
| 5b | Gatekeeper đầy đủ: D, I, P, K, routing, certificate | ⚠️ Một phần | Chỉ giữ phần cần cho các bảo đảm: scope, sổ α, thu hồi |
| 6 | 8 hệ thống × mọi cặp × 3 lần × 2 backend; 6 ablation | ❌ | **Bỏ.** Thay bằng so sánh quy tắc trên cùng luồng nhiễu thật (đã có P1–P3, T1–T3) |
| 7 | Phân tích, viết | ⏳ | ✅ |

**Điều đáng nói thẳng:** Phase 3 theo đúng to-do gốc lẽ ra phải dừng ở câu "power ≥ 80%?". G1 đã trả lời "không" ngày 03/11, nhưng sau đó vẫn chạy E1 và E2. Hai thí nghiệm đó không thừa: chúng tạo ra khoảng 2.000 lần chạy ghép cặp, làm nền cho mọi kết quả plasmode. Nhưng lẽ ra phải chạy chúng **với mục tiêu đó ngay từ đầu** (bài học L27).

---

## 3. Kết quả từ giai đoạn 0 đến nay: cái nào dùng được, tại sao

### 3a. Dùng được, giá trị cao

| Kết quả | File | Vì sao hữu dụng |
| --- | --- | --- |
| **Khoảng 2.000 lần chạy ghép cặp thật** (G1, E1, E2) | `runs/` (nhánh `raw-archive`) | Nền của mọi plasmode; không ai khác có dữ liệu A/A và ghép cặp cho coding agent ở cỡ này |
| **Cấu trúc nhiễu:** F(n) = 7,1 / 5,5 / 3,4 điểm (n = 113 / 200 / 500); 21,5% lời gọi đầu không lặp lại được; ghép cặp giảm phương sai 3,3–4,6× | `noise_floor_audit.json`, `stationarity_e2.json` | Số đo mới cho cộng đồng: cần bao nhiêu lần chạy để tin một mức tăng |
| **C8: 7/13 mức tăng đã công bố nằm trong nhiễu** (XRepoSkill, MemGovern) | `noise_floor_audit.json` | Có tác động thực tế. Phải kèm giới hạn (nhiễu đo trên một model, nên quy tắc có lợi cho các tuyên bố) |
| **C1:** skill có hiệu ứng nhỏ (E1, E2 đăng ký trước; SWE-Skills-Bench) | `e1_final.json`, `e2_final.json` | Động cơ thật cho bài toán chứng nhận: tín hiệu nhỏ so với nhiễu |
| **C4–C6, P1:** Gatekeeper giữ FWER ≤ 0,002 trên nhiễu thật; khi bị theo dõi liên tục, B-X2 từ 0,075 lên 0,303; plug-in nhận 10,5 ô có hại hoặc vô dụng trên 100 ô | `plasmode_real.json`, `plasmode_extra.json` | Bằng chứng chính cho tính hợp lệ khi bị theo dõi |
| **Theo dõi trên null thật:** B-X2 từ 0,026 lên 0,103 | `null_monitoring_real.json` | Cùng ý trên, không cần cấy hiệu ứng |
| **T1–T3, T2b:** vòng đời skill. Thu hồi hai bước: phát hiện 100%, độ trễ 75, **0/1000** thu hồi nhầm, 13% thời gian cách ly. e-SR: độ trễ 12 nhưng thu hồi nhầm 35%. Library Drift: phát hiện 53% | `lifecycle_plasmode.json`, `two_stage_retirement.json` | Phần phương pháp còn lại sau khi đối chiếu Qu et al.: thu hồi có kiểm soát thu hồi nhầm |
| **T4:** đối chứng dương trên agent thật được admit ở trial 20, khớp dự đoán đăng ký (21–25); mức tăng 0,55 [0,35; 0,75] | `t4_decision.json` | Chứng minh phương pháp chạy đúng trên agent thật **và** dự đoán chi phí của nó đúng |

### 3b. Dùng được nhưng có giới hạn

| Kết quả | Giới hạn |
| --- | --- |
| C2: tái lập XRepoSkill (bác bỏ 4/6 mức tăng) | Khác model, khác benchmark. Chỉ là động cơ; không kết luận "họ sai" |
| C3: cổng ngây thơ trên dữ liệu thật (43–44% so với nền 38,5%) | Nhãn chưa xác lập được |
| §16: đường cong nhận nhầm theo độ phủ | **Kết quả âm:** không có lợi thế khi chỉnh ngưỡng bằng đáp án. Phải báo cáo, vì nó định nghĩa đúng giá trị: hợp lệ **mà không cần chỉnh ngưỡng** |
| Phân tích dư địa (thăm dò; 48,5% "đúng file, sai cách sửa") | Chưa đăng ký trước; mỗi task chỉ có 3 lần chạy |
| Nghi test PASS_TO_PASS chập chờn (bản vá giống hệt bản gốc mà không được tính là giải được) | Chưa kiểm |

### 3c. Không dùng được, hoặc chỉ là bài học

- G1 giai đoạn B: lỗi seed 0 (A14).
- Các lần chạy lại vì A76.
- Ô MemGovern: hạ tầng xong, chưa chạy ô.
- Kiểm "model không đổi" thất bại, nên B3 dừng (A75).
- 2.1: dừng sau 4 task (A79).
- Các lỗi này đã được ghi vào audit; giá trị của chúng chỉ nằm ở phần threats to validity và quy trình.

**Chi tiêu:**

| Hạng mục | USD |
| --- | --- |
| G1 | 31,26 |
| E1 | 78,68 |
| E2 | 43,04 |
| Thí nghiệm chính tới nay (kiểm model 0,35 + T4 2,16 + 2.1 0,97) | 3,48 |
| **Tổng** | **156,46** |

---

## 4. Hướng đi đề xuất

### 4a. Định vị

**Tên làm việc:** "Certifying skills for coding agents under real evaluation noise" (chứng nhận skill cho coding agent dưới nhiễu đánh giá thật).

**Luận điểm chính:** ở coding agent, hiệu ứng của skill nhỏ so với nhiễu đánh giá. Ba thực hành phổ biến không phân biệt được tín hiệu và nhiễu:
- so một lần;
- kiểm định cỡ mẫu cố định nhưng nhìn kết quả nhiều lần;
- nhận ứng viên theo minibatch.

Paper (i) **đo** nhiễu đó trên khoảng 2.000 lần chạy thật, (ii) đưa ra một **giao thức** nhận, ghép và thu hồi skill có bảo đảm FWER theo từng (skill, scope), và (iii) **kiểm chứng** giao thức trên nhiễu thật và trên agent thật.

**Ba đóng góp (đều đã có phần lớn dữ liệu):**

| # | Đóng góp | Đã có | Còn thiếu |
| --- | --- | --- | --- |
| K1 | **Nghiên cứu đo lường nhiễu đánh giá coding agent:** F(n), không tất định, lợi ích ghép cặp, dư địa theo loại thất bại, phần nhiễu do test chập chờn; đối chiếu 13 mức tăng đã công bố, kèm bảng "cần bao nhiêu trial để chứng nhận" | Phần lớn | F2, F3 (miễn phí) |
| K2 | **Giao thức có bảo đảm:** admission FWER theo (skill, scope); bảo đảm cho skill ghép; thu hồi hai bước với P(thu hồi nhầm) ≤ α. Trích Qu et al. là công trình gần nhất; chỉ tuyên bố phần khác biệt (FWER, scope, ghép, thu hồi có xác nhận) | Mã, mô phỏng | F1: chứng minh (miễn phí) |
| K3 | **Kiểm chứng:** plasmode trên nhiễu thật (P1–P3, T1–T3, T2b, §16 kể cả kết quả âm); đối chứng dương trên agent thật (T4) | Gần đủ | Tùy chọn P1: vòng đời trên agent thật |

**Vì sao hướng này có xác suất thành công cao hơn mọi hướng trước:** các việc còn lại là **phép đo và chứng minh**, không phải phép thử có cổng.
- Phép đo luôn cho ra kết quả báo cáo được, dù số đo tốt hay xấu.
- Các hướng trước (G1, E1, E2, 2.1) đều đặt cược vào giả thuyết "skill có hiệu ứng ≥ ngưỡng", và cả bốn lần đều trượt.

**Điểm yếu mà reviewer A\* sẽ chấm, và cách xử lý:**

| Điểm yếu | Mức | Xử lý |
| --- | --- | --- |
| Một model | Cao | P2 (có chi phí, chờ @thuthuy): lặp lại phần đo nhiễu cốt lõi trên model thứ hai. Không có P2 thì phải ghi rõ trong threats |
| Trùng với Qu et al. (betting referee) | Cao | Định vị K1 là đóng góp chính; K2 chỉ nhận phần khác biệt; so sánh trực tiếp với e-BH và e-SR của họ (đã có ở T1, T2) |
| "Không chứng nhận được skill thật nào" | Trung bình | Biến thành kết quả: K1 cho thấy vì sao (dư địa, F(n)). T4 cho thấy giao thức chứng nhận đúng khi hiệu ứng có thật |
| "Lợi thế chỉ là thận trọng" | Trung bình | §16: báo cáo thẳng là không có lợi thế khi chỉnh ngưỡng bằng đáp án. Giá trị là hợp lệ khi không có đáp án và khi bị theo dõi |

**Mức cạnh tranh** (định tính; không có dữ liệu để tính xác suất được nhận):
- Có K1 + K2 + K3 nhưng không có P2: **ranh giới** cho A\*. Lỗ hổng một model là lý do bị loại phổ biến.
- Có thêm P2: **cạnh tranh được**.
- Mình không hứa được nhận.

### 4b. To-do mới

Mỗi việc ghi theo L38: kết quả gì, xác suất cho ra kết quả dùng được, và vì sao.

| # | Việc | Chi phí | Cho ra | P(có kết quả dùng được) và lý do | Phụ thuộc |
| --- | --- | --- | --- | --- | --- |
| F1 | Chứng minh: admission FWER (Ville + sổ α); ghép (Định lý 4′, hệ số TV, ξ_s → 2ξ_s); thu hồi hai bước (Σα_k ≤ α) → `docs/theory/proofs.md` | 0 | K2 | **Cao:** đều là kết quả chuẩn (Ville 1939; Wang & Ramdas 2022), chỉ cần ráp và kiểm. Rủi ro: bị coi là đơn giản; xử lý bằng cách không tuyên bố là lý thuyết mới | — |
| F2 | **Đăng ký §18 rồi chạy nghiên cứu đo lường:** dư địa theo loại thất bại trên E1 + E2; không tất định; F(n); lợi ích ghép cặp; **chấm lại bản vá gốc** của các task nghi chập chờn, mỗi task 5 lần (chỉ dùng Docker, không gọi LLM) | 0 | K1 | **≈ 1:** phép tính trên dữ liệu đã có; kết quả nào cũng báo cáo được | Lấy E2 thô từ `raw-archive` |
| F3 | Bảng "cần bao nhiêu trial để chứng nhận" cho 13 mức tăng đã công bố, mô phỏng trên nhiễu thật (cùng cách đã dự đoán đúng T4) | 0 | K1 | **≈ 1:** phép tính. Độ tin cậy của cách mô phỏng đã được T4 kiểm (dự đoán 21–25, thực tế 20) | F2 |
| F4 | Mô phỏng trước P1: δ trước = +0,55 (đo ở T4), δ sau là hiệu ứng của "bản vá sai" (ước từ chạy thử) → phân phối số trial cần để admit rồi thu hồi | 0 | Quyết định P1 | **≈ 1** (phép tính) | — |
| F5 | Viết lại paper theo 4a; bảng và hình sinh tự động; kiểm `refs.bib`; cập nhật `number_provenance` và `glossary` | 0 | Bản thảo | Cao | F1–F3 |
| F6 | 👤 Một người biết thống kê đọc F1; 👤 thầy duyệt hướng | 0 | — | — | F1 |
| P1 | *(tùy chọn)* **Vòng đời trên agent thật:** skill bắt đầu đúng (gợi ý bản vá đúng) rồi đổi sang sai ở trial k; Gatekeeper phải admit, rồi thu hồi bằng hai bước | Từ F4; ước 5–8 USD (≈ 0,11 USD mỗi cặp × 50–70 cặp, theo T4) | Kiểm chứng T2b trên agent thật | Chỉ đề xuất khi F4 cho xác suất cao. Hiệu ứng do mình dựng nên dự đoán được, giống T4 | F4; @thuthuy duyệt trần |
| P2 | **Model thứ hai:** đo nhiễu A/A trên khoảng 100 task (200 lần chạy) và lặp lại T4 | Gemini Flash: ≈ 0,24 USD mỗi lần chạy (đo 02/11) → ≈ 48 USD cho 200 lần, ≈ 58 USD nếu thêm T4 (khoảng 20 cặp). Model của hãng khác: chưa có giá đo | Tính tổng quát cho K1 và K3 | **≈ 1 cho phần đo nhiễu** (không có cổng). T4 trên model mạnh hơn: cao | 2.3: thông tin khóa và giá (@thuthuy) |

**Thứ tự:** F2 → F3 → F1 → F4 song song. P1 và P2 chỉ làm khi @thuthuy duyệt, kèm số dự đoán từ F4 hoặc giá đo. Sau đó là F5 và F6.

**Thời gian:** F1–F4 mất khoảng 1–2 ngày làm việc. Hạn ASE 2027 dự kiến cuối 05/2027, nên phần viết có nhiều thời gian.

**Việc bỏ hẳn:**
- SkillShift-SE 180 cặp;
- tuyên bố "11,5% → 5,1%";
- RQ2 trên skill thật;
- regime A/B/C;
- 8 hệ thống × 2 backend;
- mọi pilot skill thật mới không có cận trên ≥ cổng (L38).

---

## 5. Kiểm lại trước khi duyệt (05/11/2026): hai tuyên bố ở trên bị yếu đi

### 5a. Bậc thang skill của H6: chỉ hai đầu là rẻ

Hiệu ứng đã đo của các skill đối chứng:

| Skill | Dữ liệu | n | Mức tăng tỉ lệ giải |
| --- | --- | --- | --- |
| Bản vá gốc (`control-oracle-patch`) | T4 | 20 | +0,550 |
| Test FAIL_TO_PASS (`control-oracle-tests`) | G1 B3 | 38 | +0,158 |
| File cần sửa (`control-oracle-files`) | G1 B2 | 38 | +0,026 |
| 3 skill có hại dạng chỉ dẫn (`harm-*`) | E1, 3 seed × 40 | 120 mỗi skill | −0,05 tới −0,06 (từng seed: 0 tới −0,125) |

**Hệ quả:**
- Các cổng chỉ khác nhau ở **vùng giữa**, tức hiệu ứng khoảng ±0,05–0,15. Gán nhãn thật cho vùng này cần khoảng 100 trial trở lên mỗi skill. Đây chính là bài toán quá đắt của RQ1 gốc.
- Vậy bậc thang H6 **không** cứu được RQ1 với giá rẻ. Vùng giữa phải dùng plasmode.
- Lần chạy thật chỉ dùng được để **kiểm xem mô phỏng có dự đoán đúng chi phí không**. Ví dụ đăng ký trước số trial cho `control-oracle-tests` rồi chạy, tương tự T4.

### 5b. Tính mới của K1: phần lớn đã có người công bố

Các công trình tìm được:
- **"On Randomness in Agentic Evals"** (arXiv 2602.07150): khoảng 60.000 quỹ đạo trên SWE-bench Verified. Pass@1 của một lần chạy dao động 2,2–6,0 điểm, kể cả ở nhiệt độ 0. Khuyên chạy nhiều lần và phân tích power.
- **"Coding Agents Have Converged"** (arXiv 2609.17394): chỉ những task "lúc giải được, lúc không" mới mang thông tin cho phép so sánh ghép cặp.
- **"Engineering Reliable Coding Agents"** (arXiv 2608.13867) và **"Same Model, Different Harness"** (arXiv 2608.26218).

**Hệ quả:**
- "Đo nhiễu đánh giá coding agent" **không thể** là đóng góp chính. F(n), tính không tất định và khuyến nghị chạy nhiều lần đều đã có.
- Phần có thể còn khác (phải đọc bản gốc mới khẳng định được, theo R1):
  1. nhiễu của **phép so sánh có và không có skill** trên cùng task (A/A ghép cặp);
  2. tác hại của **việc theo dõi liên tục** lên các quy tắc nhận skill;
  3. đối chiếu với các mức tăng của các **hệ thống skill** đã công bố.

**Việc phải làm trước khi chốt hướng:** đọc bản gốc của 4 bài trên và của Qu et al., đưa vào `configs/sources.json`, rồi lập bảng "đã có hay chưa có" cho từng đóng góp dự định. Chưa có bảng đó thì chưa chốt định vị.
