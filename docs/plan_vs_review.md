# Đối chiếu thí nghiệm với review và hội nghị đích (lập 18/11/2026)

**Yêu cầu của @thuthuy (18/11):** "Những phần nghiêng về viết paper thì bỏ ở to do list với độ ưu tiên phía sau, giải quyết điểm yếu liên quan tới thực nghiệm và lý thuyết có thể làm paper yếu đi. Đọc hết thí nghiệm đã làm và chuẩn bị làm so sánh với phần review và hội nghị nhắm đến xem plan hợp lý chưa? cần add thêm gì không".

**Nguồn đối chiếu:**
- Bản đánh giá 16/11: `docs/reviews/meta_review_2026-11-16.md`. Đây là tổng hợp mô phỏng do một bộ đánh giá AI tạo, không phải quyết định của hội đồng.
- CFP của EASE 2027 (`sources-snapshots`, `ease_2027_research_cfp`):
  - nhận "Replication studies" và "studies with negative findings or non-significant results";
  - một tiêu chí chấm là "…Transparency: The extent to which the paper includes sufficient information to understand how … data was obtained, analyzed, and interpreted, and how the paper supports independent verification or replication".
  - Bản trích đang lưu không chứa đủ danh sách tiêu chí. Tôi không liệt kê các tiêu chí khác cho tới khi đọc được bản gốc.

## 1. Kiểm kê thí nghiệm

| Nhóm | Thí nghiệm | Trạng thái | Trả lời điểm nào của review |
| --- | --- | --- | --- |
| Phát hiện chính | §25 (Jinja: học, chấm, môi trường một commit), §25 bước 4 (Bleve), §27, §29 (bỏ chỉ dẫn), §30 (học lại không rò rỉ) | Xong | Cốt lõi; R1 cho 4/5 |
| Lặp lại | §33 (seed 2), §35 (36 task mới), C10R (§44, pool 70 task cố định, E = 9.028) | Xong | P0: phép thử 70 task |
| Phạm vi | §34 (agent Flash), Pygments (§27) | Xong | P2: model khác, repo khác |
| Kiểm toán | §41 (mỗi task đúng 3 commit; hai kênh rò rỉ), §36 | Xong | P1: "can thiệp lịch sử" thay cho "rò rỉ thuần" |
| Tách thông điệp và diff | C10 (§43), C10R (§44) | Xong | P2: "giữ lịch sử hợp lệ, chỉ bỏ kênh rò rỉ" |
| Thống kê | §42 (12 quyết định, ngưỡng họ 480), mệnh đề cuối pool (B1–B7) | Xong | P0: Định lý 2, Mệnh đề 3, α |
| Model viết skill khác hãng | §38, A′ | Xong; không model khác hãng nào qua Holm | R3: hành vi chung của bộ học |
| Auditor khác hãng | §39 | Xong | Phụ lục |
| Agent khác hãng | C4′ (§40, POOL B 136 task, 3 agent, lớp `chroot`) | Chờ chạy | P2: họ model khác |
| Bộ học thứ hai | W7-b (§45, XRepoSkill) | Lượt Flash một commit xong (k = 12); bước học chờ chạy thử | Không có trong review; là điểm yếu W7 tự liệt kê |

## 2. Điểm yếu thực nghiệm và lý thuyết còn mở

Sắp theo mức review nhấn mạnh. Các việc thuần viết bài nằm ở mục 5, ưu tiên sau.

| # | Điểm yếu | Review nói | Hiện có | Đánh giá |
| --- | --- | --- | --- | --- |
| **X1** | **Mỗi điều kiện một lượt học** | R3 coi "learning randomness" là mối lo chính; P1 bắt ghi giới hạn; P2 "Repeat learning across seeds" | Một lượt gốc Jinja, một Bleve, một §30. §38 chỉ lặp **bước viết skill** trên quỹ đạo có sẵn | **Lỗ lớn nhất còn lại.** Kế hoạch hiện tại không có việc nào lặp lượt học gskill. Mục D của `kaggle/plan_v4.md` đang bị khuyên dừng (Q7) |
| **X2** | **Môi trường Kaggle chưa được nối với môi trường của paper** | (Không trực tiếp; thuộc tiêu chí "independent verification") | C1 và C5 chứng minh **bộ chấm** cho điểm giống Docker, và agent không thấy gì ngoài image. **Chưa có** phép đo agent chạy trong `chroot` có cho kết quả giống agent chạy trong Docker không | Nếu C4′ cho kết quả khác paper, reviewer sẽ hỏi: do agent khác hay do môi trường khác? Hiện không trả lời được |
| **X3** | Bộ theo dõi trace chưa được đối chiếu với nhãn độc lập | Ghi chú trang 8 của PDF: "nhãn độc lập, ma trận nhầm lẫn; tách thấy thông điệp khỏi dùng thông tin" | §41 tách ba mức (tồn tại, hiển thị, chỉ báo dùng). Chưa có nhãn độc lập | Bộ theo dõi đỡ nhiều kết luận (§41: 0/669 lượt ở môi trường một commit thấy kênh nào; mọi task không mô tả giải được ở môi trường gốc đều có diff "Bug Patch" trong trace: 15/15, 17/17, 20/20). Thiếu kiểm định thì reviewer có thể bác |
| X4 | Bảo đảm thống kê: chứng minh mới chưa ai ngoài nhóm đọc | P0 | Mệnh đề cuối pool có chứng minh, mô phỏng (B7) | 👤 Cần người biết thống kê đọc. Không làm bằng thí nghiệm được |
| X5 | Học với bộ chấm S thay vì L | P2 "compare training scorers S and L" | Chưa | Tùy chọn. Giá trị thấp hơn X1; có thể gộp vào X1 nếu làm |
| X6 | Agent khác hãng | P2 (ghi rõ: không bắt buộc) | C4′ chờ chạy; power 1,00 chỉ đúng nếu agent mới giống agent nghiên cứu | Đã có kế hoạch. Phiên 1 (không hợp lệ) gợi ý Haiku tự tìm ra rò rỉ, nên kịch bản "không bác bỏ" có khả năng cao. Kịch bản đó đã có diễn giải đặt trước (40-5 mục 5) |
| X7 | Mức tăng chỉ theo bộ chấm của benchmark | P1 "benchmark-resolved gains unless independent semantic validation" | Câu chữ đã sửa (D2); §36 có phân tích bản vá đảo ngược chính xác | Đủ cho EASE nếu câu chữ giữ đúng mức |

