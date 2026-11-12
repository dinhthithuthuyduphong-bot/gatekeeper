# Kế hoạch cải tiến để paper đạt mức A* (bản 1, 12/11/2026; chờ @thuthuy duyệt)

**Phạm vi rà soát:**
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

### 0.1 Các lần chạy
- Không có workflow nào đang chạy hoặc đang chờ, trừ một lần build Pages bị kẹt từ 06/11 (vô hại).
- Lần chạy có phí cuối cùng là §30, chạy bù `evalrest` (run 42858029048, xong 10/11).
- Từ 10/11 đến 11/11, một phiên khác (`session_01HnEHQ…`) đã:
  - hoàn tất §30: học lại skill khi đã bịt rò rỉ;
  - thêm §31: đọc theo FWER, thứ tự task, độ nhạy theo θ, chi phí admit lại;
  - trả lời hai bản phản biện (11/11).
- Paper và CI đều xanh.

### 0.2 Kết quả §30 (mới, quan trọng)
- Skill học lại trong môi trường một commit **không có chỉ dẫn đọc lịch sử nào**: 0/8 ứng viên được giữ có chỉ dẫn này.
- Skill đó **được chứng nhận**:
  - 33 so với 16 task giải được; p = 2,4·10⁻⁴; mức tăng +0,17 [0,08; 0,26];
  - Gatekeeper admit sau 65 task.
- Mức tăng của nó không khác phần mức tăng thật của skill gốc: hiệu số −0,04 [−0,13; 0,05].
- Đem sang môi trường còn rò rỉ, skill này giải 1/34 task không có mô tả, so với 15/34 của skill gốc.
- Như vậy paper đã đi từ "chẩn đoán" sang "chẩn đoán cộng biện pháp sửa".

### 0.3 Chi tiêu và ràng buộc
- Đã chi:
  - từ 06/11: §22–§23: 7,18; Bleve: 15,88; MemGovern: 5,28; §27: 5,77; §29: 2,98; §30: 14,66 USD;
  - trước đó: E2 43,04 USD; E1 và thí nghiệm chính theo sổ trong `CLAUDE.md`.
- **Chặn mọi lần chạy có phí:** project GCP đã chạm **trần chi tiêu đặt ở phía tài khoản** (A124, lỗi 403 "Spend cap breached for project"). Muốn chạy tiếp, @thuthuy phải nâng trần đó trong Google Cloud Billing. Đây là việc tài khoản, thuộc quyền @thuthuy.
- **Model khác hãng chưa truy cập được:** hạn mức Claude bị từ chối; yêu cầu model open-weight đang chờ. Đây là điểm yếu bị cả ba phản biện nêu.

---

## 1. Vị trí so với mức A*

ASE thuộc hạng A* theo CORE, nên đích hiện tại (ASE 2027, hạn dự kiến cuối 5/2027) đã là A*. Câu hỏi là paper còn thiếu gì so với mức chấp nhận ở đó.

### 1.1 Điểm mạnh đã có (cả ba phản biện đồng ý)
- **Phát hiện mới, có chuỗi nhân quả nhiều tầng:**
  - bộ học tự viết chỉ dẫn khai thác rò rỉ;
  - đo được rò rỉ chiếm bao nhiêu mức tăng, qua bốn đường độc lập: bỏ lịch sử, bỏ chỉ dẫn, trace, học lại;
  - lặp lại ở repo thứ hai (Go).
- **Có biện pháp:** học lại khi đã bịt rò rỉ cho ra skill sạch và được chứng nhận (§30).
- **Quy trình chặt:** đăng ký trước, đối chứng cho chính phép đo, nêu cả kết quả thất bại (MemGovern), dữ liệu gốc công khai.

### 1.2 Điểm yếu còn lại, xếp theo mức nguy hiểm khi phản biện A*

