# Rà soát pilot từ ngày 01/11 tới 05/11/2026: vì sao kẹt lâu và tốn kém

Nguồn: nhật ký tiến độ trong `TODO.md` (dòng 672 trở đi), `docs/audit_pilot.md`.

| # | Nguyên nhân | Bằng chứng | Thiệt hại |
| --- | --- | --- | --- |
| 1 | Pilot hỏi "skill có tác dụng không" bằng thiết kế xác nhận lớn, thay vì kiểm phương pháp (cổng có hoạt động không) | G1, E1, E2 đều FAIL | khoảng 153 USD, khoảng 4 ngày |
| 2 | Bỏ qua tín hiệu từ ngày đầu: R15 (SD hiệu ứng thật khoảng 0,03), R14 (power khoảng 5%), R16 (bộ chọn task kích hoạt yếu) | Nhật ký ngày 01/11 | Lẽ ra phải đổi thiết kế từ 01/11 |
| 3 | Leo thang sau mỗi lần thất bại | Ngân sách E1: 65 → 75 → 91 USD; thêm E2 45 USD | khoảng 70 USD |
| 4 | Không xây tiếp trên đối chứng dương đã đạt ở G1 (`control-oracle-tests`: Z = −0,125, CI [−0,22; −0,03], ngày 02/11) | Nhật ký ngày 02/11 | Mất phép kiểm phương pháp rẻ nhất |
| 5 | Chi phí mỗi lần chạy tăng khoảng 3 lần do trần bước 60 → 100 → 250 | 0,022 → 0,063–0,07 USD/lần chạy; khoảng 1,26 triệu token vào mỗi lần chạy | khoảng 3 lần chi phí mỗi trial |
| 6 | Hạ tầng: đĩa, phiên 2 giờ, lỗi 429, container khởi động lại | Nhiều mục A# | Thời gian |
| 7 | Lỗi của tôi (A21–A77) | `docs/audit_pilot.md` | Thời gian, niềm tin |

**Khả năng chi trả của thiết kế gốc** (0,126 USD mỗi trial):
- δ = 0,109: 216–470 trial mỗi ô, tức 27–59 USD mỗi ô; khoảng 20 ô thì 540–1.180 USD.
- δ khoảng 0,03 (mức thực tế): không đạt trong 4.000 trial.
- Kết luận: chứng nhận hàng loạt ô thật không kham nổi với hiệu ứng thực tế.
