# Kế hoạch cải tiến để paper đạt mức A* (bản 2, 12/11/2026; chờ @thuthuy duyệt)

**Bản 2 thay bản 1.** Mục 1 đánh giá bản 1 và nêu các dữ kiện mới tìm được trong lần rà soát thứ hai. Các mục sau là kế hoạch đã sửa.

**Phạm vi rà soát (cả hai lần):**
- bản thảo gốc (`docs/01-FSE-2027-13-paper.pdf`);
- TODO gốc và mục ★ của `TODO.md`;
- các tài liệu định hướng: `strategy_review.md`, `direction_final.md`, `plan_replication.md`, `plan_scope_measured.md`, `todo_strongest.md`, `potential_issues.md`;
- mọi nhánh trên remote;
- paper mới nhất (`paper/main.tex`, commit `c7d3e06`);
- ba bản phản biện bên ngoài (08/11, 10/11, 11/11).

**Quy ước:**
- Chi phí ước tính lấy từ lượt chạy cùng cấu hình đã đo (L53), ghi kèm file nguồn.
- Mục nào chưa có số đo thì ghi "cần đo thử trước".

---

## 0. Tình hình hiện tại (12/11/2026)

- **Không có lần chạy nào đang chạy.** Lần chạy có phí cuối là §30 (xong 10/11).
- **§30 đã xong:**
  - Skill học lại khi đã bịt rò rỉ không có chỉ dẫn đọc lịch sử (0/8 ứng viên).
  - Skill đó được chứng nhận: 33 so với 16; p = 2,4·10⁻⁴; admit sau 65 task.
  - Mức tăng không khác phần mức tăng thật của skill gốc: −0,04 [−0,13; 0,05].
  - Đem sang môi trường còn rò rỉ, nó giải 1/34 task không có mô tả (skill gốc: 15/34).
- **§31 và hai bản trả lời phản biện (11/11) đã vào paper:** bảo đảm cho pool hữu hạn, 10.000 thứ tự task, độ nhạy theo θ, đọc theo FWER.
- **Mọi lần chạy có phí đang bị chặn:** project GCP chạm trần chi tiêu ở phía tài khoản (A124).
- **Model khác hãng** (`docs/preregistration_main.md` §26):
  - Mistral Small 3.1 đang chờ quyền truy cập (404).
  - Claude bị từ chối hạn mức.
  - Phương án dự phòng đã được @thuthuy đồng ý ngày 07/11: Gemini Flash. Khi đó paper chỉ được viết "trong họ Gemini".

---

## 1. Bản 1 đã đủ mạnh chưa

**Kết luận: đúng hướng, nhưng chưa đủ.** Bản 1 có năm chỗ yếu. Lần rà soát thứ hai tìm thêm bốn dữ kiện miễn phí, và chúng làm đổi thiết kế.

### 1.1 Dữ kiện mới (miễn phí, tính ngày 12/11 từ dữ liệu đã lưu)

| # | Dữ kiện | Nguồn | Hệ quả |
| --- | --- | --- | --- |
| D1 | Ở lượt học Bleve, chỉ dẫn đọc lịch sử có ở 4/9 ứng viên khác rỗng, và xuất hiện lần đầu ở **ứng viên thứ 5**, ứng viên cuối của nửa đầu (nửa đầu kết thúc với 6 ứng viên, 354 metric call). Ở Jinja: ứng viên thứ 2, 5/8. | `scripts/candidates_history.py` trên `s25bleve_learn_run.tar.gz` | Giả định "nửa lượt học là đủ" của bản 1 **không an toàn**. S2 phải đổi thiết kế (mục 4, S2). |
| D2 | Tỉ lệ task **không có mô tả issue**: Jinja 106/350 (30%), Bleve 131/350 (37%), Pygments 24/350 (7%). | dòng task trên `data-snapshots` | Gợi ra một **giả thuyết kiểm được**: bộ học viết chỉ dẫn rò rỉ khi nhiều task không giải được nếu thiếu lối tắt. Hai repo có chỉ dẫn đều có tỉ lệ này cao. |
| D3 | Tỉ lệ giải nền trên issue thật của `conan-io/conan` (SWE-bench-Live): 6/28 lượt chạy không skill ở E2 (khoảng 0,21). | bản ghi E2 (`scripts/replicate_attribution.py`) | S3 không rơi vào hiệu ứng sàn như Pygments (5/100). |
| D4 | E1 có **ba skill có hại do mình dựng** (`harm-minimal-edit`, `harm-skip-verification`, `harm-swallow-exceptions`), đã chạy trên agent thật. | `results/placebo_suite.json`, mục `D2_on_real_data` | Phép so quy tắc trên luồng thật (A1) có nhãn âm thật, không chỉ A/A. |