## 3. Kế hoạch hiện tại có hợp lý không

**Hợp lý:**
- Mọi điểm P0 về thống kê đã được xử lý bằng phân tích, không cần chạy thêm.
- C10, C10R trả lời trực tiếp câu "xóa lịch sử là can thiệp gì".
- §38 và §39 được báo cáo kể cả khi không thuận (EASE nhận kết quả không có ý nghĩa thống kê).
- C4′ có phép thử chính, power và diễn giải đặt trước.

**Chưa hợp lý:**
1. **Thứ tự ưu tiên lệch so với review.** Review nhắc X1 (lặp lượt học) ở hai chỗ và coi là mối lo chính của một reviewer. Nó lại đứng sau C4′ và W7, hai việc review không đòi (C4′ thuộc P2, ghi rõ "do not present this as necessary"; W7 không có trong review).
2. **C4′ thiếu một đối chứng cầu nối (X2).** Không có nó, một kết quả C4′ khác paper không diễn giải được.
3. **Hạn mức Kaggle tháng 11 không đủ cho mọi việc trước mốc đóng băng 01/12.** Đã dùng khoảng 25,7 USD trên 100. Còn lại khoảng 74 USD, nhưng cần:
   - C4′: trần 12 USD mỗi agent, tối đa 36 USD;
   - bước học W7: cận trên thô 20–23 USD, chưa đo;
   - một lượt học gskill (X1): ở §30 tốn 10,99 USD theo giá Vertex; trên Kaggle chưa đo, và cần ít nhất hai lượt (hai môi trường).

## 4. Đề xuất thêm (mỗi mục cần @thuthuy duyệt, vì là thêm thí nghiệm)

### X2′. Đối chứng cầu nối Docker và `chroot` (khuyên làm trước C4′)

- **Câu hỏi:** cùng một model, cùng task, cùng seed: agent chạy trong `chroot` có cho tỉ lệ giải và mức dùng kênh rò rỉ giống khi chạy trong Docker không?
- **Thiết kế:** chạy lớp `chroot` **trên GitHub Actions** (nơi đã có model của paper qua Vertex) với Flash-Lite, seed 41, 34 task không mô tả, nhánh không skill và có skill, môi trường gốc. So với kết quả Docker đã có của đúng các nhánh đó (seed 41 và seed 51).
- **Đạt khi:** chênh lệch chroot − Docker nằm trong khoảng chênh lệch giữa hai seed của Docker (nhiễu chạy lại đo được trên cùng task).
- **Vì sao chạy trên Actions:** Kaggle chỉ có `gemini-3.1-flash-lite-preview`, chưa chắc là cùng model với bản trên Vertex. Đổi môi trường mà giữ nguyên model là cách duy nhất tách được ảnh hưởng của môi trường.
- **Tiền:** tiền Vertex (thật hoặc credit). Chưa đo; sẽ đo bằng lượt thử trước khi xin trần.
- **Nếu không đạt:** C4′ vẫn chạy, nhưng mọi kết luận về agent khác hãng phải ghi "trong môi trường `chroot`, khác Docker ở mức đo được".

### X1′. Lượt học gskill thứ hai cho mỗi môi trường (khuyên làm; trả lời mối lo chính của R3)

- **Câu hỏi:** chỉ dẫn đọc lịch sử có xuất hiện lại khi học lại với seed khác trong môi trường gốc, và không xuất hiện khi học lại trong môi trường một commit không?
- **Thiết kế:** như §25 bước 2 và §30, đổi seed của GEPA, giữ mọi thứ khác. Đại lượng: skill tốt nhất có dòng lịch sử không; mức tăng của skill đó trên 34 task không mô tả.
- **Nơi chạy, hai phương án (một phán đoán giá trị, nên @thuthuy chọn):**

  | Phương án | Ưu | Nhược |
  | --- | --- | --- |
  | Vertex (như §30) | Cùng model, cùng Docker với paper; so được trực tiếp | Tiền thật: khoảng 11 USD mỗi lượt theo §30, hai lượt khoảng 22 USD |
  | Kaggle (lớp `chroot`, Gemini của Kaggle) | Miễn phí | Model là bản preview của Kaggle; cần X2′ đạt; hạn mức tháng 11 không đủ nếu vẫn chạy cả C4′ và W7 |

- **Giới hạn:** hai lượt mỗi môi trường vẫn ít. Đây là bước từ n = 1 lên n = 2, không phải ước lượng phân phối.

