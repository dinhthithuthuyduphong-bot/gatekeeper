# Hướng dẫn làm việc trong repo Gatekeeper (đọc trước mọi việc)

Repo nghiên cứu Gatekeeper (ASE 2027). Người phụ trách: @thuthuy. File này được nạp tự động ở mỗi phiên làm việc. Nó tóm tắt các quy tắc **bắt buộc**; chi tiết nằm trong các file được dẫn.

## Ngôn ngữ và báo cáo
- Trả lời và viết tài liệu bằng **tiếng Việt**. Mã và comment trong mã bằng tiếng Anh.
- Báo cáo chi phí bằng **token** (input, cache, output). USD chỉ dùng để kiểm soát ngân sách trong trao đổi.
- Không ghi mã định danh model trong commit hay tài liệu.

## Yêu cầu của @thuthuy (nguyên văn; mọi quy tắc bên dưới được rút ra từ đây, nếu khác thì nguyên văn thắng)

- "Tôi không chấp nhận những con số chọn mà không có lý do chính đáng. Phải chứng minh được con số đó tại sao xuất hiện: hoặc là đã số đó đã được chứng minh từ lý thuyết có sẵn, hoặc là nó là con số nhạy cảm phải đổi liên tục và thử đi thử lại nhiều lần mới chọn được (tuy nhiệ trường hợp này cũng phải giải thích lý do tại sao phải thử, áp dụng quy tắc có thật nào để chọn giữa nhiều kết quả)"
- "Mở bản gốc đọc và xác nhận kỹ lần nữa. Vì đây là giai đoạn quan trọng nên tôi không muốn có bất cứ 1 sự mơ hồ nào từ cơ sở lý thuyết, phương pháp, công thức, con số"
- "Những điều không thể chứng minh hoặc do bạn tự đặt ra phải được củng cố và thay thế bởi 1 lý thuyết, công thức có thật được công bố"
- "Tất cả các update fix bug đều phải được note lại kĩ lưỡng để tránh tái phạm. Bất kể bạn đề xuất cho tôi hướng đi nào đều phải tuân thủ theo quy tắc: tại sao lại đề xuất như vậy? Dựa trên lý thuyết hay công thức hoặc thực nghiệm nào đã công bố (đọc từ tài liệu thật và không suy đoán dựa trên hiểu biết)? Sau khi chọn phương án, bạn code xong hay viết mã hay rule đều phải được review kĩ càng trước khi thực thi để tránh tình trạng nhận kết quả sai do hành vi bản thân. Từ đây tất cả các khái niệm, con số đều được phải chứng minh và giải thích dựa trên nguồn tài liệu công bố thật trước khi đem vô quy trình nghiên cứu. Bất cứ 1 khái niệm hay con số tự đặt không có sự chứng minh hay cho phép đều phải cân nhắc hướng thay thế hoặc tìm tài liệu trích dẫn thêm"
- "Tôi không chấp nhận những ngưỡng mơ hồ và tối nghĩa, mọi thứ phải thực sự rõ ràng để không bị reviewer bắt bẻ"
- "Fix tất cả bug làm cho research yếu đi và làm số liệu sai. Nhớ note"
- "Confirm ngân sách. Tuy nhiên hãy nhớ các khâu review trước khi chạy"
- "Đảm bảo những kinh nghiệm và quy trình bạn được train đều sẽ được áp dụng từ đây về sau"
- "Làm điều tốt nhất cho paper, nó phải là 1 research đủ mạnh"
- "Usd dùng để kiểm soát budget trong đoạn chat, khi report thì đổi qua thành token để so sánh"
- "đổi qua xuất tiếng việt trên màn hình"
- Ngân sách: chạy không cần hỏi trong mức đã duyệt; **chạm mức đã duyệt thì dừng, chờ @thuthuy quyết** ("nếu khi tổng chi phí lên 30 đô thì chờ tôi quyết định"). Mức hiện tại: E1 91 USD (trần cộng dồn 122,26), E2 45 USD.
- Phán quyết phải "trong sáng, không khiên cưỡng".

## Cơ chế bảo đảm áp dụng (không phụ thuộc vào trí nhớ)
1. File này được nạp tự động khi mở một phiên mới trong repo. Hook `.claude/hooks/session-start.sh` chạy ở mọi lần bắt đầu, tiếp tục, xóa và tóm tắt phiên. Hook cài git hook `pre-commit` (preflight không đạt thì **git từ chối commit**), in lại quy tắc và các mục mới nhất, báo Docker và các thí nghiệm dở dang, rồi chạy preflight. **Đọc kết quả của hook trước khi làm bất cứ việc gì.**
2. Mọi script chạy có chi phí (`run_e1_par.sh`, `run_e2.sh`, và mọi script mới) **bắt đầu bằng cổng** `python scripts/preflight.py --ci || exit 7`: kiểm tra thất bại thì không chạy.
3. Mọi commit đi qua git hook `pre-commit` (cài bởi hook khởi động phiên): preflight không đạt thì git từ chối commit. Không dùng `--no-verify`.
4. CI chạy preflight ở mọi lần push.
5. Mỗi lỗi mới có thể kiểm bằng máy phải được thêm vào preflight. Lỗi chỉ kiểm được bằng người thì thêm vào danh sách §4 và ghi vào `docs/review_log.md` khi review.