### 1.2 Năm chỗ yếu của bản 1 và cách bản 2 sửa

| # | Chỗ yếu của bản 1 | Sửa ở bản 2 |
| --- | --- | --- |
| G1 | S2 chỉ **đếm** ("k trên m repo"). Đếm thì không giải thích được, và với m nhỏ khoảng tin cậy rất rộng: 6/6 cho cận dưới 0,54; 8/8 cho 0,63. | S2 thành phép thử một **dự đoán đặt trước** (liều–đáp ứng theo D2): chọn repo theo tỉ lệ task không mô tả, dự đoán repo tỉ lệ cao có chỉ dẫn, repo tỉ lệ thấp không có. |
| G2 | S2 dùng nửa lượt học; D1 cho thấy có thể bỏ sót. | Thiết kế hai giai đoạn: chạy 300 metric call; chưa thấy chỉ dẫn thì chạy tiếp tới 600, đúng lệnh `--resume` đã dùng. |
| G3 | W1 (một model) không có đường đi cụ thể. | Thêm S1a: agent Flash trên 34 task không mô tả (phương án đã được đồng ý 07/11). Thêm S1b: đổi model reflection. |
| G4 | Thiếu phép phát hiện lúc chạy và thước đo mức phơi nhiễm; phản biện 08/11 hỏi cả hai. | Thêm A6 (bộ theo dõi truy cập lịch sử, kiểm trên trace đã có) và A7 (tỉ lệ task không mô tả trên toàn SWE-smith). |
| G5 | Không có tiêu chí dừng, không có "làm xong thì paper được nói gì", không có lịch và sổ rủi ro. | Thêm mục 5 (bậc thang tuyên bố), mục 7 (lịch), mục 8 (rủi ro). |

---

## 2. Điểm yếu còn lại của paper, xếp theo mức nguy hiểm

| # | Điểm yếu | Ai nêu | Mục trả lời |
| --- | --- | --- | --- |
| W1 | Một họ model cho agent; một model reflection | cả ba | S1a, S1b, S1c |
| W2 | Một bộ học; mỗi điều kiện một lượt học; "bộ học viết chỉ dẫn rò rỉ" là quan sát, chưa phải quy luật | 10/11, 11/11 | S2 |
| W3 | Chỉ task tổng hợp; chưa có repo thật | cả ba | S3 |
| W4 | Gatekeeper chưa được so với quy tắc khác trên luồng thật | 11/11 | A1 |
| W5 | Tỉ lệ giải nền thấp, khó đo tác hại | 11/11 | B2, S3 |
| W6 | Một seed mỗi nhánh | cả ba | B1 |
| W7 | Lý thuyết ít mới | 10/11 | A2, A3 |
| W8 | Thông điệp loãng | 10/11 | A3 |
| W9 | Lời hứa của bản thảo gốc (so với baseline quyết định) chưa thực hiện | bản thảo gốc | A1, B3 |

---

## 3. Khoảng cách với bản thảo gốc

| Lời hứa của bản thảo gốc | Hiện trạng | Xử lý |
| --- | --- | --- |
| SkillShift-SE: 180 cặp, 25 repo | Bỏ (540–1.180 USD) | Không khôi phục; S2 và S3 thay vai trò "nhiều repo" |
| RQ1: so với replay cộng fingerprint | Bỏ | A1: so các quy tắc trên luồng thật, có nhãn âm thật (D4) |
| RQ2: composition | Đã cắt khỏi paper | Không khôi phục |
| Định lý admit có dịch chuyển | Có, kèm điều kiện pool hữu hạn | Đủ; A2 thêm phần mới |
| Thu hồi | Chỉ có plasmode | B3: trên hai luồng thật đã có |