| # | Điểm yếu | Ai nêu | Tình trạng |
| --- | --- | --- | --- |
| W1 | Một họ model cho agent; một model reflection | cả ba | mở; bị chặn ở quyền truy cập |
| W2 | Một pipeline học, một lượt học mỗi điều kiện: "bộ học viết chỉ dẫn rò rỉ" mới là một quan sát, không phải một tỉ lệ | 10/11, 11/11 | mở |
| W3 | Chỉ task tổng hợp (SWE-smith), ba repo; chưa có repo thật | cả ba | mở |
| W4 | Gatekeeper chưa được so với các quy tắc khác **trên luồng thật**, chỉ trên A/A | 11/11 | mở; làm được miễn phí |
| W5 | Tỉ lệ giải nền thấp (5–17/100): đo được lợi, gần như không đo được hại | 11/11 | mở |
| W6 | Một seed mỗi nhánh | cả ba | mở |
| W7 | Lý thuyết "trang trí": Theorem 1 là Ville cộng chặn hợp; Gatekeeper là aGRAPA đã có | 10/11 | đã hạ giọng một phần |
| W8 | Thông điệp loãng: bộ chấm, quy lỗi, MemGovern, mức nhiễu chen vào trục chính | 10/11 | mở; làm được miễn phí |
| W9 | Lời hứa trung tâm của bản thảo gốc chưa thực hiện: so với baseline quyết định (replay verification cộng fingerprint) theo harm–coverage | bản thảo gốc | đã bỏ (Phase 4/6 không kham nổi) |

---

## 2. Khoảng cách với bản thảo gốc và TODO gốc

| Lời hứa của bản thảo gốc | Hiện trạng | Có khôi phục được không |
| --- | --- | --- |
| SkillShift-SE: 180 cặp, 25 repo, nhãn hại | Bỏ (Phase 4): 540–1.180 USD | Không. Thay bằng phép đo phổ ở mục S2 |
| RQ1: so với replay cộng fingerprint, harm–coverage | Bỏ (Phase 6) | **Một phần, miễn phí:** so các quy tắc trên luồng thật đã có (A1) |
| RQ2: composition | Đã cắt khỏi paper (08/11) | Không: chưa có cặp skill thật cùng vùng mã |
| Định lý admit cho scope chọn thích nghi, có dịch chuyển | Có, kèm điều kiện pool hữu hạn (11/11) | Đủ |
| Thu hồi (retirement) | Chỉ có plasmode (§15) | Một phần (B3) |
| Uncertainty-directed validation | Không | Không cần cho định vị mới |

**Kết luận phần 2:** định vị hiện tại ("bộ học biến lỗi môi trường thành chỉ dẫn; vì vậy phải chứng nhận theo scope, dưới đối chứng") đã thay cho định vị gốc. Không nên cố khôi phục SkillShift-SE. Lời hứa đáng khôi phục là phép so "quy tắc nào bắt được, quy tắc nào bỏ sót", và làm được trên dữ liệu đã có.

---

## 3. Tài sản trên các nhánh (dùng lại được)

| Nhánh | Nội dung | Dùng cho |
| --- | --- | --- |
| `main` | Paper, §24–§31, mọi script phân tích | Mọi việc |
| `trial` | Lượt học Bleve, §27 (placebo, Pygments, trace) | Đã gộp vào `main` |
| `pilot-snapshots` | Kết quả gốc của §25–§30, hai lượt học Jinja đầy đủ (`s25_learn_run`, `s30_learn_run`) | A1, A2, S2 |
| `raw-archive` | Trace và log gốc của E1, E2, T4 | A1 (luồng thật), B3 |
| `e2-results`, `s28-results`, `rescore-results` | Kết quả E2 và các lần chấm lại | A1 |
| `data-snapshots` | Dòng task SWE-smith và Live, census 222 repo | S2, S3 |
| `sources-snapshots` | Bản gốc của 45 nguồn trích dẫn | Viết |

---

## 4. Kế hoạch

Mỗi mục ghi:
- điểm yếu nó trả lời;
- thiết kế;
- tiêu chí thành công;
- chi phí;
- rủi ro;
- ai quyết.

### Gói A: miễn phí, tôi làm được ngay (khoảng 3–5 ngày làm việc)