### X3′. Kiểm định bộ theo dõi trace bằng nhãn độc lập (0–1 USD; khuyên làm)

- **Thiết kế:**
  - lấy mẫu phân tầng khoảng 60 trace (theo nhánh và theo kết quả của bộ theo dõi);
  - hai bộ gán nhãn độc lập, không thấy kết quả của bộ theo dõi: @thuthuy (hoặc một người khác) và một model khác hãng qua Kaggle;
  - báo ma trận nhầm lẫn, độ đồng thuận, và các ca lệch.
- Cỡ mẫu 60 và chỉ số đồng thuận phải có nguồn trước khi chốt (R2). Sẽ tìm nguồn và đăng ký trước.
- Kéo theo: tách "thấy thông điệp" khỏi "dùng thông tin" theo đúng ghi chú trang 8.

### Không khuyên thêm

- Repo thứ ba hay benchmark khác: review nói P2 không cần.
- X5 (học với bộ chấm S) như một thí nghiệm riêng: chỉ gộp vào X1′ nếu không tốn thêm lượt.

## 5. Thứ tự ưu tiên đề xuất

| Bậc | Việc | Loại |
| --- | --- | --- |
| 1 | C4′ chạy tiếp như đã duyệt (không đổi) | Thực nghiệm, đã duyệt |
| 1 | **X2′ đối chứng cầu nối** (nếu duyệt) | Thực nghiệm |
| 1 | **X1′ lượt học thứ hai** (nếu duyệt) | Thực nghiệm |
| 2 | **X3′ kiểm định bộ theo dõi** | Thực nghiệm, gần như 0 USD |
| 2 | W7: chạy thử (0 USD); bước học chỉ chạy nếu còn hạn mức sau bậc 1 | Thực nghiệm |
| 2 | X4: nhờ người đọc chứng minh | Lý thuyết, 👤 |
| 3 | Viết bài: đưa §38, A′, §39, C4′, W7 vào bài; D10, A5 (khai báo AI), G1 (27 ghi chú PDF), G4 (soát tiếng Anh), các ghi chú hình và bảng | Viết, **làm sau** |
| 3 | Gói tái lập ẩn danh (A4), dựng lại trên máy sạch (F4) | Minh bạch, làm sau nhưng **bắt buộc trước khi nộp** (tiêu chí Transparency của CFP) |

## 6. Cần @thuthuy quyết (hạn: trước 21/11, để còn 10 ngày trước mốc đóng băng 01/12)

**Q8. Có thêm X2′ (đối chứng cầu nối Docker và `chroot`) không?**
- Thuộc quyền @thuthuy: thêm một thí nghiệm, tốn tiền Vertex.
- Ảnh hưởng: không có X2′ thì mọi kết quả C4′ khác paper đều có hai cách giải thích (agent khác hoặc môi trường khác). Có X2′ thì tách được.
- Lời khuyên: **làm**, trước C4′. Tôi sẽ đo chi phí bằng lượt thử miễn phí rồi xin trần.

**Q9. Có thêm X1′ (lượt học thứ hai) không, và chạy ở đâu?**
- Thuộc quyền @thuthuy: thêm thí nghiệm; chọn giữa tiền thật (Vertex) và hạn mức miễn phí (Kaggle, model khác).
- Ảnh hưởng: đây là điểm review nhắc hai lần và là mối lo chính của R3. Không có X1′ thì kết luận "bộ học viết chỉ dẫn" dựa trên một lượt mỗi môi trường.
- Lời khuyên: **làm trên Vertex** (khoảng 22 USD theo §30, sẽ đo lại), vì cùng model và cùng môi trường với paper nên so được trực tiếp. Nếu không muốn chi tiền thật: làm trên Kaggle sau khi X2′ đạt, và hoãn bước học W7.

**Q10. Thứ tự hạn mức Kaggle tháng 11 khi không đủ cho mọi việc:** khuyên C4′ trước, rồi X3′, rồi W7.

**Q2 (cũ). Mốc đóng băng 01/12:** nếu duyệt X1′ hoặc X2′, cần xác nhận chúng xong trước 01/12, hoặc dời mốc.

## 7. Phản biện bản đối chiếu này (18/11, phiên khác; 0 USD)

Tôi đã đối chiếu từng khẳng định với `docs/reviews/meta_review_2026-11-16.md`, các bản đăng ký và file kết quả. Các mục 1–6 ở trên giữ nguyên theo R5; mục này sửa và bổ sung.

### 7.1 Khẳng định sai hoặc quá mức

1. **"X1 là lỗ lớn nhất, review nhắc hai lần, nên phải đứng trên C4′": quá mức.**
   - P1 chỉ đòi *ghi* giới hạn "Make the one-learning-run-per-condition limitation visible beside the relearning conclusion". Việc này đã xong (D5, `docs/todo_ease_revision.md`).
   - Việc *chạy lại* lượt học nằm ở **P2 — Optional strengthening** ("Repeat learning across seeds and compare training scorers S and L"), **cùng bậc** với agent khác hãng ("Add a different model family…"), tức C4′.
   - Câu "do not present this as necessary merely to expand a case study" nói về cách *trình bày* trong bài, không nói C4′ kém quan trọng hơn X1. Không có căn cứ trong review để xếp X1 trên C4′.
