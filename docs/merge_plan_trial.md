# Kế hoạch nhập nhánh `trial` vào `main` (P20, lập 07/11/2026; chưa thực hiện)

> Chỉ lập kế hoạch. Việc đẩy lên `main` cần @thuthuy cho phép: phiên này chỉ làm trên `trial`.

## Số trùng và cách đánh số lại

`main` (tại `a469803`, 06/11) và `trial` cùng dùng một số mã cho những mục khác nhau:

| Loại | Đã dùng trên `main` | Trên `trial` | Đánh số lại các mục của `trial` |
| --- | --- | --- | --- |
| Lỗi (audit) | A89, A91, A92, A93 (lớn nhất A93) | A89–A104 | A89 → A94, A90 → A95, A91 → A96, A92 → A97, A93 → A98, A94 → A99, A95 → A100, A96 → A101, A97 → A102, A98 → A103, A99 → A104, A100 → A105, A101 → A106, A102 → A107, A103 → A108, A104 → A109 |
| Bài học | L47, L48 (`main` không có L44–L46) | L44, L45, L46, L47t, L48t, L49t | L44–L46 giữ nguyên; L47t → L49, L48t → L50, L49t → L51 |
| Review | R-45, R-46 | R-45 … R-55 | R-45 … R-55 → R-47 … R-57 |

## Cách làm khi được phép
1. Tạo nhánh tạm từ `main`, gộp `trial` vào, rồi giải quyết xung đột ở `docs/audit_pilot.md`, `docs/lessons_learned.md`, `docs/review_log.md`, `docs/preregistration_main.md` và `CLAUDE.md`: giữ cả hai phía.
2. Đánh số lại bằng một script thay theo bảng trên. Thay **cả** các chỗ tham chiếu trong mã, comment, test (ví dụ `A97, A103` trong `.github/workflows/*.yml` và `scripts/preflight.py`) và trong mọi tài liệu.
3. Đối chiếu T4: `main` ghi 0,55, `trial` ghi 0,60. Lấy số tính lại từ file kết quả, ghi lý do chênh.
4. Chạy `python scripts/preflight.py` và CI trên nhánh tạm, rồi mới mở pull request.
