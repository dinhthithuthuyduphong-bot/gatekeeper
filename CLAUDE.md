# Hướng dẫn làm việc trong repo Gatekeeper (đọc trước mọi việc)

Repo nghiên cứu Gatekeeper (ASE 2027). Người phụ trách: @thuthuy. File này được nạp tự động ở mỗi phiên làm việc. Nó tóm tắt các quy tắc **bắt buộc**; chi tiết nằm trong các file được dẫn.

## Ngôn ngữ và báo cáo
- Trả lời và viết tài liệu bằng **tiếng Việt**. Mã và comment trong mã bằng tiếng Anh.
- Báo cáo chi phí bằng **token** (input, cache, output). USD chỉ dùng để kiểm soát ngân sách trong trao đổi.
- Không ghi mã định danh model trong commit hay tài liệu.

## Quy tắc nghiên cứu R1–R5 (`docs/research_rules.md`)
1. **R1:** mọi đề xuất phải nêu: tại sao; dựa trên lý thuyết, công thức hay thực nghiệm **đã công bố** nào; câu trích từ **bản gốc đã đọc** (nhánh `sources-snapshots`, cấu hình ở `configs/sources.json`). Không suy đoán từ trí nhớ. Không tự đoán URL.
2. **R2:** mọi con số và khái niệm phải thuộc một nhóm có điều kiện kiểm được: chuẩn công bố, suy ra, bên thứ ba, định nghĩa can thiệp, vận hành. Ghi vào `docs/number_provenance.md`. Số tự đặt thì thay thế, tìm nguồn, hoặc hỏi @thuthuy.
3. **R3:** mọi mã hay quy tắc mới phải **review trước khi chạy** theo danh sách `docs/research_rules.md` §4, chạy `python scripts/preflight.py`, và ghi vào `docs/review_log.md`.
4. **R4:** mọi lỗi được ghi vào `docs/audit_pilot.md` (lỗi, ảnh hưởng, sửa, bằng chứng) **và** `docs/lessons_learned.md` (nguyên nhân gốc, phòng ngừa). Mỗi bài học thành một mục kiểm tra trong §4.
5. **R5:** không đổi quy tắc sau khi thấy dữ liệu. Mọi thay đổi trước khi phân tích là một "Ghi chú thực thi" hoặc một "Sai lệch D#" có ngày và lý do, ghi trong bản đăng ký trước. Quy tắc cũ vẫn được tính và báo cáo.

## Quy trình cho mỗi tác vụ (theo thứ tự)
1. Đọc bản đăng ký trước liên quan (`docs/preregistration_*.md`), kể cả mọi ghi chú thực thi và sai lệch.
2. Tìm nguồn → thêm vào `configs/sources.json` → workflow `sources` → kiểm đoạn trích **chứa đúng câu cần dùng**.
3. Viết mã. Hàm nhận con số khoa học (α, θ, cách chia α) **không có giá trị mặc định**.
4. Mô phỏng **đúng quy tắc quyết định cuối cùng** trên đúng thiết kế, cả tỉ lệ sai lẫn power (`scripts/verify_methods.py`, L11).
5. Test cho từng chỗ sửa. Chạy `python scripts/preflight.py` (lint, test, nguồn, mặc định, khóa bí mật).
6. Chạy thử miễn phí (mô hình giả lập) trên ít nhất 1 task thật của bộ dữ liệu mới.
7. Ghi `docs/review_log.md`. Chỉ sau đó mới chạy có chi phí.
8. Sau khi chạy: kiểm `infra_failures`, `endpoint_mismatch`, `patch_apply_failed` trong file kết quả. Commit và push.

## Không bao giờ
- Commit khóa service account. Khóa chỉ nằm ở scratchpad `secret/gcp-key.json`. Trước mỗi commit kiểm `git diff --cached | grep "BEGIN PRIVATE KEY"`.
- Phân phối lại nội dung không có LICENSE (rule của XRepoSkill: chỉ commit mã rule).
- Coi "không có kết quả" là "kết quả xấu" hoặc ngược lại mà chưa đọc log của công cụ (L1).
- Chạy lại một lỗi do agent gây ra (thành thử lại đến khi thành công, L1).
- Ghi đè kết quả của thí nghiệm khác (L6). Thay đổi thiết kế giữa chừng phải chạy thành giai đoạn riêng (L12).
- Vượt ngân sách @thuthuy đã duyệt. Trần tính từ số đã chi thực tế (L8).

## File tham chiếu
| Việc | File |
| --- | --- |
| Kim chỉ nam, nhật ký tiến độ | `TODO.md` |
| Quy tắc, danh sách review §4, mục đang vi phạm §5 | `docs/research_rules.md` |
| Sổ review trước khi chạy | `docs/review_log.md` |
| Lỗi đã gặp (A#, B#, C#) | `docs/audit_pilot.md` |
| Bài học L1–L13 | `docs/lessons_learned.md` |
| Nguồn gốc mọi con số | `docs/number_provenance.md` |
| Ký hiệu và thuật ngữ (một nghĩa duy nhất) | `docs/glossary.md` §7 |
| Kiểm định phương pháp bằng số | `docs/method_check.md`, `scripts/verify_methods.py` |
| Bản đăng ký trước | `docs/preregistration_g1_v2.md`, `_e1.md`, `_e2.md` |
| Kiểm tra tự động trước khi chạy | `scripts/preflight.py` (chạy cả trong CI) |