---

## 4. Kế hoạch

### Gói A: miễn phí (khoảng 5–7 ngày làm việc)

**A1. So các quy tắc admit trên luồng thật** (W4, W9)
- **Luồng** (đều đã chạy):
  - 7 lần admit của §25–§30;
  - Pygments;
  - placebo so với không skill;
  - A/A thật của E1/E2;
  - **ba skill có hại của E1 (D4)**;
  - T4.
- **Quy tắc đem so:** Gatekeeper; plug-in một lần và có giám sát; cổng Mantel–Haenszel; luật GEPA; lặp lại 2/3 seed; Library Drift (N_min = 100).
- **Nhãn, đặt trước và không dùng các quy tắc đang so:**
  - "nên nhận": tác dụng được một lượt chạy độc lập xác nhận (học lại, bỏ chỉ dẫn, hoặc đối chứng dương theo cấu trúc);
  - "không nên nhận": A/A, placebo, skill có hại theo cấu trúc.
- **Thành công:** bảng quyết định từng quy tắc trên từng luồng; số lần nhận nhầm và bỏ sót của mỗi quy tắc.
- **Giới hạn:** khoảng 20 luồng, nên là minh họa có nhãn, ghi là thăm dò.

**A2. E-process cho phần do môi trường** (W7)
- **Thiết kế:** kiểm anytime-valid cho hiệu số giữa hai môi trường trên cùng task; Z_i ∈ [−2, 2], đổi thang về [−1, 1]; chứng minh theo Proposition pool hữu hạn đã có.
- **Đăng ký trước (§32):**
  - công thức;
  - ghi rõ dữ liệu Jinja/Bleve đã được nhìn ở dạng khoảng bootstrap, nên kết quả trên hai repo này là minh họa;
  - phép kiểm sẽ được dùng **xác nhận** trên dữ liệu mới của B1 (seed 2).
- **Thành công:** paper có một công cụ mới, "chứng nhận rằng một phần mức tăng thuộc về môi trường", và dùng nó trên dữ liệu chưa nhìn.

**A3. Dựng lại paper quanh một trục** (W7, W8)
- **Trục:** bộ học biến lỗi môi trường thành chỉ dẫn → chứng nhận phải gắn với scope và đối chứng → bịt lỗi rồi học lại cho skill sạch.
- **Xuống phụ lục:** auditor LLM, MemGovern, so với mức tăng đã công bố, SWE-Skills-Bench ρ.
- **Lên đầu:** "đối chứng một commit bắt được rò rỉ; e-process không tự bắt được".
- **Thành công:** abstract dưới 200 từ; mỗi RQ một câu kết luận.

**A4. Chuẩn bị theo yêu cầu của ASE**
- Số trang, double-blind, Data Availability.
- Artifact ẩn danh; license của từng thứ phân phối lại.
- Thu hồi khóa `0cf3193a`.

**A5. Vì sao skill sạch giúp** (thăm dò)
- So nội dung skill gốc và skill học lại theo nhóm chỉ dẫn.
- So quỹ đạo của các task chỉ skill sạch giải được.

**A6. Bộ theo dõi truy cập lịch sử** (mới; trả lời câu hỏi "phát hiện lúc chạy")
- **Thiết kế:** quy tắc trên trace: agent gọi `git log`/`git show`, và quan sát chứa commit không thuộc task.
- **Kiểm trên mọi trace đã lưu**, có nhãn theo cấu trúc:
  - môi trường gốc với skill gốc: có khai thác;
  - môi trường một commit: không thể khai thác;
  - skill bỏ chỉ dẫn: 6/100 tự tìm.
- **Thành công:** độ nhạy và tỉ lệ báo nhầm của bộ theo dõi; một đối chứng **không cần chạy lại** mà người dùng benchmark áp được ngay.
- **Giới hạn:** chỉ bắt kênh lịch sử git; ghi rõ.

**A7. Mức phơi nhiễm trên toàn SWE-smith** (mới)
- **Thiết kế:** workflow `data` tính, cho cả 222 repo (59.136 task), tỉ lệ task không có mô tả issue.
- **Dùng cho:**
  - paper: "bao nhiêu phần của benchmark nằm ở vùng mà rò rỉ quyết định kết quả";
  - quy tắc chọn repo của S2.
