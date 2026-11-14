## R-66. §37 giai đoạn 0 của hướng Kaggle (0 USD)

- **Đối chiếu bản đăng ký:** §37 được commit (`17c6634`) trước lượt so khớp đầy đủ; 4 bản vá chạy thử trước đó được ghi ở mục "đã thấy trước".
- **Mã:** `kaggle/scripts/udocker_shim.py` (thay `docker.from_env` và lệnh kéo image; mã chấm của SWE-smith giữ nguyên), `kaggle/scripts/k0_stage0.py`, `kaggle/tests/test_udocker_shim.py` (bản sao `/testbed` riêng cho từng container, image gốc không bị sửa, lệnh được tách như `docker exec`).
- **Kiểm ở máy này:** 117/117 bản vá trùng điểm; bản vá gốc 20/20; "không vá" 0/20; 0 lỗi hạ tầng.
- **Chưa kiểm được:** notebook chưa chạy trên Kaggle. Ô 5 (thư viện `kaggle_benchmarks`) viết theo tài liệu, chưa chạy thử.
- **Sự cố khi làm:** hết đĩa một lần do giải nén image hai lần (hai tên image cho cùng nội dung); đã xoá bản thừa, không mất dữ liệu của repo.