2. **"W7 không có trong review": không đúng.** Review viết "R3's confounding concerns further limit claims about the optimizer's general behavior". W7 (bộ học thứ hai) trả lời đúng câu hỏi về hành vi chung của bộ học. Mối lo "learning randomness" của R3 cũng một phần đã có lời đáp ở §38: model viết skill của gskill lặp lại bước biến rò rỉ thành chỉ dẫn qua 3 seed (0,94 so với 0,29; ghi chú 38-6). Phần chưa lặp là bước chọn ứng viên của GEPA.
3. **Chi phí X1′ "khoảng 22 USD" thiếu khâu chấm (A141).**
   - Học: môi trường gốc 12,25 USD dự kiến (chi phí đo của lượt học gốc, §30 dòng "Học: dự kiến 12,25 USD"); một commit 10,99 USD (§30). Cộng 23,24.
   - Chấm skill mới trên 34 task, như §30: 3,667 USD mỗi môi trường, tức khoảng 7,33.
   - **Tổng dự kiến khoảng 30,6 USD**, chưa cộng biên của trần theo L66. Con số 22 chỉ là phần học.
   - "Đổi seed của GEPA": §30 ghi "không seed cho agent khi học". Chưa kiểm mã gskill có tham số seed cho GEPA hay không. Nếu không có, lượt lặp chỉ là "chạy lại" (ngẫu nhiên tự nhiên), và bản đăng ký phải ghi đúng như vậy.
4. **"Hạn mức Kaggle tháng 11 không đủ": chỉ đúng khi X1′ chạy trên Kaggle.**
   - Đã dùng 25,69 USD (P0 0,47; B 3,05; A 20,06; A′ 1,30; C3 0,01; C4 phiên 1 0,77; C6 0,03); còn khoảng 74,3.
   - C4′ tối đa 36 (trần, không phải dự kiến) cộng bước học W7 tối đa 23 (cận thô) là 59 ≤ 74,3.
   - Vậy Q10 chỉ cần thiết nếu chọn X1′ trên Kaggle.

### 7.2 X2′: nên làm, nhưng sửa ba điểm

1. **Quy tắc đạt tự đặt (vi phạm R2).** "Nằm trong khoảng chênh giữa hai seed Docker" không có nguồn công bố, và không có power.
   - Đã có **ba** seed Docker của Flash-Lite trên các task này, không phải hai: seed 41 (§25), 51 (§33), 61 (C10R nhánh A).
   - Đề xuất thay: báo hiệu chroot − Docker kèm khoảng tin cậy theo cặp task (ước lượng, không phải cổng đạt/không đạt). Nếu cần một cổng, dùng kiểm định tương đương TOST (Schuirmann 1987). Lề tương đương phải có căn cứ, ví dụ độ lệch chuẩn giữa các seed đo được. Phải đưa nguồn TOST vào `configs/sources.json` và đọc trước khi đăng ký.
2. **Không cần chặn C4′.** Kết quả X2′ chỉ đổi cách *diễn giải* C4′, không đổi thiết kế. Hai việc chạy song song được.
   - Đích của C4′ là hiệu hai mức tăng giữa hai môi trường, cả hai đều trong `chroot` (ghi chú 40-5), nên ảnh hưởng hằng của lớp `chroot` triệt tiêu một phần.
   - Lớp `chroot` dùng đúng các lớp của image gốc và hai bước Dockerfile của §25 (`kaggle/preregistration_s40.md`, ghi chú 40-4). Các khác biệt với Docker đã được liệt kê trước.
3. **Phạm vi:** X2′ chỉ kiểm lớp `chroot` với Flash-Lite. Nó chỉ loại được giải thích "do môi trường" cho agent khác hãng khi ảnh hưởng của môi trường không phụ thuộc agent. Bài phải ghi giới hạn này.
- **Chi phí dự kiến thấp:** C10R chi 0,397 (không skill) + 1,378 (có skill) cho 70 task. Với 34 task, khoảng 0,86 USD.

### 7.3 X3′: nên làm, đổi lấy mẫu thành kiểm toàn bộ ở tầng quan trọng

- Con số "0/669 ở môi trường một commit" đúng **theo cách dựng**: kênh không tồn tại. Gán nhãn tầng đó chỉ kiểm dương tính giả.
- Các khẳng định cần kiểm là "mọi task không mô tả giải được ở môi trường gốc đều có diff Bug Patch trong trace" (15/15, 17/17, 20/20). Đây là 52 trace. Kiểm **toàn bộ** 52 trace thì không cần căn cứ cho cỡ mẫu 60 (R2).
- Phần lấy mẫu chỉ còn cho tầng âm tính, để ước lượng âm tính giả.
- Bộ gán nhãn là model khác hãng không phải "nhãn độc lập" theo nghĩa của ghi chú trang 8. Cần ít nhất một người gán.

### 7.4 Thứ tự đề xuất sau phản biện

1. Đã duyệt, chạy tiếp: C4′ và chạy thử W7 (0 USD). X2′ chạy song song nếu được duyệt (khoảng 0,86 USD dự kiến).
2. X3′: kiểm toàn bộ 52 trace (0 USD, cần người gán).
3. X1′: một phán đoán giá trị. Mạnh hơn ở đúng điểm R3 nêu, nhưng khoảng 30,6 USD tiền thật và chỉ đưa n từ 1 lên 2. @thuthuy chọn (CLAUDE.md, quyền quyết định mục 1, 2, 4).
4. Bước học W7 sau C4′, trong hạn mức còn lại (đủ theo 7.1 mục 4).

## 8. Trả lời phản biện ở mục 7 (18/11/2026)

