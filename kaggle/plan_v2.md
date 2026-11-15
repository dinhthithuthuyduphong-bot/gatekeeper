# Kế hoạch bản 2 (15/11/2026): dùng hạn mức AI của Kaggle cho việc thuần văn bản

Thay `plan.md` (bản 1) ở phần giai đoạn 1–3. **Chưa được duyệt**: chờ @thuthuy quyết từng mục.

## 1. Tình hình sau giai đoạn 0

| Đã biết | Nguồn |
| --- | --- |
| Hạn mức AI: 10 USD/ngày, 100 USD/tháng; 37 model của Anthropic, OpenAI, xAI, Google | trang Settings; K0c |
| Gọi model chỉ được trong notebook Benchmarks; đặt được `seed`, `temperature`; nhiều lượt qua `respond()` (chưa chạy thử) | K0d |
| Chạy container (udocker) trên Kaggle **không khả thi**: phiên bị khởi động lại hoặc bị hủy ở 9/15 lần chạy | `audit.md` K3–K14 |
| Chi phí mỗi lần gọi: **chưa đo** (ba lần gọi ngắn hiện 0,00 USD) | trang Quotas |
| Điều khoản dùng hạn mức cho nghiên cứu: **chưa đọc** | K0e |

Hệ quả: mọi việc cần agent chạy trong container (model khác hãng làm agent, thêm lượt học đầy đủ, repo thật) **không làm được bằng Kaggle**. Chỉ làm được việc gửi văn bản đã lưu cho model và đọc câu trả lời.

## 2. Điểm yếu nào sửa được

| Điểm yếu của paper | Sửa được bằng kế hoạch này? | Bằng mục |
| --- | --- | --- |
| Một model viết skill (reflection); "bộ học viết chỉ dẫn rò rỉ" mới là một quan sát | **Có, phần lớn** | A |
| Mỗi điều kiện một lượt học; log lần gọi đầu tiên đã mất | **Một phần**: lặp lại bước viết skill nhiều lần, không lặp cả lượt học | A |
| Auditor quy lỗi chỉ thuộc một họ model (phụ lục) | **Có** | B |
| Một họ model cho **agent** | **Không** (cần container) | — |
| Chỉ task tổng hợp; chưa có repo thật | **Không** | — |
| Tỉ lệ giải nền thấp; một bộ học (gskill) | **Không** | — |

## 3. Các mục

### P0. Đo trước khi chạy (trần 0,50 USD hạn mức)
- Gửi **một** prompt thật của mục A (khoảng 30 nghìn token) tới 4 model; ghi số token và chi phí do thư viện báo (`usage`).
- Chạy thử `respond(system=..., input_messages=[...])` một lần: prompt gốc của gskill có system prompt và user prompt riêng hay gộp, và gửi lại đúng như vậy được không.
- @thuthuy chép câu điều khoản về mục đích dùng hạn mức (K0e).
- **Dừng nếu:** điều khoản cấm; hoặc chi phí mỗi lần gọi khiến mục A vượt 60 USD.

### A. Bộ viết skill của hãng khác có biến rò rỉ thành chỉ dẫn không (ưu tiên 1)
- **Câu hỏi:** việc bộ học viết chỉ dẫn "đọc lịch sử git" có phụ thuộc vào model viết skill không?
- **Dữ liệu:** 27 lần gọi model viết skill đã lưu (Jinja gốc 6, Bleve 7, Jinja bịt rò rỉ 14), nguyên văn prompt của gskill.
- **Hai điều kiện, tách bằng dữ liệu đã có:**
  - *có rò rỉ trong quỹ đạo*: các lần gọi mà ít nhất một quỹ đạo agent cho thấy commit "Bug Patch" (Jinja gốc, Bleve);
  - *không có rò rỉ*: 14 lần gọi của lượt học bịt rò rỉ (0/42 quỹ đạo có commit đó).
