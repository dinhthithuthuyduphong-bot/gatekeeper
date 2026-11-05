# Đánh giá repo `-gatekeeper-p6` để tìm phần dùng lại được (05/11/2026)

**Phạm vi đọc** (bản sao chỉ đọc, commit `5edebe8`):
- `README_VI.md`, `EVIDENCE_LEDGER.md`;
- `research_closure/RESULT*.md`, `PAPER_EXPECTATION_AUDIT.md`, `ERRATA_20261026.md`;
- file kết quả của các Study Q, R2, T, T2, U, V;
- `model_reviews/MOCK_REVIEWS.md`.

**Chưa đọc hết:** các study từ B tới P chỉ đọc qua sổ bằng chứng. Mọi con số dưới đây chép từ file kết quả của p6, chưa chạy lại.

## 1. p6 đã làm gì

| Nhóm | Skill | Target và "draw" | Kết quả chính (theo file) |
| --- | --- | --- | --- |
| B–K, D/E/G (đăng ký trước) | 2 họ biến đổi AST viết tay (`negative_type_guard`, `none_identity`) | 14 target trên repo thật; draw = đầu vào sinh từ oracle viết tay | D: Gatekeeper admit 2 ô (đều có lợi), B2/B6-R/B8 admit 12 ô. E: 3 ô có hại, Gatekeeper REJECT sau 2 draw, B6-R ADMIT |
| H (thống kê) | Mô phỏng | 50 họ × 6 ô | Fixed-200 với IUT/Holm **tốt hơn** Gatekeeper ở mức hại 2–3%, với ít draw hơn. Đánh đổi, không trội |
| P/Q | Patch LLM đã resolved trên SWE-bench Verified | 694 patch; draw = đầu vào sinh ở mức hàm | 43,1% khác hành vi so với bản fix; **11,1% hồi quy theo hợp đồng**; hệ số phóng đại theo định nghĩa oracle 3,88. HQ1 không được ủng hộ |
| R/R2 (ghép) | 12 họ quy tắc viết tay | 16 target | 18/136 cặp họ có footprint giao nhau. **2 cặp file có footprint rời nhau nhưng không giao hoán** (cùng một cặp họ). Không đo tác hại của ghép |
| T, T2, V | **Quy tắc autofix của Ruff** (skill "có trên thị trường") | 60 + 60 dự án PyPI tải nhiều nhất | T: 1.559 ô dùng được, 12 có hại. T2: 3.626 ô, 29 có hại |
| U | Patch LLM | 693 patch | Có vùng "hại một phần" (5–20% số draw): 33 patch theo hợp đồng |

## 2. Lời phê bình: phần nào p6 đã tự xác nhận

1. **Định lý:** p6 tự ghi hai lỗi (`PAPER_EXPECTATION_AUDIT.md`):
   - hệ số 2 ở cận TV (đúng như bản sửa R12 của repo này);
   - Định lý 7 không thể đúng với mọi ε < θ.
   - Sổ α cho skill ghép dùng hệ số 1/C(N, m), khiến ngưỡng chứng nhận lên rất cao khi thư viện lớn (review W3).
2. **Ngữ nghĩa mơ hồ:** chữ "draw" lúc là đầu vào sinh ở mức hàm, lúc là draw của oracle viết tay, trong khi giả định là task i.i.d. Hàm loss có hệ số 0,5 nhưng không đi vào quyết định (review W3, W4).
3. **Lệch động cơ:** paper nói về skill của agent (Voyager/GSE), nhưng đánh giá trên 2 biến đổi AST viết tay và 12 quy tắc kiểu linter.
4. **Trình bày:** đọc như nhật ký phòng thí nghiệm, quá nhiều mã study.
5. **Về "review":** file `MOCK_REVIEWS.md` do **model sinh ra**, không phải người review. Các đánh giá "accept / strong accept" trong đó **không phải bằng chứng** và không được dùng.

## 3. Phần có giá trị thật, đánh giá không thiên vị

### 3a. T, T2, V: quy tắc Ruff trên 120 dự án PyPI (dữ liệu lớn nhất, nhãn tách khỏi cổng)

Chỉ tính các ô Ruff. T: 11 ô hại, 1.520 ô an toàn. T2: 20 ô hại, 3.528 ô an toàn.

| Quy tắc | T: hại admit | T2: hại admit | T: an toàn giữ lại | T2: an toàn giữ lại | Draw trung bình (T / T2) |
| --- | --- | --- | --- | --- | --- |
| Replay + fingerprint (B6R, baseline quyết định của paper gốc) | **9** | **17** | 996 | 2.342 | — |
| LLM judge (T2: 19 ô hại được chấm) | 6 | 10 | 1.128 | 2.520 | 1 lời gọi |
| Nhãn `safe` của chính Ruff (RS) | 0 | **3** | 677 | 1.622 | 0 |
| Smoke test 20 draw (S20) | 0 | 1 | 1.518 | 3.523 | 20 / 20 |
| Gatekeeper (G) | 0 | 0 | 1.512 | 3.505 | khoảng 199 / 238 |
| G_FDR | 0 | 0 | 1.517 | 3.517 | — |
| B8 (chạy hết draw) | 0 | 0 | 1.506 | 3.508 | khoảng 200 / 239 |

