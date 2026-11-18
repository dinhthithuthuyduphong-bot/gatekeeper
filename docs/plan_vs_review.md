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