**Chấp nhận:** 7.1 mục 1, 2, 4; toàn bộ 7.2 và 7.3; thứ tự ở 7.4. X1 và C4′ cùng ở P2; W7 trả lời câu của review về "the optimizer's general behavior"; quy tắc đạt của X2′ ở mục 4 là tự đặt; X3′ nên kiểm toàn bộ 52 trace và cần một người gán nhãn.

**Hai điểm sửa thêm, đã kiểm trên dữ liệu và mã gốc:**

1. **Chi phí X1′: 28,10 USD, không phải 30,6.**
   - 30,6 lấy chi phí chấm của §30 (3,667 USD) cho **cả hai** môi trường. Nhưng:
     - chấm skill ở môi trường gốc tốn **1,940 USD** (§25 bước 2, "Kết quả bước chấm skill gskill", 100 task, 0 lỗi hạ tầng);
     - 3,667 của §30 gồm một lượt chạy bù 0,748 USD (lần đầu 2,918); lượt bù là sự cố, không phải khâu của thiết kế.
   - Dự kiến theo chi phí đo của từng khâu, đúng môi trường: học 12,254 (gốc) + 10,990 (một commit) + chấm 1,940 (gốc) + 2,918 (một commit) = **28,10 USD**. Nếu tính cả khả năng phải chạy bù như §30: 28,85 USD.
   - Ghi ở `docs/audit_pilot.md` A142.
2. **Câu hỏi "gskill có seed cho GEPA không" đã có câu trả lời, và nó đổi thiết kế của X1′.**
   - Trong `train_optimize_anything.py` ở commit ghim `8c7b697` (sha256 `ba95bce7…`, đã kiểm ở §38):
     - `parser.add_argument("--seed", type=int, default=42, ...)`;
     - cùng giá trị đó vừa chia dữ liệu (`load_and_split_data(..., seed=args.seed)`, trong đó `random.seed(seed)` trước khi xáo task), vừa đi vào `EngineConfig(..., seed=args.seed, ...)` của GEPA.
   - Cả ba lượt học đã có đều chạy với seed 42 (`config.json` trong `s25_learn_run`, `s25bleve_learn_run`, `s30_learn_run`). Chữ "không seed" ở §30 là nói về **agent** khi học, không phải về GEPA.
   - **Hệ quả:**
     - đổi `--seed` sẽ đổi luôn tập train/val/test, tức 100 task test không còn là 100 task của paper. Mức tăng của skill mới khi đó không so được trực tiếp;
     - muốn đổi riêng hạt giống của GEPA thì phải sửa mã của gskill để tách hai việc. Đó là một sai lệch về độ trung thành (`docs/reviewer_fidelity.md`).
   - **Thiết kế khuyên cho X1′:** chạy lại **đúng lệnh cũ, giữ `--seed 42`**. Cùng tập task, cùng hạt giống của GEPA. Biến thiên giữa hai lượt đến từ agent không có seed và từ việc lấy mẫu của model khi học, tức đúng phần "learning randomness" mà R3 nêu. Phần biến thiên do GEPA chọn minibatch và ứng viên khác đi thì không được đo; bài phải ghi rõ giới hạn này.


## 9. Kiểm lại mục 8 (18/11/2026; 0 USD)

**Đã kiểm, đúng:**
- Chi phí: §25 bước 2 "Cộng dồn bước học: 12,254 USD" và chấm "100/100 task; 0 lỗi hạ tầng; 1,940 USD"; §30 "học 10,990 + chấm 3,667 (lần đầu 2,918; chạy bù 0,748)". Tổng 12,254 + 10,990 + 1,940 + 2,918 = 28,102. Tôi chấp nhận 28,10 USD và A142.
- Mã gskill: tải `train_optimize_anything.py` tại `gepa@8c7b697`, sha256 `ba95bce75bfc656e565726ed43994e8f33dfd7f2803c4770ab1350521ad9f531` (khớp §38). Có đúng `--seed` mặc định 42; `random.seed(seed)` rồi `random.shuffle(all_data)` trong `load_and_split_data`; và `EngineConfig(... seed=args.seed ...)`.
- `config.json` của `results/s30_learn_run.tar.gz` ghi `"seed": 42`.

**Ba điểm bổ sung cho thiết kế X1′ (chạy lại đúng lệnh, seed 42):**
1. **Cùng seed chưa bảo đảm cùng tập task.**
   - `load_and_split_data` gọi `load_dataset("SWE-bench/SWE-smith", split="train")` **không ghim revision**. Nó lấy các dòng đầu khớp repo theo thứ tự của dataset, rồi mới xáo.
   - Nếu dataset trên Hugging Face đổi sau ngày 06/11 hoặc 10/11, tập train/val/test sẽ khác dù seed vẫn là 42.
   - **Bước bắt buộc, 0 USD, trước khi chạy có phí:** dựng lại phép chia với seed 42 và so danh sách mã task train/val/test với lượt cũ. Khác ở bất kỳ mã nào thì dừng và báo @thuthuy.
2. **Câu giới hạn phải chính xác.** Giữ seed 42 là cố định *dòng số ngẫu nhiên* của GEPA, không phải cố định *lựa chọn* của nó. Khi điểm của agent khác đi, các lựa chọn sau đó của GEPA cũng khác.
   - Câu đúng: "biến thiên giữa hai lượt học, với cùng phép chia dữ liệu và cùng hạt giống của GEPA".
   - Không viết: "biến thiên do GEPA không được đo".
