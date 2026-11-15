# §39 (đăng ký trước): auditor khác hãng cho đối chứng sham-skill

**Ngày đăng ký:** 15/11/2026, trước mọi lần gọi model của mục này.
**Duyệt:** @thuthuy 15/11/2026: "Duyệt phương án tốt nhất miễn không charge tiền lố" (mục B của `plan_v2.md`).
**Ngân sách:** chỉ dùng hạn mức AI miễn phí của Kaggle, trần 8 USD. Tài khoản không gắn phương thức thanh toán (ghi chú 38-1).

## 1. Câu hỏi

Ở §19 C, ba auditor Gemini được cho xem một skill giả (cặp A/A, skill không gây ra gì). Kết quả: skill giả bị quy lỗi 25/25, 3/25 và 5/25 lần. Trên lỗi thật, tỉ lệ quy lỗi vượt cận trên mà dữ liệu cho phép. Câu hỏi: auditor của hãng khác, nhận **đúng prompt đó**, có cho kết quả như vậy không?

Paper hiện viết "We tested single auditors with one prompt". Kết quả §39 cho phép nói về nhiều hãng thay vì một họ model.

## 2. Dữ liệu

- **102 prompt:** 52 real, 25 sham, 25 plain, theo đúng thứ tự và đúng các dòng (condition, skill, iid, target, ref) của `results/sham_audit.json`.
- **Dựng lại** bằng `kaggle/scripts/b39_build.py`, gọi `build_prompt` của `scripts/sham_audit.py` (không sửa) trên dữ liệu gốc của E1 (nhánh `raw-archive`, 58 lô).
  - File jobs gốc nằm ở thư mục tạm của một phiên cũ, nay đã mất.
  - Đề bài lấy từ file `dataset/data.jsonl` của chính lô đó. Đây là các dòng mà agent đã chạy; bản gốc lấy từ `e1_rows.jsonl`.
- **Không kiểm được việc trùng byte với prompt gốc** (không còn bản gốc để so). Kiểm gián tiếp: tỉ lệ ký tự trên token Gemini đã ghi nằm trong khoảng 2,35–4,04 (trung vị 3,39). Không có dòng nào lệch hẳn khỏi khoảng đó.
- **File:** sha256 `de507e4bb30caf587d15b37caaafb436d0331e368d81bfcf33878249e76f48d5`, 1.572.192 ký tự.
  - File chứa văn bản quỹ đạo, nên **không commit**, theo cách đã làm ở §19 C.
  - @thuthuy tải file lên Kaggle làm **dataset riêng tư**.

## 3. Model và cách gọi

- **Auditor:** đúng các model khác hãng mà §38 chọn bằng quy tắc của nó sau P0 (Anthropic, OpenAI, xAI, trọng số mở). Không thêm model Gemini, vì §19 C đã có ba model Gemini.
- **Cách gọi như §19 C** (`configs/models/vertex_gemini.json`):
  - một tin nhắn user;
  - `seed=1`;
  - không đặt nhiệt độ;
  - một lần gọi mỗi prompt.
- §19 C đặt `reasoning_effort: low` cho Flash và Pro. Tham số này không áp dụng chung cho các hãng khác nên không đặt. Đây là khác biệt nêu trước.
- **Ô chạy:** `kaggle/notebooks/b39_run_cell.py`, giống hệt ô của §38 ngoài khối cấu hình (có test kiểm). Cùng các quy tắc dừng của ô §38: 8 USD/ngày, trần 8 USD, không gửi lại lần gọi đã có câu trả lời.

## 4. Endpoint và phân tích (`kaggle/scripts/b39_analyse.py`, viết và test trước khi chạy)

- **Đọc quyết định:** bằng `parse` của §19 C. Câu trả lời không đọc được tính là "không quy lỗi", như cách `scripts/make_numbers.py` đếm các con số trong paper. Số câu không đọc được được báo riêng.
- **Mỗi auditor:**
  - **sham:** k/25, khoảng Clopper–Pearson 95%;
  - **plain:** k/25;
  - **real:** tỉ lệ quy lỗi trên 52 cặp, và cận dưới của tỉ lệ quy lỗi sai max(0, tỉ lệ − U). U = 0,4684 là cận trên 95% theo cụm task của §21 (`results/section21.json`). Đây đúng là đại lượng paper đang báo cho ba auditor Gemini.
- **Không có kiểm định giả thuyết mới.** §39 lặp lại cùng các con số mô tả của paper với auditor khác hãng.
- **Diễn giải đặt trước:**
  1. **Câu chữ của paper được giữ nếu** cận dưới trên lỗi thật > 0 ở ít nhất một auditor khác hãng. Khi đó paper viết: "auditors of k vendors", liệt kê từng con số.
  2. **Nếu** cận dưới bằng 0 và sham k = 0 ở mọi auditor khác hãng: hiện tượng chỉ được thấy ở Gemini. Paper phải nói rõ như vậy.
  3. Mọi trường hợp đều báo đủ số của từng auditor.

## 5. Ghi chú thực thi
(chưa có)