**A1. So các quy tắc admit trên luồng thật** (trả lời W4, một phần W9)
- **Thiết kế:**
  - Lấy mọi luồng ghép cặp đã chạy: 7 lần admit của §25–§30, Pygments, placebo so với không skill, A/A thật của E1/E2, nhánh có hại của E1, T4.
  - Áp lên đúng các luồng đó, theo đúng thứ tự task: Gatekeeper, plug-in một lần và có giám sát, cổng Mantel–Haenszel, luật GEPA, quy tắc lặp lại 2/3 seed, Library Drift (N_min = 100).
  - Gán nhãn "nên nhận / không nên nhận" bằng một quy tắc đặt trước, không dùng chính các quy tắc đang so. Ví dụ: nhãn dương khi tác dụng thật được xác nhận bởi một lượt chạy độc lập (học lại, seed khác, bỏ chỉ dẫn).
- **Thành công:** một bảng quyết định từng quy tắc trên từng luồng. Gatekeeper không nhận Pygments, A/A hay placebo, và nhận các luồng có tác dụng thật; các quy tắc khác nhận nhầm ít nhất một luồng.
- **Rủi ro:** chỉ khoảng 15–20 luồng, nên là phép minh họa, không phải ước lượng tỉ lệ. Phải ghi là thăm dò, đăng ký trước quy tắc gán nhãn.

**A2. Một e-process cho phần do rò rỉ** (trả lời W7: thêm một đóng góp phương pháp thật)
- **Thiết kế:**
  - Chứng nhận anytime-valid cho hiệu số giữa hai môi trường: Z_i = (Z_i ở môi trường gốc) − (Z_i ở môi trường một commit), Z_i ∈ [−2, 2], tính trên cùng task.
  - Phát biểu và chứng minh tính hợp lệ: cùng cấu trúc với Proposition 1, thang [−2, 2] đổi về [−1, 1].
  - Áp lên dữ liệu đã có của Jinja và Bleve.
- **Thành công:** paper có một phép kiểm anytime-valid cho "phần mức tăng do môi trường". Đây là thứ phép kiểm skill đơn lẻ không làm được, và trả lời trực tiếp lời chê "Gatekeeper chỉ là aGRAPA".
- **Rủi ro:**
  - Với n = 100 và hiệu số khoảng 0,17, phép kiểm có thể không đạt ngưỡng; khi đó báo cáo đúng như vậy.
  - Cần đăng ký trước (§32), trước khi tính trên dữ liệu thật. Lưu ý: dữ liệu này đã được nhìn ở dạng khoảng bootstrap.

**A3. Tái cấu trúc paper quanh một trục** (trả lời W8, W7)
- **Trục:** "Một bộ học skill biến lỗi của môi trường đánh giá thành chỉ dẫn → chứng nhận phải gắn với scope và với đối chứng → bịt lỗi rồi học lại cho skill sạch".
- **Chuyển xuống phụ lục:** auditor LLM, MemGovern, so với mức tăng đã công bố, SWE-Skills-Bench ρ.
- **Đưa lên đầu:** "đối chứng một commit mới bắt được rò rỉ; e-process không bắt được" (hiện ở cuối mục Results).
- **Gộp:** Sample Complexity vào Evaluation Design.
- **Lý thuyết:** nói thẳng đóng góp là áp dụng e-process cho cặp, pool hữu hạn và hiệu số giữa môi trường (A2), không phải một bất đẳng thức mới.
- **Thành công:** abstract dưới 200 từ; mỗi RQ có một câu kết luận; phần 1–2 đọc được bởi người không chuyên thống kê.

**A4. Kiểm lại toàn bộ theo yêu cầu của ASE**
- Số trang, mẫu IEEE, double-blind (ẩn tên repo GitHub, link artifact ẩn danh), mục Data Availability.
- Gói artifact ẩn danh (Zenodo hoặc anonymous.4open.science); kiểm license của từng thứ được phân phối lại.
- Thu hồi khóa `0cf3193a`; việc này đang mở trong TODO.

**A5. Phân tích "vì sao skill sạch giúp"** (một phần W1, W2; thăm dò)
- So nội dung skill gốc và skill học lại theo nhóm chỉ dẫn, và so quỹ đạo của các task chỉ skill sạch giải được.
- Mục đích: chỉ ra phần nội dung thật mà bộ học tìm được khi không có lối tắt.

### Gói B: có phí, rẻ, tăng độ chắc của kết quả đã có (khoảng 10–15 USD)