3. **Thời điểm khác nhau là một nguồn biến thiên thêm.** Lượt mới chạy sau lượt cũ khoảng hai tuần, trên endpoint preview. Hiệu giữa hai lượt gồm cả khả năng nhà cung cấp đổi model. Phần này không tách được; bài phải ghi rõ.
   - Ngoài ra, lượt học chạy hai nửa (300 + 300 lần gọi metric). Nửa hai phải chạy tiếp từ thư mục của nửa một **mới**, không được từ lượt cũ (L6).

**Không đổi:** chi phí dự kiến 28,10 USD (28,85 nếu tính chạy bù); trần theo L66 sẽ cao hơn và được tính khi đăng ký. X1′ vẫn chờ @thuthuy (Q9, hạn 21/11).

## 10. Kiểm điểm bổ sung 1 của mục 9 (18/11/2026; 0 USD)

**Mã gốc xác nhận:** trong `train_optimize_anything.py` ở commit ghim, `load_and_split_data` gọi `ds = load_dataset("SWE-bench/SWE-smith", split="train")` **không ghim phiên bản**, giữ các dòng đầu tiên có `repo` khớp cho tới khi đủ 350, rồi `random.seed(seed)` và `random.shuffle(all_data)`. Vậy phép chia phụ thuộc cả seed lẫn nội dung và thứ tự hiện tại của dataset. Điểm bổ sung 1 đúng.

**Ba lượt học đã có dùng đúng phép chia của bản xuất trên `data-snapshots`** (`scripts/split_identity.py`, test `tests/test_split_identity.py`; kết quả `results/split_identity_jinja.json`, `results/split_identity_bleve.json`):

| Lượt học | Mã task trong log | Thuộc train | Thuộc val | Thuộc test hoặc không có trong bản xuất |
| --- | --- | --- | --- | --- |
| Jinja gốc (§25 bước 2) | 86 | 36 | 50 | 0 |
| Jinja một commit (§30) | 113 | 63 | 50 | 0 |
| Bleve gốc (§25 bước 4) | 11 | 8 | 3 | 0 |

- Ở cả hai lượt Jinja, đủ 50/50 task val xuất hiện, và không task nào của tập test lọt vào lúc học.
- **Giới hạn:** phép kiểm chỉ thấy các mã task có trong log. Nó xác nhận không có task test hay task lạ nào được dùng, nhưng không chứng minh tập train trùng hoàn toàn (Jinja: 36 và 63 trên 200 task train xuất hiện).

**Cổng cho X1′ (thay "bước bắt buộc" của mục 9 bằng hai lớp cụ thể):**
1. **Trước lượt có phí:** chạy lại bản xuất (`scripts/export_swesmith.py`, cùng `--seed 42`, trên Actions vì máy của phiên không vào được Hugging Face) vào một đường dẫn mới, rồi so **toàn bộ** danh sách mã task và nhãn train/val/test với bản xuất cũ. Lệch dù một mã thì dừng và báo @thuthuy. 0 USD.
2. **Trong lượt có phí:** sau nửa một, chạy `scripts/split_identity.py` trên log của lượt mới. Không đạt thì không chạy nửa hai.

**Điểm bổ sung 2 và 3 của mục 9:** chấp nhận nguyên văn. Câu giới hạn sẽ là "biến thiên giữa hai lượt học, với cùng phép chia dữ liệu và cùng hạt giống của GEPA". Chênh lệch theo thời gian của endpoint preview được ghi là không tách được. Nửa hai chạy tiếp từ thư mục của nửa một mới (L6).

## 11. Kế hoạch chạy X2′ và X1′, từng bước (18/11/2026)

**@thuthuy 18/11:** "Tôi có thể chấp nhận vượt trần dự kiến là 10 usd, hãy tính toán cẩn thận thứ tự chạy từng bước".

**Cách hiểu (ghi lại để @thuthuy sửa nếu sai):** duyệt cả Q8 (X2′) và Q9 (X1′). Trần cộng dồn của hai việc = dự kiến @thuthuy đã thấy + 10 = 0,86 + 28,10 + 10 = **38,96 USD**, tính theo số đã chi thực tế (L8), trên Vertex.

### 11.1 Chi phí dự kiến của từng khâu (số đo, không phải ước đoán)

| # | Khâu | Dữ liệu đo dùng làm dự kiến | Dự kiến (USD) |
| --- | --- | --- | --- |
| 1 | X2′ nhánh không skill, môi trường gốc, 34 task, qua `chroot` | C10R nhánh A không skill: 0,397 cho 70 task, × 34/70 | 0,193 |
| 2 | X2′ nhánh có skill, như trên | C10R nhánh A có skill: 1,378 cho 70 task, × 34/70 | 0,669 |
| 3 | Học, môi trường gốc, nửa 1 | §25 bước 2 nửa 1 | 6,364 |
| 4 | Học, môi trường gốc, nửa 2 | §25 bước 2 nửa 2 | 5,890 |
| 5 | Học, môi trường một commit, nửa 1 | §30 nửa 1 | 5,138 |
| 6 | Học, môi trường một commit, nửa 2 | §30 nửa 2 | 5,852 |
| 7 | Chấm: skill mới (gốc) trên 100 task test, môi trường gốc | `f1_skill_probe`: 1,940 | 1,940 |
| 8 | Chấm: không skill, môi trường gốc, 100 task | `f1_probe`: 1,438 | 1,438 |
| 9 | Chấm: skill mới (một commit) trên 100 task, môi trường một commit | `s25_leakfree_skill`: 1,867 | 1,867 |
| 10 | Chấm: không skill, môi trường một commit, 100 task | `s25_leakfree_none`: 1,461 | 1,461 |
| 11 | Chấm: skill mới (một commit) trên 34 task không mô tả, môi trường gốc | §30 nhánh C: 0,346 | 0,346 |
| | **Tổng** | | **31,16** |

