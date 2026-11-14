# Giai đoạn 0 trên Kaggle: hướng dẫn chạy (`kaggle/preregistration_s37.md`)

Mục đích: kiểm xem notebook Kaggle chấm được task SWE-smith với **cùng điểm** như Docker hay không, và đo hạn mức gọi model. Không tốn tiền.

## Chuẩn bị (một lần)
1. Tài khoản Kaggle đã xác minh số điện thoại (cần để bật Internet trong notebook).
2. Tải file `kaggle/notebooks/kaggle_stage0.ipynb` của repo này về máy.
3. Trên Kaggle: **Create → New Notebook → File → Import Notebook**, chọn file vừa tải.
4. Ở khung Settings bên phải: **Internet = On**, **Accelerator = None**.

## Chạy
**Phần A: K0a, K0b (notebook thường).**
- Dùng file `kaggle/notebooks/kaggle_stage0.ipynb` bản mới nhất của nhánh mặc định (bản cũ đọc mã ở `scripts/`, sẽ báo `No module named 'udocker_shim'`).
- Chạy lần lượt ô 1 đến ô 4. Ô 4 mất khoảng 30–60 phút. Nếu phiên bị ngắt, chạy lại ô 1, 2 rồi ô 4: nó chạy tiếp từ chỗ dừng.

**Phần B: K0c, K0d (notebook Benchmarks).**
- Thư viện `kaggle_benchmarks` không có trong notebook thường (lần chạy 14/11 báo `No module named 'kaggle_benchmarks'`, và không có biến môi trường `MODEL_PROXY_*`).
- Mở https://www.kaggle.com/benchmarks/tasks/new: Kaggle tạo một notebook có sẵn thư viện ("This will automatically create a new Kaggle notebook with `kaggle-benchmarks` and its dependencies pre-installed", quick start của kaggle-benchmarks).
- Dán toàn bộ file `kaggle/notebooks/k0cd_benchmarks_cell.py` vào một ô và chạy. Ô này gọi model ba lần, tốn vài xu hạn mức.

## Gửi lại
- `k0a.json`, `k0b_kaggle.jsonl` (phần A) và `k0cd.json` (phần B), đều trong `/kaggle/working/`.
- Ba ghi chú bằng tay: hạn mức AI theo ngày và tháng ở trang Settings; hạn mức bị trừ sau ô 5; câu điều khoản nói hạn mức được dùng cho việc gì.

## Điều kiện đạt (đã đăng ký trước)
- K0b: 100% bản vá trùng điểm đã ghi; bản vá gốc 20/20; "không vá" 0/20; không lượt nào lỗi.
- Chỉ một bản vá lệch là không đạt, và hướng Kaggle dừng cho tới khi tìm ra nguyên nhân.

## Lưu ý
- Notebook không in khóa hay thông tin tài khoản.
- Notebook chỉ đọc repo công khai; không ghi gì lên GitHub.