**B1. Seed thứ hai cho bốn nhánh Jinja** (trả lời W6)
- Môi trường gốc và môi trường một commit, có và không skill, chạy cùng lúc, seed 51.
- **Chi phí:** dự kiến 6,7 USD (`f1_probe` 1,44 + `f1_skill_probe` 1,94 + `s25_leakfree_none` 1,46 + `s25_leakfree_skill` 1,87); trần 8,0.
- **Thành công:** Δ_leak đo lần hai, độc lập; gộp hai seed thì khoảng tin cậy hẹp hơn.

**B2. Tỉ lệ giải nền và tác hại trên repo có tỉ lệ nền cao** (trả lời W5)
- **Bước 1:** đo thử nhánh không skill trên 20 task của 3–4 repo SWE-smith có F0 đạt (prettytable, gunicorn, và repo khác theo census). Khoảng 0,3 USD mỗi repo.
- **Bước 2:** chọn repo có tỉ lệ nền ≥ 0,4 (quy tắc đặt trước). Chạy phép dùng lại skill Jinja hai phía, n = 100. Khoảng 3–4 USD, theo chi phí của 27b.
- **Thành công:** phép dùng lại có power để phát hiện tác hại. Kết luận "chứng nhận không mang sang" không còn dựa vào một repo có tỉ lệ nền 5/100.

**B3. Thu hồi trên luồng thật** (một phần W9)
- Một skill đã được admit, rồi đổi scope. Chạy e-detector (Qu et al.) và quy tắc thu hồi hai bước của §15 trên luồng của scope mới.
- Có thể dùng luồng Pygments và luồng skill sạch đem sang môi trường còn rò rỉ, đều đã có: **0 USD**. Chỉ tốn tiền nếu cần thêm task.

### Gói C: có phí, quyết định khả năng vào A* (khoảng 35–60 USD)

**S2. Phổ của hiện tượng qua nhiều repo** (trả lời W2, và W1 ở tầng bộ học) — **khuyên làm nhất**
- **Câu hỏi:** bộ học có viết chỉ dẫn khai thác rò rỉ ở **bao nhiêu repo**, không chỉ ở Jinja và Bleve?
- **Thiết kế:**
  - Nửa đầu lượt học của gskill (300 metric call) trên 4–6 repo SWE-smith khác, chọn bằng quy tắc đặt trước từ census: F0 đạt, đủ 350 task, khác ngôn ngữ nếu có.
  - Lý do chỉ cần nửa đầu: ở Jinja, chỉ dẫn xuất hiện ngay ở bản viết lại thứ hai.
  - Endpoint: có hay không một dòng khớp quy tắc lịch sử của §29 trong các ứng viên sau 300 metric call. Đếm bằng máy.
- **Chi phí:** nửa đầu ở Jinja tốn 6,36 (`s25_learn_ledger_h1`) và 5,14 USD (`s30_learn_ledger_h1`). Sáu repo khoảng 31–38 USD; bốn repo khoảng 21–26 USD.
- **Thành công:** "ở k trên m repo, bộ học viết chỉ dẫn đọc lịch sử", kèm khoảng tin cậy Clopper–Pearson. Một quan sát trở thành một tỉ lệ.
- **Rủi ro:** k có thể nhỏ. Kết quả đó vẫn có giá trị (hiện tượng phụ thuộc repo) và phải được báo cáo.

**S3. Từ task tổng hợp sang issue thật của cùng repo** (trả lời W3) — **khuyên làm**
- **Câu hỏi:** skill học và được chứng nhận trên task SWE-smith của một repo có giúp trên **issue thật** của chính repo đó không?
- **Thiết kế:**
  - Repo `conan-io/conan`: 978 task SWE-smith, 165 task thật trên SWE-bench-Live; harness và image Live đã dùng ở E2 và T4.
  - Học skill gskill (hoặc chỉ nửa đầu), chứng nhận trên task tổng hợp, rồi chạy hai nhánh trên 60–100 task Live thật.
  - Lưu ý: task Live không có commit "Bug Patch", nên đây cũng là phép thử "chỉ dẫn rò rỉ có hại ở môi trường thật không".
