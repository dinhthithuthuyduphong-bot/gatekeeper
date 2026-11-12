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
- Ngân sách: chạy không cần hỏi trong mức đã duyệt; **chạm mức đã duyệt thì dừng, chờ @thuthuy quyết** ("nếu khi tổng chi phí lên 30 đô thì chờ tôi quyết định"). Mức hiện tại: E1 91 USD (trần cộng dồn 122,26), E2 45 USD (đã chi 43,04, xong), **thí nghiệm chính 64 USD** (@thuthuy duyệt 04/11/2026: "Oke", gồm cả phép kiểm "model không đổi" ở `docs/preregistration_main_draft.md` §10). **Ô MemGovern 20 USD** (@thuthuy duyệt 04/11/2026: "Cho phép ngân sách"; thử B-M trước, khả thi thì dùng bản MemGovern gốc, `docs/preregistration_main_draft.md` §11e). **Giới hạn tạm thời: tổng chi mới ≤ 50 USD trước 08:00 sáng 05/11/2026 giờ Việt Nam (01:00 UTC)** (@thuthuy 04/11: "Sau khi có E1 và E2 thì tiến hành phân tích và chuyển qua bước tiếp theo không cần confirm, giới hạn tạm thời cho trước 8h sáng mai là 50 USD"; nằm trong các mức đã duyệt ở trên). **T4 (đối chứng dương trên agent thật) trần 6 USD** (@thuthuy 05/11: "Làm T1–T4 trước"; nằm trong 64 USD của thí nghiệm chính). **Danh sách mạnh nhất (`docs/todo_strongest.md`), @thuthuy 05/11: "Duyệt hết":** 2.1 pilot skill "cách chạy test" trần **3 USD**; 2.3 đo model thứ hai khoảng **1 USD** (chờ thông tin khóa); 2.2 và 2.4 phải báo con số đo được và chờ @thuthuy chốt trần. Chỉ chi sau khi bản đăng ký trước được commit, review và chạy thử miễn phí. **Kế hoạch tái hiện (`docs/plan_replication.md`): trần 60 USD** (@thuthuy 06/11: "Tôi chấp nhận bỏ ra tầm 60 đô chạy thực nghiệm chính thêm"; "thử cái đó trước để dự đoán, tích cực thì mới đi tốt"), chia theo track và cổng dừng; phép thử tín hiệu §22 trần 5 USD. **§23 (sau D-M11), @thuthuy 06/11:** 23a model Pro trần **3 USD**, nâng lên **5 USD** ("Tăng 2 đô cho phương án 1 nếu cần", ghi chú 23-1); 23b model Flash trần **7 USD** cho cả sàng lọc và xác nhận ("Tăng phương án 1 lên 3 đô thử với model mạnh là pro. Tăng phương án 2 lên 7 đô với model mạnh hơn là flash"); nằm trong 60 USD. **Ngân sách mới 40 USD cho Bleve và MemGovern** (@thuthuy 06/11: "Chọn cả bleve và Memgovern, ngân sách mới là 40 đô"): Bleve chạy trước (§25 bước 4), MemGovern dùng phần còn lại; tổng hai track ≤ 40 USD. **Bổ sung 7–10 USD nếu MemGovern thiếu** (@thuthuy 06/11: "Có thể bổ sung từ 7 đến 10 đô nếu thiếu", sau khi §5 không đạt và phải chạy cả hai nhánh): tổng hai track ≤ 50 USD; chỉ dùng phần bổ sung khi 40 USD không đủ. **MemGovern đã dừng** (@thuthuy 07/11: "Dừng memgorven"; chi 5,28 USD; phần bổ sung không dùng). Bleve giữ các trần của §25 bước 4, trong phần 40 − 5,28 = 34,72 USD. **Đã chi đến 08/11:** Bleve 15,88 USD (xong), §27 5,77 USD (xong; @thuthuy duyệt 7 USD), MemGovern 5,28 USD; tổng 26,93 trong 40 USD. **§29 ablation trần 4,00 USD** (@thuthuy 08/11: "Duyệt 4 đô"; dự kiến 3,38; trần nhánh 1,75 + 2,25); **đã chi 2,98, xong**). **§30 học lại trong môi trường một commit: trần 20 USD** (@thuthuy 10/11: "Duyệt trần 20usd"; trần đăng ký 14,50 học + 5,00 chấm = 19,50). **Bậc 0 và 1 của `docs/plan_astar.md`** (@thuthuy 12/11: "Làm bậc 0 và 1 trước"): bậc 0 miễn phí (§32); bậc 1 gồm §33 seed thứ hai (trần 8,35 USD) và §34 agent Flash trên 34 task (trần 5,0 USD; **nâng lên 6,05 USD**, @thuthuy 12/11: "Duyệt 6.05", sau khi bước đo thử cho thấy cả mục cần khoảng 5,38 USD; **§34 xong: đã chi 5,20 USD**). **§35 (36 task Jinja mới, xác nhận phần do môi trường): trần 3,95 USD** (@thuthuy 12/11: "Chọn bản mạnh hơn"). **§30 xong: đã chi 14,66 USD** (học 10,99; chấm 3,67, gồm chạy bù 0,75 với trần 1,70 do @thuthuy duyệt 10/11).
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

## Quyền quyết định (bài học L26, L27)
**@thuthuy quyết** (chỉ những việc sau):
1. Tiền **vượt** mức đã duyệt, hoặc một ngân sách mới.
2. Câu hỏi nghiên cứu, phạm vi kết luận của paper, venue, việc thêm hoặc bỏ một thí nghiệm.
3. Việc ra bên ngoài: công bố, liên hệ người khác; tài khoản, khóa, quyền truy cập.
4. Đánh đổi giữa các phương án **không có phương án nào trội hơn**, tức một phương án mạnh hơn nhưng đắt hơn (cần một phán đoán giá trị).

**Tôi tự quyết, ghi lý do, rồi báo sau:**
- Mọi việc kỹ thuật và vận hành, việc sửa lỗi, và lựa chọn phương pháp theo chuẩn đã công bố.
- **Mọi phương án trội:** không kém hơn về độ mạnh và tính hợp lệ, không đắt hơn, không lâu hơn, nằm trong ngân sách đã duyệt và trong hướng @thuthuy đã chọn. Hỏi về phương án trội chỉ làm tốn thời gian.

**Khi cần @thuthuy quyết**, ghi đủ ba điều:
1. vì sao việc này thuộc quyền @thuthuy (mục nào ở trên);
2. ảnh hưởng tới sức mạnh của research, bằng số (power, n, chi phí, điều reviewer có thể bắt bẻ);
3. lời khuyên của tôi, kèm lý do.

Gửi yêu cầu **sớm nhất có thể**, kèm hạn cần trả lời, để không làm chậm việc khác.

**Lập kế hoạch (L27):** thiết kế thí nghiệm chính song song với pilot ngay từ đầu, để pilot sinh dữ liệu dùng lại được (ước lượng tham số, nối tiếp e-process). Mỗi giai đoạn mới phải trả lời: "dữ liệu này có dùng lại được ở giai đoạn sau không, và cần chốt gì trước để dùng lại được?"

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
| Độ trung thành với hệ thống bên thứ ba (gskill, MemGovern), câu chữ được phép dùng trong paper | `docs/reviewer_fidelity.md` |
