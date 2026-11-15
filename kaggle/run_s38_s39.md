# Chạy §38 (mục A) và §39 (mục B) trên Kaggle

Mỗi ngày làm một lượt, đến khi cả hai ô in `all done`.

## Chuẩn bị (một lần)
1. Tạo dataset **Private** tên `gatekeeper-b39`, tải file `b39_prompts.jsonl.gz` lên.
2. Tạo notebook từ https://www.kaggle.com/benchmarks/tasks/new.
3. Trong notebook: Add Input → dataset `gatekeeper-b39`.
4. Tạo hai ô:
   - ô 1: dán cả file `kaggle/notebooks/b39_run_cell.py`;
   - ô 2: dán cả file `kaggle/notebooks/a38_run_cell.py`.

## Mỗi ngày
1. Ghi lại mức "Daily AI Models" trên trang Quotas.
2. Chạy theo lô để kết quả không mất khi phiên bị ngắt: **Save Version → Save & Run All (Commit)**.
   - Nếu bản lô báo lỗi thiếu `MODEL_PROXY` (môi trường lô không có khóa), dùng cách tương tác: chạy ô 1 rồi ô 2, giữ tab mở. Mỗi khi một ô chạy xong, **tải ngay** các file `*_results_*.jsonl` trong Output.
3. Khi bản lô xong: mở Output của phiên bản đó, tải các file `a38_results_*.jsonl` và `b39_results_*.jsonl`, gửi cho Claude.
4. Ngày hôm sau: Add Input → chọn **output của phiên bản notebook hôm trước** (hoặc một dataset chứa các file kết quả đã tải). Ô chạy tự đọc kết quả cũ, bỏ qua những lần gọi đã có câu trả lời, và cộng dồn tiền đã tiêu.

## Mỗi ô tự dừng khi
- tiền tiêu trong phiên chạm trần ngày: B 2,5 USD, A 7,0 USD (tổng dưới 10 USD/ngày);
- tiền tiêu cộng dồn chạm trần của mục: A 40 USD, B 8 USD;
- một model lỗi 3 lần liên tiếp (model đó bị bỏ qua trong phiên).

Tài khoản không gắn thanh toán. Hết hạn mức thì lệnh gọi bị từ chối, không phát sinh tiền.

Dự kiến:
- B xong trong ngày đầu (khoảng 2 USD);
- A cần khoảng 3 ngày (khoảng 22 USD), mỗi ngày gần một lượt seed, khoảng 1 giờ.