- **Chi phí:** cần đo thử trước.
  - Học: 11–12 USD (hai lượt Jinja: 12,25 và 10,99).
  - Chấm tổng hợp: khoảng 3,3 USD.
  - Chấm task thật: trên SWE-bench-Live, một lần chạy tốn khoảng 0,063 USD (đo ở E2 và T4, `docs/preregistration_main.md` §14), nên 60 task × 2 nhánh khoảng 7,6 USD. Task conan có thể dài hơn trung bình, nên cần đo thử.
  - Tổng khoảng 22–23 USD. Bản rút gọn (nửa đầu lượt học, 40 task thật) khoảng 14 USD.
- **Thành công:** một kết luận về scope trên repo thật, trả lời giới hạn lớn nhất về tính tổng quát.
- **Rủi ro:** tỉ lệ nền trên conan Live có thể thấp. Phải đo trước trên 10 task (khoảng 1 USD) rồi mới quyết.

**S1. Model khác hãng** (trả lời W1)
- **Phụ thuộc:** quyền truy cập (Claude bị từ chối hạn mức; yêu cầu open-weight đang chờ). Không lập kế hoạch chi tiết khi chưa có quyền.
- **Thiết kế tối thiểu khi có quyền:** 34 task không có mô tả, có và không skill gốc, model khác hãng làm agent. Câu hỏi: agent khác có làm theo chỉ dẫn đọc git không?
- **Chi phí:** cần đo thử 5 task trước.
- **Phương án thay thế khi không có quyền:** đổi **model reflection** của bộ học sang Flash hoặc Flash-Lite trong một nửa lượt học. Câu hỏi: chỉ dẫn rò rỉ có phụ thuộc vào model reflection không? Khoảng 5–6 USD.

---

## 5. Thứ tự đề xuất và ngân sách

| Bước | Việc | Chi phí | Điều kiện |
| --- | --- | --- | --- |
| 1 | A1, A2 (đăng ký trước §32), A3, A4, A5, B3 | 0 | Không |
| 2 | Nâng trần chi tiêu GCP | — | @thuthuy (tài khoản) |
| 3 | B1 (seed 2) và bước đo thử của B2 | khoảng 7,9 USD | Trần GCP đã nâng |
| 4 | S2 (bốn repo) | khoảng 21–26 USD | @thuthuy duyệt |
| 5 | Đo thử conan Live 10 task, rồi S3 | khoảng 1 + 22 USD | Theo kết quả đo thử |
| 6 | S1 khi có quyền truy cập | đo thử trước | @thuthuy (quyền, tiền) |

- **Tổng gói khuyên** (bước 3 đến 5): khoảng 52–57 USD.
- **Phương án tối thiểu** chỉ gồm bước 1 và 3: khoảng 8 USD. Phương án này sửa W4, W6, W7, W8 và nửa W5, nhưng chưa sửa W1–W3.

---

## 6. Cần @thuthuy quyết

1. **Trần chi tiêu GCP** (quyền: tài khoản).
   - Mọi bước có phí đều bị chặn cho tới khi nâng.
   - Lời khuyên: nâng lên mức đủ cho gói được chọn, cộng 20% dự phòng.
2. **Chọn gói** (quyền: ngân sách mới, thêm thí nghiệm).
   - **Ảnh hưởng:**
     - Gói A cộng B1 làm phần thống kê và trình bày chặt hơn, nhưng các lời chê về tính tổng quát (một model, một bộ học, task tổng hợp) vẫn còn nguyên.
     - S2 và S3 là hai việc duy nhất biến "một trường hợp" thành "một hiện tượng".
   - **Lời khuyên:** duyệt gói A, B1, S2 (bốn repo) và đo thử conan. Tổng khoảng 31 USD, sau đó quyết S3 (khoảng 22 USD) theo số đo thử.
3. **Quyền truy cập model khác hãng** (quyền: tài khoản). Đây vẫn là lời chê số một.
4. **Đưa bản thảo lên arXiv trước khi nộp** (quyền: công bố).
   - Lợi: giữ quyền ưu tiên trong một hướng nghiên cứu đông.
   - Rủi ro: kiểm chính sách double-blind của ASE 2027 khi CfP ra.
5. **Báo tác giả gskill** về rò rỉ và bộ chấm (quyền: liên hệ bên ngoài). Câu hỏi này vẫn đang chờ từ 07/11.

**Hạn cần trả lời:** mục 1 và 2 trước 15/11, để các lượt học (mỗi lượt vài giờ) xong trong tháng 11 và còn thời gian viết.