- **Khác dự kiến 28,96 mà @thuthuy đã thấy ở chỗ nào:** thêm khâu 8 và 10 (nhánh không skill **chạy cùng lúc** với nhánh có skill, theo việc D4 của review: tách so sánh cùng ngày khỏi khác ngày), và khâu 11 (như §30 nhánh C). Cộng 2,20 USD, trong phần 10 USD @thuthuy cho phép.
- **Biên còn lại:** 38,96 − 31,16 = 7,80 USD, đủ cho một lần chạy bù cỡ §30 (0,748).

### 11.2 Thứ tự chạy và lý do

| Bước | Việc | Tiền | Thời gian | Cổng để sang bước sau |
| --- | --- | --- | --- | --- |
| **0.1** | Tái xuất phép chia với seed 42 trên Actions, so toàn bộ mã task và nhãn với bản xuất cũ (mục 10) | 0 | vài phút | Trùng 100%. Lệch: dừng cả X1′, báo @thuthuy |
| **0.2** | @thuthuy cho biết trần chi tiêu và credit của project Vertex | 0 | — | Còn chỗ ≥ 38,96 USD dưới trần chi tiêu của project (A124: lần trước chạm trần làm 38 lượt hỏng) |
| **0.3** | Đăng ký §46 (X2′) và §47 (X1′): đại lượng, phép kiểm, trần từng khâu, diễn giải đặt trước; review R-82 | 0 | — | Commit trước mọi lượt có phí (R5) |
| **0.4** | Chạy thử miễn phí (model giả lập) mọi nhánh mới, trên Actions: lớp `chroot` + `f1_probe.py`; học với thẻ mới (không ghi đè lượt cũ, L6); chấm | 0 | 1–2 giờ | Không lỗi hạ tầng; file kết quả ở đường dẫn mới |
| **1** | X2′: khâu 1 rồi 2, cùng một job | 0,86 | khoảng 1 giờ | Không lỗi hạ tầng. Kết quả không chặn X1′ |
| **2** | Học gốc, nửa 1 (khâu 3) | 6,36 | ≤ 5 giờ (`--timeout 18000`) | (a) `split_identity.py` đạt trên log mới; (b) quy tắc dừng sớm của §25: `num_candidates` > 1; (c) chi ≤ trần |
| **3** | Học gốc, nửa 2 (khâu 4), tiếp từ thư mục của bước 2 | 5,89 | ≤ 5 giờ | Đủ 600 metric call |
| **4** | Học một commit, nửa 1 (khâu 5) | 5,14 | ≤ 5 giờ | Như bước 2, cộng: mọi lần viết lại lịch sử thành công, không mã thoát 5 hay 6 (như §30) |
| **5** | Học một commit, nửa 2 (khâu 6) | 5,85 | ≤ 5 giờ | Đủ 600 metric call |
| **6** | Chấm: hai job chạy song song. Job gốc: khâu 8 rồi 7. Job một commit: khâu 10 rồi 9, rồi 11 | 7,05 | vài giờ | 0 lỗi hạ tầng; đủ 100/100 mỗi nhánh |
| **7** | Phân tích theo §47; lưu dữ liệu gốc (`archive_raw.py`, `verify_archive.py`) | 0 | — | — |

**Vì sao thứ tự này:**
- **X2′ trước:** rẻ nhất (0,86), và chạy đúng đường thanh toán trên Vertex. Nếu project chạm trần chi tiêu hay endpoint đổi, ta biết ở đây, không phải giữa một lượt học 6 USD. Kết quả của nó cũng dùng ngay cho C4′ đang chạy trên Kaggle.
- **Học gốc trước học một commit:** lượt học ở môi trường gốc lặp lại khẳng định chính về cơ chế ("bộ học viết chỉ dẫn"). Nếu phải dừng giữa chừng vì tiền hay thời gian, phần quan trọng hơn đã xong.
- **Học tuần tự, không song song:** mỗi lượt học chạy 6 worker. Hai lượt song song nhân đôi tải lên Vertex, trong khi B6 đã ghi 2 lượt sập vì giới hạn tốc độ. Tuần tự cũng cho phép dừng sau mỗi nửa nếu chi phí lệch.
- **Chấm sau khi cả hai lượt học xong, và chạy cùng lúc:** bốn nhánh chạy trong cùng khoảng thời gian, nên so sánh giữa hai môi trường không lẫn thay đổi theo ngày của model (D4).

### 11.3 Trần

- **Kiểm trước mỗi khâu:** trần của khâu = min(trần riêng, 38,96 − số đã chi của X2′ và X1′ đến lúc đó).
- **Trần riêng:**
  - học: 14,50 USD mỗi lượt, như §30;
  - chấm và X2′: tính theo L66 (phân vị 0,999 của chi phí mô phỏng), ghi trong §46 và §47 trước khi chạy.
- **Chạm 38,96 thì dừng và báo @thuthuy.** Không chấm một skill học dở như thể đã học đủ (quy tắc của §30).

