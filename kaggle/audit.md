# Lỗi của hướng Kaggle (ghi tại đây cho tới khi thư mục được đưa lên `main`; khi đó chuyển vào `docs/audit_pilot.md` và `docs/lessons_learned.md`)

| # | Lỗi | Ảnh hưởng | Sửa | Bài học |
| --- | --- | --- | --- | --- |
| K1 | Notebook bản đầu đọc mã ở `scripts/`; sau khi chuyển mã sang `kaggle/scripts/` mà không chạy thử lại, ô 3 báo `No module named 'udocker_shim'` | Mất một lần chạy của @thuthuy; không sai số liệu | Notebook tự tìm thư mục mã | Đổi chỗ file thì chạy lại mọi nơi gọi tới nó |
| K2 | Ô 4 dùng `!python {CODE}/...` trên nhiều dòng; IPython không thay biến | Mất một lần chạy; không sai số liệu | Gọi bằng `subprocess` | Notebook phải được chạy thử trước khi gửi, không chỉ đọc lại mã |
| K3 | Ô 3 làm kernel khởi động lại (giả thuyết: udocker giải nén 4,7 GB vào đĩa hệ thống); ô sau mất biến | Mất một lần chạy; không sai số liệu | udocker ở `/kaggle/working`; mỗi ô tự đủ; việc nặng chạy trong tiến trình riêng, có ghi log | Việc nặng trong notebook chạy ở tiến trình riêng; mỗi ô không phụ thuộc trạng thái của ô trước |