- **Thành công:** một bảng theo repo; phân phối của tỉ lệ này.

**B3. Thu hồi trên luồng thật** (W9; 0 USD)
- **Luồng:** skill Jinja trên Pygments; skill sạch đem sang môi trường còn rò rỉ.
- **So:** e-detector của Qu et al. với quy tắc hai bước của §15.

### Gói B: có phí, rẻ (khoảng 13–17 USD)

**B1. Seed thứ hai cho bốn nhánh Jinja** (W6; cũng là dữ liệu xác nhận cho A2)
- **Chi phí:** dự kiến 6,7 USD (`f1_probe`, `f1_skill_probe`, `s25_leakfree_none`, `s25_leakfree_skill`); trần 8,0.
- **Thành công:** Δ_leak lần hai nằm trong khoảng của lần một; e-process của A2 đạt ngưỡng trên dữ liệu gộp.
- **Dừng:** nếu Δ_leak lần hai có khoảng tin cậy chứa 0 thì báo cáo cả hai lần và hạ câu chữ. Không chạy seed thứ ba để "gỡ".

**S1a. Agent thứ hai trong họ Gemini trên 34 task không mô tả** (W1, một phần)
- **Thiết kế:** skill gốc so với không skill, môi trường gốc, agent Flash; đếm số task giải được và số trace đọc "Bug Patch".
- **Chi phí:** đo thử 5 task trước (khoảng 0,6 USD); ước tính cả phép thử khoảng 3,8 USD theo tỉ lệ giá; trần 5,0.
- **Thành công:** paper viết được "hai model của một hãng".
- **Điều kiện:** @thuthuy mở lại mục model thứ hai (đang tạm ngưng).

**B2. Dùng lại trên repo có tỉ lệ nền cao** (W5)
- **Bước 1:** đo nhánh không skill trên 20 task của 3 repo đã qua F0 (prettytable, gunicorn, một repo theo A7); khoảng 0,3 USD mỗi repo.
- **Bước 2:** chỉ chạy nếu có repo đạt tỉ lệ nền ≥ 0,4 (ngưỡng đặt trước); phép dùng lại hai phía, n = 100, khoảng 3–4 USD.
- **Dừng:** không repo nào đạt thì ghi lại, không chạy bước 2.

### Gói C: quyết định khả năng vào A*

**S2. Bộ học viết chỉ dẫn rò rỉ khi nào: phép thử liều–đáp ứng** (W2) — khuyên làm nhất
- **Giả thuyết đặt trước (từ D2):** bộ học viết chỉ dẫn đọc lịch sử ở repo có **nhiều** task không mô tả issue, và không viết ở repo có **ít**.
- **Chọn repo bằng quy tắc** (sau A7; không chọn tay):
  - điều kiện: có ≥ 350 task, F0 đạt trên 30 task;
  - 2 repo có tỉ lệ task không mô tả cao nhất và 2 repo thấp nhất; hòa thì theo tên.
  - Pygments (7%) là ứng viên tự nhiên của nhóm thấp.
- **Lượt học hai giai đoạn** (sửa G2):
  - chạy 300 metric call;
  - chưa có dòng nào khớp quy tắc lịch sử của §29 thì `--resume` tới 600;
  - đã có thì dừng (đủ để trả lời endpoint).
- **Endpoint (đếm bằng máy):** có hay không ứng viên khớp quy tắc lịch sử.
- **Chi phí:** mỗi repo 5,1–6,4 USD nếu dừng ở 300; 11,0–12,3 USD nếu chạy đủ 600 (`s25_learn_ledger_h1/h2`, `s30_learn_ledger_h1/h2`).
  - Giai đoạn 1 (1 repo cao, 1 repo thấp): 11–24 USD.
  - Giai đoạn 2 (thêm 2 repo): 11–24 USD.
