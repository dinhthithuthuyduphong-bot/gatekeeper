# Tải gói tái lập lên figshare cho vòng review ẩn danh (E-A4, R-99)

Đây là việc ra bên ngoài, làm bằng tài khoản figshare của @thuthuy. Tôi không có tài khoản và không tự làm việc này.

**Vì sao chọn figshare.** Hướng dẫn mà chính sách Open Science của SIGSOFT dẫn tới (`disclose_data_dbr_howto`) cho thấy hai cách khác nhau:
- **figshare** cho phép tạo link riêng tư không lộ tác giả trong lúc review, và công bố chính thức khi bài được nhận.
- **Zenodo** chỉ ẩn danh được nếu công bố công khai ngay: "However, the file will be publicly accessible and indexed in Zenodo."

Bản công bố không xóa được, và lời khuyên Q6 là chỉ đưa ra khi đã xem bản cuối. Vì vậy figshare là phương án trội.

Hướng dẫn gốc viết năm 2018, nên giao diện figshare có thể đã khác. Nếu khác, giữ đúng hai điều cốt lõi là **link riêng tư** và **chưa Publish**.

## Các bước
1. **Lấy file.** Dùng file `replication_package.zip` tôi gửi, dựng bằng `scripts/build_replication_package.py`. Gói đã được quét danh tính (0 chỗ lộ) và có `LICENSE` (MIT) cùng `LICENSE-DATA.md` (CC-BY 4.0).
2. **Tạo item.** Trên figshare, tạo một item mới (loại Dataset) và tải file zip lên.
3. **Điền thông tin không lộ danh tính.** Hướng dẫn gốc: "Make sure that title and description are blinded. These fields _will_ become visible instead." Đề xuất:
   - Title: `Replication package: A Published Skill Learner Found the Leak (anonymized for review)`
   - Description: `Code, data, traces and registrations of the paper, anonymized for double-anonymous review. See README.md.`
   - Phần tác giả có thể điền thật. Hướng dẫn gốc: "You can provide unblinded author details here already. _Author details be blinded once the item is published for double-blind review_."
   - License: CC BY 4.0. Phần mã trong gói theo `LICENSE` (MIT).
4. **Tạo link riêng tư, không Publish.** Hướng dẫn gốc: "Be sure to `Generate a private link` and **do not flag the `Publish` option**." Không cần bật Apply embargo, Make file(s) confidential hay Reserve DOI ("There is no need to flag the options `Apply embargo`, `Make file(s) confidential`, and `Reserv`…", đoạn trích bị cắt ở đây).
5. **Kiểm link.** Mở link riêng tư trong một cửa sổ ẩn danh của trình duyệt, chưa đăng nhập. Phải tải được file, và trang không được hiện tên hay tài khoản của @thuthuy.
6. **Gửi link cho tôi.** Tôi thay macro `\anonpackage` trong `paper/main.tex` bằng link, rồi chạy `python scripts/ease_pdf_check.py paper/main.pdf`. Lệnh này phải báo PASS, tức không còn chữ ANON-LINK-PENDING.
7. **Khi bài được nhận:** bấm Publish trên chính item đó để có DOI, rồi đổi câu trong Data Availability của bản camera-ready thành DOI và tên tác giả thật.