- **Can thiệp:** ở điều kiện có rò rỉ, skill cha được bỏ dòng lịch sử bằng đúng quy tắc của §29 (`make_ablation.RULE`), để đo việc model **tự viết lại** chỉ dẫn, không phải giữ nguyên dòng có sẵn. Bản không bỏ dòng cũng được chạy để đối chiếu.
- **Model:** 4 model, mỗi hãng một (Anthropic, OpenAI, xAI, và một model trọng số mở); chọn bằng quy tắc cố định sau P0 (model rẻ nhất của mỗi hãng nhận đủ độ dài prompt). Thêm model Gemini gốc của gskill làm mốc.
- **Lặp:** 3 seed mỗi (model, lần gọi), `temperature` như gskill dùng (đọc từ mã gskill đã ghim; nếu không đặt được đúng giá trị thì ghi là sai lệch).
- **Endpoint (đếm bằng máy):** skill trả về có dòng khớp quy tắc lịch sử hay không. Báo tỉ lệ theo model và theo điều kiện, kèm khoảng tin cậy; chênh lệch hai điều kiện kiểm bằng hoán vị theo lần gọi.
- **Diễn giải đặt trước:**
  - tỉ lệ cao khi có rò rỉ và gần 0 khi không, ở nhiều hãng → hiện tượng không riêng của một model viết skill;
  - chỉ model gốc viết → paper phải thu hẹp câu chữ về một model;
  - viết cả khi không có rò rỉ → chỉ dẫn là thói quen của model, không phải do rò rỉ; paper phải nói lại.
- **Giới hạn nêu trước:** đây là lặp lại **một bước** (viết skill từ quỹ đạo đã có), không phải một lượt học; quỹ đạo do agent Gemini tạo; không đo skill mới có làm tăng điểm không.
- **Ước tính:** 5 model × 27 lần gọi × 3 seed, cộng bản đối chiếu ≈ 500–600 lần gọi. Chi phí chỉ tính được sau P0; trần đề xuất 40 USD hạn mức, chia nhiều ngày.

### B. Auditor khác hãng cho đối chứng sham-skill (ưu tiên 2)
- Gửi nguyên văn 102 prompt của `sham_audit.json` cho 3 model khác hãng; đếm số lần skill giả bị quy lỗi (hiện: 25/25, 3/25, 5/25 với ba model Gemini).
- Prompt ngắn (khoảng 4,6 nghìn token); ước tính dưới 2 USD mỗi model; trần 8 USD.
- Sửa câu "single auditors … one model family" ở phụ lục.

### C. Tùy chọn, chỉ khi A và B xong và còn hạn mức
- Cho model đọc quỹ đạo đã lưu và hỏi agent có dùng commit chèn lỗi không; so với bộ theo dõi bằng quy tắc (34/34; 0/398). Giá trị thấp hơn A và B.

## 4. Không vượt hạn mức, không phát sinh tiền

- Hạn mức AI của Kaggle là mức miễn phí; theo hiểu biết của tôi (chưa đọc được trang chính thức), hết hạn mức thì lệnh gọi bị từ chối chứ không tính tiền. **@thuthuy xác nhận tài khoản Kaggle không gắn phương thức thanh toán.**
- Mỗi notebook có bộ đếm chi phí theo số thư viện báo: tự dừng ở **8 USD/ngày** (80% hạn mức ngày) và ở trần của từng mục.
- Tổng trần của kế hoạch: P0 0,50 + A 40 + B 8 = **48,50 USD hạn mức** trong tháng (dưới 100 USD).
- Kết quả từng lần gọi được ghi ra file ngay; chạy lại thì bỏ qua lần đã có (không gọi trùng).
- Không dùng Vertex/GCP; không mang khóa của Kaggle ra ngoài notebook.

## 5. Thứ tự và phần việc của @thuthuy

| Bước | Ai | Việc |
| --- | --- | --- |
| 1 | @thuthuy | Quyết: làm A, B hay không; chép câu điều khoản; xác nhận không có phương thức thanh toán |
| 2 | Claude | Đăng ký trước §38 (A) và §39 (B); viết notebook; chạy thử bằng model giả lập tại máy |
| 3 | @thuthuy | Chạy ô P0 trong notebook Benchmarks (vài phút) |
| 4 | Claude | Chốt model và số seed theo số đo P0; ghi vào bản đăng ký |
| 5 | @thuthuy | Chạy notebook A (mỗi ngày một lượt, tự dừng ở 8 USD), rồi B; gửi file kết quả |
| 6 | Claude | Phân tích theo bản đăng ký; cập nhật paper nếu @thuthuy đồng ý |

**Rủi ro:** notebook Benchmarks cũng có thể bị ngắt như notebook thường; mỗi lần gọi chỉ vài chục giây và được ghi ngay, nên bị ngắt thì chạy tiếp từ chỗ dừng.