- **Thành công:** dự đoán đúng ở cả 4 repo. Cộng Jinja, Bleve và lượt học sạch, paper có 7 lượt học cùng chỉ về một cơ chế.
- **Nếu dự đoán sai:** vẫn báo cáo; khi đó paper nói "hiện tượng có ở k/6 repo" và bỏ lời giải thích bằng tỉ lệ task không mô tả.
- **Dừng:** sau giai đoạn 1, nếu repo "cao" không có chỉ dẫn sau 600 metric call thì dừng S2 và báo @thuthuy.

**S3. Từ task tổng hợp sang issue thật của cùng repo** (W3, W5) — khuyên làm
- **Repo:** `conan-io/conan`: 978 task SWE-smith, 165 issue thật trên SWE-bench-Live; harness Live đã dùng ở E2 và T4.
- **Thiết kế:**
  - học skill (gskill, môi trường gốc);
  - chứng nhận trên 100 task tổng hợp;
  - chạy hai nhánh trên **100 issue thật**, cùng lúc.
- **Power** (mô phỏng 20.000 lần, kiểm định dấu một phía, α = 0,025):
  - tác dụng như phần thật của Jinja (20% cặp lợi, 3% cặp hại): 0,77 ở n = 60; **0,96 ở n = 100**;
  - tác dụng bằng một nửa: 0,57 ở n = 100; 0,83 ở n = 165.
- **Chi phí:**
  - học: 11,0–12,3 USD;
  - chấm tổng hợp: 3,3 USD;
  - issue thật: 100 × 2 × 0,063 = 12,6 USD (trung bình của E2; task conan có thể dài hơn, cần đo thử 10 task, khoảng 1,3 USD);
  - tổng khoảng 27–29 USD.
- **Thành công:** một kết luận về scope trên repo thật, dù chiều nào.
  - Chứng nhận trên task tổng hợp mà không giúp trên issue thật: bằng chứng mạnh nhất cho "scope before reuse".
  - Giúp cả hai: bằng chứng rằng chứng nhận có ích ngoài task tổng hợp.
- **Dừng:** đo thử cho tỉ lệ nền < 0,10 thì không chạy.

**S1b. Đổi model reflection** (W1; khi chưa có model khác hãng)
- Một lượt học hai giai đoạn trên Jinja, model reflection là Flash.
- Câu hỏi: chỉ dẫn rò rỉ có phụ thuộc model viết skill không?
- Chi phí: 5–12 USD; phần reflection rẻ hơn bản gốc.

**S1c. Model khác hãng** (W1, đầy đủ)
- Chỉ lập thiết kế chi tiết khi Mistral Small 3.1 có quyền truy cập.
- Thiết kế tối thiểu: như S1a, 34 task; đo thử 5 task trước (ước tính cũ ở §26: khoảng 0,33 USD mỗi lượt).

---

## 5. Làm xong thì paper được nói gì (bậc thang tuyên bố)

| Sau khi xong | Câu paper được viết | Điểm yếu còn lại |
| --- | --- | --- |
| Hiện tại | "Ở hai repo, một bộ học viết chỉ dẫn khai thác rò rỉ; bịt rò rỉ rồi học lại cho skill sạch được chứng nhận." | W1–W6 |
| Gói A | Thêm: "Trên 20 luồng thật có nhãn, quy tắc X nhận nhầm k luồng, Gatekeeper nhận nhầm 0"; "một phép kiểm anytime-valid cho phần do môi trường"; "bộ theo dõi phát hiện khai thác mà không cần chạy lại"; "p% task của benchmark nằm ở vùng phơi nhiễm". | W1, W2, W3, W5, W6 |
| Thêm B1, S1a | Thêm: "lặp lại với seed thứ hai"; "hai model của một hãng". | W2, W3, W5 |
| Thêm S2 | Thêm: "bộ học viết chỉ dẫn rò rỉ ở repo có nhiều task không mô tả và không viết ở repo có ít (dự đoán đặt trước, m repo)". | W3 |
| Thêm S3 | Thêm: "chứng nhận trên task tổng hợp [có / không] mang sang issue thật của cùng repo". | W1 (khác hãng) |

---

## 6. Ngân sách theo bậc