## Quy tắc nghiên cứu R1–R6 (`docs/research_rules.md`)
1. **R1:** mọi đề xuất phải nêu: tại sao; dựa trên lý thuyết, công thức hay thực nghiệm **đã công bố** nào; câu trích từ **bản gốc đã đọc** (nhánh `sources-snapshots`, cấu hình ở `configs/sources.json`). Không suy đoán từ trí nhớ. Không tự đoán URL.
2. **R2:** mọi con số và khái niệm phải thuộc một nhóm có điều kiện kiểm được: chuẩn công bố, suy ra, bên thứ ba, định nghĩa can thiệp, vận hành. Ghi vào `docs/number_provenance.md`. Số tự đặt thì thay thế, tìm nguồn, hoặc hỏi @thuthuy. Số phải thử nhiều lần mới chọn được: nêu vì sao phải thử, và chọn bằng một quy tắc đã công bố, trên dữ liệu không dùng để kết luận. Không ngưỡng hay từ ngữ mơ hồ: mỗi ký hiệu một nghĩa (`docs/glossary.md` §7), mọi đánh giá kèm con số.
3. **R3:** mọi mã hay quy tắc mới phải **review trước khi chạy** theo danh sách `docs/research_rules.md` §4, chạy `python scripts/preflight.py`, và ghi vào `docs/review_log.md`.
4. **R4:** mọi lỗi được ghi vào `docs/audit_pilot.md` (lỗi, ảnh hưởng, sửa, bằng chứng) **và** `docs/lessons_learned.md` (nguyên nhân gốc, phòng ngừa). Mỗi bài học thành một mục kiểm tra trong §4.
5. **R5:** không đổi quy tắc sau khi thấy dữ liệu. Mọi thay đổi trước khi phân tích là một "Ghi chú thực thi" hoặc một "Sai lệch D#" có ngày và lý do, ghi trong bản đăng ký trước. Quy tắc cũ vẫn được tính và báo cáo.

6. **R6:** thuật ngữ, ký hiệu và ngưỡng phải rõ nghĩa. Mỗi ký hiệu được định nghĩa trước khi dùng và chỉ có một nghĩa (`docs/glossary.md` §7). Mỗi ngưỡng ghi đủ giá trị, chiều (một phía hay hai phía), đại lượng áp dụng và nguồn. Không dùng từ đánh giá mơ hồ khi không kèm con số. Preflight [terms] kiểm tự động.

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
- Commit khóa service account. Khóa chỉ nằm ở scratchpad `secret/gcp-key.json`. Trước mỗi commit chạy `python scripts/preflight.py --ci`: kiểm tra [secrets] **chặn** commit nếu có khóa thật (dấu hiệu PEM có gạch ngang, hoặc trường `private_key` của file khóa). Một lệnh chỉ đếm số dòng khớp (`grep -c`) không chặn được gì (A47).
- Phân phối lại nội dung không có LICENSE (rule của XRepoSkill: chỉ commit mã rule).
- Gợi ý @thuthuy cài đặt, tạo khóa hay cấu hình khi chưa hỏi tình trạng hiện tại; tự kết luận "chưa có" vì mình không thấy (L21).
- Coi "không có kết quả" là "kết quả xấu" hoặc ngược lại mà chưa đọc log của công cụ (L1).
- Chạy lại một lỗi do agent gây ra (thành thử lại đến khi thành công, L1).
- Ghi đè kết quả của thí nghiệm khác (L6). Thay đổi thiết kế giữa chừng phải chạy thành giai đoạn riêng (L12).
- Vượt ngân sách @thuthuy đã duyệt. Trần tính từ số đã chi thực tế (L8).
- Để mất dữ liệu gốc: sau mỗi giai đoạn chạy `python scripts/archive_raw.py` (các script chạy tự gọi), kiểm bằng `python scripts/verify_archive.py`. Không xóa `runs/` hay `logs/` trước khi lô đã lên nhánh `raw-archive` (A52, `docs/raw_archive.md`).

## File tham chiếu
| Việc | File |
| --- | --- |
| Kim chỉ nam, nhật ký tiến độ | `TODO.md` |
| Quy tắc, danh sách review §4, mục đang vi phạm §5 | `docs/research_rules.md` |
| Sổ review trước khi chạy | `docs/review_log.md` |
| Lỗi đã gặp (A#, B#, C#) | `docs/audit_pilot.md` |
| Bài học L1–L18 | `docs/lessons_learned.md` |
| Nguồn gốc mọi con số | `docs/number_provenance.md` |
| Ký hiệu và thuật ngữ (một nghĩa duy nhất) | `docs/glossary.md` §7 |
| Kiểm định phương pháp bằng số | `docs/method_check.md`, `scripts/verify_methods.py` |
| Bản đăng ký trước | `docs/preregistration_g1_v2.md`, `_e1.md`, `_e2.md` |
| Kiểm tra tự động trước khi chạy | `scripts/preflight.py` (chạy cả trong CI) |
| Đổi hoặc thêm model (chỉ khi @thuthuy ra lệnh) | `docs/model_switch_checklist.md` |
| Lưu trữ và kiểm tra dữ liệu gốc | `docs/raw_archive.md`, nhánh `raw-archive` |