**Đọc trung thực:**
- **Đúng câu hỏi RQ1 của paper gốc:** replay + fingerprint nhận nhầm hầu hết ô có hại (9/11, 17/20). Đây là bằng chứng thật cho động cơ "replay không đủ".
- Nhưng **mọi cổng dùng bằng chứng trên target** (S20, B8, Gatekeeper) đều gần 0. Ở T và V, smoke test 20 draw **trội** Gatekeeper: ít draw hơn khoảng 10 lần, cùng 0 ô hại. Tiêu chí W1 (an toàn) và W3 (chi phí) của chính p6 **không đạt** ở T và V; ở T2, W1 đạt (S20 nhận 1 ô hại) nhưng W3 vẫn không đạt.
- **Kết luận:** với biến đổi mã tất định, tác hại hiếm (khoảng 0,8% số ô) và hầu như tất định, nên thống kê tuần tự **không cần thiết**.

### 3b. U: patch LLM có tác hại một phần

- Theo hợp đồng: có 33 patch ở vùng hại 5–20%.
  - S20 nhận nhầm **10/33**. G, G_FDR và B8 nhận 0.
  - G chỉ giữ lại 303/649 patch an toàn, còn G_FDR giữ 626 và B8 giữ 621.
- **Kết luận:** khi tác hại là một phần (không tất định), smoke test thất bại thật. Cổng tuần tự dạng FDR ngang B8 ở chi phí gần bằng, chứ không rẻ hơn rõ rệt.

### 3c. Q: kết quả đo phụ thuộc định nghĩa oracle

- Trong 694 patch resolved, 11,1% là hồi quy theo hợp đồng; nếu đếm mọi khác biệt so với bản fix thì là 43,1%, gấp 3,88 lần.
- **Cảnh báo tính mới:** mình nhớ đã có công trình về "patch qua test SWE-bench nhưng sai hành vi", nhưng **chưa kiểm** (R1). Phải tìm và đọc bản gốc trước khi dùng.

### 3d. R2: một ví dụ thật cho tương tác khi ghép

- 2 cặp file có footprint rời nhau nhưng không giao hoán, xảy ra trên repo thật (pycubrid, pydal). Đây là ví dụ thật cho việc kiểm tra chỉ dựa trên footprint là không đủ.
- **Nhỏ:** chỉ một cặp họ, skill viết tay, không đo tác hại.

## 4. "Ánh sáng" cho paper hiện tại

| # | Ý | Dữ liệu thật ở cả hai repo | Rủi ro |
| --- | --- | --- | --- |
| A1 | **Bản đồ chế độ:** loại cổng cần dùng phụ thuộc vào việc kết quả trên mỗi draw có tất định không. Biến đổi mã tất định (p6 T/T2): smoke test là đủ, còn replay và LLM judge thì không. Skill mức agent (repo này E1/E2/T4): hiệu ứng nhỏ so với nhiễu, nên cần cổng có bảo đảm. Theo dõi liên tục phá cổng cỡ mẫu cố định | Có ở cả hai | Hai miền khác nhau, review đã chê là rời rạc. Phải có một câu hỏi chung và **một** định nghĩa draw/trial dùng cho cả hai |
| A2 | **Động cơ cho RQ1 gốc:** replay + fingerprint nhận 9/11 và 17/20 ô có hại trên quy tắc Ruff thật | Có (p6) | Đó là B6R do p6 tự dựng, không phải GSE thật. Ghi rõ như B-X2 ở repo này |
| A3 | **Chủ đề "endpoint quyết định con số":** Q (hệ số 3,88); repo này có A76 (loss == 0 so với < 0,5) và nghi PASS_TO_PASS chập chờn | Có ở cả hai | Có thể trùng với công trình về patch "plausible" (chưa kiểm) |
| A4 | Ví dụ ghép không giao hoán (R2) | p6 | Nhỏ, không có tác hại |

**Không dùng được, hoặc không nên dùng:**
- Mock review.
- Các phân tích hậu kiểm của p6 (T-A5 B6-strong, U-A1 e-BH) như thể chúng là kết quả xác nhận. Riêng T2 đã đăng ký trước chúng.
- Các định lý chưa sửa.
- Mọi kết quả "demo" (CONSTRUCTED_DEMO_FIXTURES).

**Thiên vị cần tránh:**
- p6 thua ở W1 và W3 trong T và V, ở W3 trong T2, và thua Fixed-200 trong H. Nếu dùng p6 thì phải báo cáo các kết quả thua này.
- Không được chỉ lấy dòng "B6R nhận 17/20".

## 5. Kết luận

**Có ánh sáng, nhưng là ánh sáng về định vị, không phải một kết quả thắng.**
- Dữ liệu của hai repo cho cùng một câu trả lời trung thực: cổng thống kê chỉ cần khi kết quả trên mỗi draw có nhiễu. Ở biến đổi tất định, một smoke test rẻ là đủ. Ở skill mức agent, nhiễu chiếm ưu thế, và các quy tắc phổ biến hỏng khi bị theo dõi liên tục.
- Đây có thể là trục chính của paper. Nó trả lời "khi nào cần gì" bằng số đo, thay vì "Gatekeeper thắng".
- **Chưa chốt:** phải làm xong việc rà tài liệu (`docs/strategy_review.md` §5b), gồm cả công trình về patch "plausible", và kiểm A1 có bị trùng không.