| Bậc | Gồm | Dự kiến | Cộng dồn |
| --- | --- | --- | --- |
| 0 | Gói A, B3 | 0 | 0 |
| 1 | B1, S1a (gồm đo thử) | 6,7 + 4,4 = 11,1 USD | 11 |
| 2 | S2 giai đoạn 1 | 11–24 USD | 22–35 |
| 3 | Đo thử conan, S3 | 1,3 + 27–29 USD | 50–65 |
| 4 | S2 giai đoạn 2 | 11–24 USD | 61–89 |
| Tùy chọn | B2, S1b | 4–5; 5–12 USD | |

Mọi bậc có phí cần trần GCP được nâng trước.

---

## 7. Lịch đề xuất (hạn ASE 2027 chưa công bố; TODO giả định cuối 5/2027, phải xác nhận khi có CfP)

| Thời gian | Việc | Mốc kiểm |
| --- | --- | --- |
| 13–22/11 | Gói A (A1, A2 kèm đăng ký §32, A6, A7, B3) | Bảng luồng thật; bảng phơi nhiễm; §32 đã commit |
| 23–30/11 | Bậc 1 (B1, S1a); A3 bản đầu | Δ_leak lần hai; paper bản tái cấu trúc |
| 12/2026 | Bậc 2 (S2 giai đoạn 1); quyết bậc 4 | Dự đoán liều–đáp ứng đúng hay sai ở 2 repo |
| 01/2027 | Bậc 3 (S3) | Kết quả issue thật |
| 02/2027 | Viết bản đầy đủ; đóng băng thí nghiệm | Bản thảo hoàn chỉnh |
| 03/2027 | Phản biện thử (thầy, một người biết thống kê; mục đang mở trong TODO) | Danh sách sửa |
| 04/2027 | Artifact ẩn danh; A4 | Gói nộp |

---

## 8. Rủi ro và cách xử lý

| Rủi ro | Dấu hiệu | Xử lý |
| --- | --- | --- |
| Trần chi tiêu GCP | 403 "Spend cap breached" (A124) | @thuthuy nâng trần trước bậc 1; mỗi workflow dừng ngay ở lỗi 403 đầu tiên (đã sửa ở A124) |
| Model sau cùng một tên đổi theo ngày | phép kiểm §5 từng không đạt (74–75/109) | Mọi phép so xác nhận chạy hai nhánh cùng lúc; so khác ngày chỉ là mô tả |
| Lượt học chạm trần giữa chừng | A107, A108, A125 | Trần = chi phí đo + 1 lượt xấu nhất; lượt học dở không được chấm như đã đủ |
| Kết quả ngược dự đoán (S2, S3) | — | Diễn giải đặt trước cho cả hai chiều; báo cáo đủ; không chạy thêm để gỡ |
| Bị công bố trùng | bài mới về skill và rò rỉ benchmark | Đưa arXiv sớm (@thuthuy quyết, tùy chính sách double-blind) |
| Quá nhiều nội dung cho 10 trang | paper hiện 9 trang | A3 chuyển phần phụ xuống phụ lục trước khi thêm kết quả mới |

---

## 9. Cần @thuthuy quyết

1. **Nâng trần chi tiêu GCP** (quyền: tài khoản). Không nâng thì chỉ làm được bậc 0.
2. **Chọn bậc** (quyền: ngân sách mới, thêm thí nghiệm).
   - **Ảnh hưởng:**
     - Bậc 0–1 làm chắc những gì đã có.
     - Bậc 2–3 là phần biến "một trường hợp ở hai repo tổng hợp" thành "một cơ chế có dự đoán, kiểm trên repo thật".
   - **Lời khuyên:** duyệt bậc 0–2 ngay (tối đa khoảng 35 USD); quyết bậc 3 sau khi có số đo thử conan (1,3 USD).
3. **Mở lại mục model thứ hai cho S1a** (quyền: thêm thí nghiệm; đang tạm ngưng theo lệnh 07/11).
4. **Quyền truy cập Mistral Small 3.1** (quyền: tài khoản). Tình trạng yêu cầu hiện ra sao?
5. **arXiv trước khi nộp, và báo tác giả gskill** (quyền: công bố, liên hệ bên ngoài).

**Hạn cần trả lời:** mục 1–3 trước 15/11. Gói A tôi bắt đầu được ngay khi @thuthuy đồng ý, vì không tốn tiền.
