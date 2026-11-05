# Danh sách việc theo hướng mạnh nhất (bản chờ @thuthuy duyệt, 05/11/2026)

**Nguyên tắc:**
- Mỗi việc ghi rõ: vá điểm yếu nào mà reviewer sẽ chấm; chi phí; xác suất thành công (bằng số nếu có mô phỏng, nếu không thì ghi "chưa đo"); điều kiện để làm tiếp hoặc dừng.
- Việc tốn tiền chỉ làm sau khi bước miễn phí trước nó đã cho số đo.

## Giai đoạn 1: miễn phí, làm ngay

| # | Việc | Vá điểm yếu | Xác suất / ghi chú |
| --- | --- | --- | --- |
| 1.1 | **Đường cong nhận nhầm theo độ phủ** trên nhiễu thật: cho ngưỡng của mọi quy tắc thay đổi; so tại **cùng độ phủ**, đúng endpoint RQ1 gốc (`analysis.harm_at_coverage`). Đăng ký trước | Phản biện "Gatekeeper an toàn chỉ vì thận trọng"; nối lại với câu hỏi gốc | Cao (miễn phí). Có thể B-X2 **ngang** Gatekeeper ở một lần nhìn; vẫn báo cáo |
| 1.2 | **Mệnh đề và chứng minh** cho thu hồi hai bước (xác suất thu hồi nhầm ≤ Σα_k = α) và cho skill ghép (Định lý 4′), trong `docs/theory/proofs.md` | Tính mới và tính đúng của phương pháp | Cao |
| 1.3 | **Đóng T4** (đang chạy): so với dự đoán D-M6; CI; token | Kiểm chứng trên agent thật | Hiện đang tốt: 13 trial, mức tăng 0,54, e-value 11,4 |
| 1.4 | Vì sao agent thất bại **cả khi có bản vá đúng** (5/11 task ở T4) | Giải thích giới hạn của agent và vì sao chứng nhận khó | Cao |

## Giai đoạn 2: tốn tiền, mỗi bước có cổng dừng (@thuthuy duyệt từng bước)

| # | Việc | Vá điểm yếu | Chi phí | Cổng dừng / làm tiếp |
| --- | --- | --- | --- | --- |
| 2.1 | **Pilot skill thật "cách chạy test của repo"**, khoảng 20 task, chạy mới cả hai nhánh | **Ý nghĩa thực tế** (điểm yếu lớn nhất) | khoảng 2,5 USD | **DỪNG sau 4 task** (D-M7, A79): cận trên δ ≈ 0,09 tính từ dữ liệu mục 1.4 thấp hơn cổng 0,15; chi 0,97 USD |
| 2.2 | **Chứng nhận skill đó** trên task mới, đăng ký trước | Ý nghĩa thực tế | — | **Hủy** (2.1 dừng) |
| 2.3 | **Đo chi phí của model thứ hai** trên 5 task | **Tính tổng quát** | khoảng 1 USD (ước, chưa đo) | Cần khóa/tài khoản (quyền @thuthuy, L21: hỏi tình trạng trước) |
| 2.4 | **Lặp lại phần cốt lõi trên model thứ hai:** nhiễu A/A trên khoảng 100 task; T4; phép kiểm kiểu E2 | Tính tổng quát | Tính từ 2.3 | @thuthuy duyệt sau 2.3 |
| 2.5 | (tùy chọn) Ô MemGovern bản gốc | Thêm một hệ thống đã công bố | khoảng 20 USD (đã duyệt) | Chỉ nếu 2.1–2.4 xong mà còn ngân sách |

## Giai đoạn 3: miễn phí, viết và nộp

| # | Việc |
| --- | --- |
| 3.1 | Viết lại paper theo định vị mới (`docs/paper_argument.md`, `docs/novelty_review.md`): Qu et al. là công trình gần nhất; threats to validity; mọi số đều là số đo |
| 3.2 | Sửa `refs.bib` và kiểm từng trích dẫn; bảng và hình sinh tự động; cập nhật `number_provenance.md` và `glossary.md` |
| 3.3 | 👤 Một người biết thống kê đọc phần chứng minh |
| 3.4 | Artifact, ẩn danh; 👤 thu hồi khóa `0cf3193a` |

## Mức cạnh tranh dự đoán (định tính; không có số liệu để tính xác suất)

| Làm tới đâu | Mức |
| --- | --- |
| Giai đoạn 1 + 3 | Ranh giới cho track chính |
| + 2.1–2.2 thành công (một skill thật được chứng nhận) | Cạnh tranh được |
| + 2.3–2.4 (hai model) | Cạnh tranh tốt |