### 11.4 Thời gian

- Bốn nửa học, mỗi nửa tối đa 5 giờ, chạy tuần tự: khoảng 1–2 ngày tính cả lúc chờ duyệt cổng.
- Cộng X2′ và chấm: xong trước 01/12 nếu bước 0 xong trước 21/11.

### 11.5 Kết quả bước 0.1 (18/11/2026): đạt

- Run 44280027659 (workflow `split-check.yml`, 0 USD): tải lại dataset `SWE-bench/SWE-smith` từ Hugging Face hôm nay, dựng lại phép chia của gskill với seed 42, so từng task với bản xuất trên `data-snapshots`.
- **Jinja: 350/350 task trùng mã, nhãn train/val/test và vị trí. Bleve: 350/350 trùng.** Không task nào chỉ có ở một bên.
- Vậy chạy lại đúng lệnh cũ với `--seed 42` sẽ cho đúng phép chia của các lượt học trước. Lớp kiểm thứ hai (`split_identity.py` trên log sau nửa một) vẫn chạy như kế hoạch, vì dataset có thể đổi giữa hôm nay và lúc chạy.


## 12. Ngân sách mới: Vertex ≤ 20 USD, Kaggle ≤ 100 USD mỗi tháng (18/11/2026)

**Quyết định của @thuthuy:** "Tôi muốn tổng chi phí thực hiện trên vetext không quá 20 đô. Còn kaggle không quá 100 đô (theo hạn mức tháng)". Mục 11 dự kiến 31,16 USD trên Vertex nên không vừa. Một lượt học tốn 11–12 USD, nên trên Vertex chỉ còn chỗ cho một trong hai lượt học lặp lại. Ba phương án đã đưa ra (A: giữ lượt học ở môi trường gốc; B: A, cộng lượt một commit trên Kaggle; C: chỉ X2′). @thuthuy chọn **B**.

**Vì sao giữ lượt học ở môi trường gốc trên Vertex:** kết luận chính về cơ chế là bộ học viết chỉ dẫn đọc lịch sử khi có rò rỉ (§25, §29). Lặp lại đúng lượt đó, cùng endpoint, là phép kiểm trực tiếp nhất của câu đó (`docs/plan_vs_review.md` mục 2, review P1–P2). Lượt một commit lặp lại câu "không viết khi không có rò rỉ"; chạy nó trên Kaggle thì đổi được endpoint, nên câu trong bài phải ghi khác biệt (§48).

**Kế hoạch trên Vertex** (ghi chú 47-1):

| Khâu | Dự kiến | Trần riêng |
| --- | --- | --- |
| §46 X2′ hai nhánh | 0,862 | 1,863 |
| §47 học `x1ship` hai nửa | 12,254 | 14,500 |
| §47 chấm hai nhánh cùng lúc | 3,378 | 4,837 |
| **Tổng** | **16,494** | chặn cộng dồn 20,00 |

- Thứ tự: §46, học nửa 1, nửa 2, chấm. Trước mỗi khâu: số đã chi thực tế + trần của khâu ≤ 20,00 (`scripts/x1_budget.py`).
- Biên: 20,00 − 16,494 = 3,506 USD. Khâu chấm bị chặn nếu số đã chi trước nó vượt 15,163 USD.
- Chờ: 20/11; và chu kỳ của trần 10 USD của project ("Chưa biết").

**Kế hoạch trên Kaggle:** §48 (bản nháp). Dự kiến 14,66 USD hạn mức nếu giá như Vertex; trần 20,15. Thêm vào C4′ (khoảng 11) và W7 (20–23, chưa duyệt), tổng dự kiến cả tháng khoảng 72 trong 100; tổng các trần vượt 100, nên mọi phiên tự kiểm số đã dùng trong tháng.

**Rủi ro thời gian:** §48 cần mã mới (ô notebook chạy gskill qua lớp `chroot`, lưu và nạp thư mục chạy giữa hai phiên) và bước 0. Nếu xong bước 0 trước 25/11, hai nửa học và ba nhánh chấm cần 3 ngày hạn mức (hạn mức ngày 10 USD), xong trước mốc đóng băng 01/12 đề xuất. Nếu trễ, §48 báo cáo sau mốc hoặc chuyển sang phần giới hạn; @thuthuy quyết khi tới lúc (Q2).

### 12.1 Sửa trần Vertex lên 25 USD (18/11/2026)

@thuthuy 18/11: "sửa trần vertex lên 25 đô cho toàn bộ thí nghiệm liên quan". Mức chặn cộng dồn của X2′ và X1′ trên Vertex đổi từ 20,00 thành 25,00 (`configs/x1.json`, ghi chú 47-2). Kế hoạch, thứ tự và trần riêng không đổi.
- Tổng các trần riêng còn lại (21,20) giờ nằm trong 25,00, nên rủi ro "khâu chấm bị chặn" ở mục 12 không còn: khâu chấm chỉ bị chặn nếu số đã chi trước nó vượt 25,00 − 4,837 = 20,163 USD, lớn hơn tổng trần của các khâu trước nó (1,863 + 14,500 = 16,363).
- Vẫn không đủ để đưa lượt một commit về Vertex: 16,494 + 10,990 + 3,674 = 31,158 > 25. §48 giữ trên Kaggle.
- Biên dự kiến: 25,00 − 16,494 = 8,506 USD, chưa giao cho việc nào. Muốn dùng biên này cho một thí nghiệm khác thì phải hỏi @thuthuy.
