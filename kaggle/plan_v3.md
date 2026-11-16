# Kế hoạch bản 3 (16/11/2026): sau mục B, trước phiên cuối của mục A

Thay `plan_v2.md` ở phần "việc tiếp theo". **Mục C và D chưa được duyệt**: chờ @thuthuy quyết.

## 1. Đã có gì

| Mục | Trạng thái | Hạn mức đã dùng |
| --- | --- | --- |
| P0, P0b | Xong | 0,47 USD |
| B (§39, auditor khác hãng) | **Xong.** Skill giả bị quy lỗi ở cả 4 auditor khác hãng (10, 4, 1, 1 trên 25); cận dưới quy lỗi sai > 0 ở một auditor (Grok 4.6: 0,109) | 3,05 USD |
| A (§38, model viết skill khác hãng) | Seed 1 và 2 đủ (321 câu trả lời); còn seed 3 (159 lần gọi). **Chưa tính endpoint nào** | 13,73 USD |
| Tổng tháng | | 17,25 trên 100 USD |

## 2. Ngày mai (phiên 3 của A)

- **Về vận hành:** 159 lần gọi, khoảng 7 USD, khoảng 1 giờ. Dòng đầu log phải là `jobs 480, done 321, spent so far 13.73`. Nếu ô dừng ở trần 7 USD trước khi xong thì cần thêm một phiên ngắn.
- **Về kết quả:** tôi chưa xem endpoint của seed 1 và 2 (giữ đúng bản đăng ký), nên không dự đoán bằng dữ liệu. Ba kịch bản đã đăng ký, và việc làm tiếp theo của từng kịch bản:

| Kịch bản của A | Ý nghĩa | Việc với paper |
| --- | --- | --- |
| 1. Nhiều model khác hãng viết chỉ dẫn đọc lịch sử khi quỹ đạo có rò rỉ, gần như không viết khi không có | Cơ chế không riêng một model viết skill | Thêm một đoạn và một bảng; đổi câu "one reflection model" thành kết quả đo |
| 2. Chỉ model mốc (Gemini) viết | Cơ chế phụ thuộc model viết skill | Thu hẹp câu chữ về một model; báo đủ số của các model khác |
| 3. Model viết cả khi không có rò rỉ | Chỉ dẫn là thói quen của model | Viết lại phần giải thích ở §36; phát hiện chính (skill mất tác dụng khi bịt rò rỉ) không đổi |

- **Lưu ý về power:** phép kiểm chính chỉ có 13 lần gọi (6 so với 7). Nó chỉ phát hiện được chênh lệch từ khoảng 0,6 trở lên. Kết quả "không bác bỏ" phải được viết là "không đủ dữ liệu để kết luận", không phải "không có hiệu ứng".

## 3. Điểm yếu còn lại của paper, và cái nào sửa được

| # | Điểm yếu | Sau A và B | Còn sửa được bằng tài nguyên miễn phí? |
| --- | --- | --- | --- |
| 1 | Một model viết skill | Có số đo của 4 hãng (ngày mai) | Đã làm |
| 2 | Auditor một họ model | Đã có 7 auditor của 4 hãng và một model mở | Đã làm |
| 3 | **Một họ model làm agent** | Chưa | **Có thể**, bằng mục C dưới đây (phải qua cổng 0 USD trước) |
| 4 | Mỗi điều kiện một lượt học | Chưa (A chỉ lặp một bước) | Có thể một phần, bằng mục D, chỉ khi C chạy ổn |
| 5 | Tỉ lệ giải nền thấp | Chưa | Có thể cải thiện như tác dụng phụ của C (agent mạnh hơn) |
| 6 | Chỉ task tổng hợp, chưa có repo thật | Chưa | **Không.** Task thật cần image Docker riêng từng task; Kaggle không chạy được (K14) |
| 7 | Một bộ học (gskill) | Chưa | Không trong phạm vi này |

Điểm 6 và 7 không sửa được bằng kế hoạch này. Paper phải giữ chúng ở phần giới hạn.

## 4. Mục C (đề xuất): agent khác hãng, chạy không cần container

**Ý tưởng.** Ở giai đoạn 0, Kaggle hỏng ở bước kéo và giải nén image, không hỏng khi chạy Python. Jinja là repo Python thuần. Vậy có thể dựng môi trường của task **không dùng image**: clone repo của task ở đúng nhánh, cài bằng `pip` vào một môi trường riêng, cho agent chạy lệnh trực tiếp trong notebook Benchmarks (nơi có quyền gọi model). Khóa của Kaggle không rời notebook.

**Câu hỏi của C.** Với agent của hãng khác: skill gskill đã học có làm tăng tỉ lệ giải trong môi trường gốc không, và mức tăng có mất đi trong môi trường một commit không? Đây là đúng hai phép nhận chính của paper, lặp lại với một họ agent khác.

**Các cổng, theo thứ tự (dừng ở cổng nào không đạt):**

| Cổng | Việc | Tiền | Đạt khi |
| --- | --- | --- | --- |
| C0 | Đọc bản gốc: SWE-smith dựng `/testbed` thế nào (nhánh nào, lịch sử git có commit "Bug Patch" không, lệnh cài) | 0 | Tìm được câu trích; không suy từ trí nhớ |
| C1 | Tại máy của phiên làm việc: môi trường không-container cho điểm chấm **trùng** điểm Docker đã ghi (bản vá gốc, "không vá", và các bản vá đã lưu), như K0b đã làm cho udocker | 0 | Trùng 100% trên bộ kiểm, 0 lỗi hạ tầng |
| C2 | Trên Kaggle, không gọi model: dựng môi trường, chấm bản vá gốc và "không vá" của 5 task | 0 | 5/5 và 0/5; phiên không bị ngắt |
| C3 | Thử 3 task với agent thật, để đo token và tiền mỗi task | trần 1 USD | Có số đo; agent chạy hết vòng lặp |
| C4 | Đăng ký trước, rồi chạy chính | theo số đo C3 | — |

**Thiết kế dự kiến của C4 (chốt khi đăng ký):** cùng quy tắc nhận đã đăng ký ở §25 (e-process, θ = 0, α = 0,025, thứ tự của gskill, dừng khi vượt ngưỡng), hai môi trường (gốc, một commit), hai nhánh (không skill, có skill). Model agent chọn bằng quy tắc dựa trên số đo C3.

**Rủi ro nêu trước:**
- Môi trường không-container là một sai lệch so với SWE-smith. Nếu C1 không trùng 100% thì dừng, không sửa cho trùng.
- Agent chạy lệnh trực tiếp trên máy notebook, không có lớp cách ly. Task chỉ là repo Python công khai; mỗi task dùng thư mục và môi trường riêng.
- Phiên Kaggle có thể bị ngắt. Mỗi task ghi kết quả ngay và chạy tiếp được.
- Điều khoản dùng hạn mức AI của Kaggle vẫn chưa đọc được (K0e). @thuthuy cần chép câu điều khoản trước C3.

**Ngân sách:** hạn mức tháng còn khoảng 76 USD sau khi A xong (100 − 17,25 − 7). Mục C chỉ được chốt trần sau C3. Không dùng tiền thật.

## 5. Mục D (tùy chọn, chỉ khi C4 chạy ổn): thêm lượt học

Chạy lại lượt học gskill trên Kaggle với cùng hạ tầng của C, để có lượt học thứ hai cho mỗi điều kiện. Chi phí và thời gian chỉ ước tính được sau C3. Giá trị: trả lời điểm yếu 4. Rủi ro: một lượt học dài nhiều giờ, dễ bị ngắt phiên.

## 6. Thứ tự và quyết định

| Bước | Ai | Việc | Cần @thuthuy quyết? |
| --- | --- | --- | --- |
| 1 | @thuthuy | Chạy phiên 3 của A, gửi file | Không |
| 2 | Claude | Phân tích A theo bản đăng ký; báo kịch bản nào xảy ra | Không |
| 3 | Claude | C0, C1 (0 USD, tại máy của phiên) | **Có: duyệt làm mục C** (thêm một thí nghiệm) |
| 4 | @thuthuy | C2, C3 trên Kaggle | Theo bước 3 |
| 5 | Claude, @thuthuy | Đăng ký và chạy C4 | **Có: chốt trần sau C3** |
| 6 | Claude | Đưa A, B (và C nếu có) vào paper và hai file báo cáo; chuyển `kaggle/` về `main` | **Có: đồng ý cập nhật paper** |

**Vì sao C thuộc quyền @thuthuy:** đây là thêm một thí nghiệm (mục 2 của "Quyền quyết định").
**Ảnh hưởng tới paper:** "một họ model làm agent" là điểm reviewer bắt bẻ mạnh nhất còn lại. Nếu C đạt, hai phép nhận chính có thêm một họ agent độc lập. Nếu C cho kết quả khác, paper phải thu hẹp kết luận về agent Gemini, nhưng có số đo thay cho một điểm chưa kiểm.
**Lời khuyên của tôi:** duyệt C0 và C1 ngay (0 USD, không dùng Kaggle). Hai cổng này cho biết hướng có khả thi không trước khi tốn hạn mức.
