# Quy tắc nghiên cứu (bắt buộc, từ 03/11/2026)

Đặt bởi @thuthuy. Áp dụng cho **mọi** đề xuất, mã, quy tắc, khái niệm và con số đưa vào quy trình nghiên cứu. `TODO.md` dẫn tới tài liệu này. Khi một quy tắc dưới đây xung đột với thói quen làm việc cũ, quy tắc này thắng.

## R1. Mọi đề xuất phải có lý do và nguồn công bố

Mỗi đề xuất (phương án, thiết kế, ngưỡng, phương pháp) phải trả lời đủ ba câu hỏi:

1. **Tại sao** đề xuất như vậy: vấn đề cụ thể nào nó giải quyết.
2. **Dựa trên đâu:** định lý, công thức hoặc kết quả thực nghiệm **đã công bố**.
3. **Đã đọc bản gốc chưa:** trích được câu hoặc công thức trong tài liệu, kèm vị trí (mục, trang, dòng mã).

Không được dựa vào "hiểu biết chung" hay trí nhớ. Nguồn phải được tải về và lưu đoạn trích (`configs/sources.json` → workflow `sources` → nhánh `sources-snapshots`). Một nguồn tải về nhưng **không chứa** câu cần trích thì coi là **chưa xác nhận**. Ví dụ: trang model card của Gemini tải được nhưng không có chữ "Knowledge cutoff" (§5, mục N3).

## R2. Mọi con số và khái niệm phải được chứng minh trước khi vào quy trình

Mỗi con số thuộc đúng một nhóm, ghi trong `docs/number_provenance.md`:

| Nhóm | Điều kiện để được dùng |
| --- | --- |
| **Chuẩn công bố** | Trích được từ tài liệu gốc (ví dụ α một phía 0,025: ICH E9) |
| **Suy ra** | Có công thức công bố, và mọi đầu vào của công thức đều đo được hoặc thuộc nhóm "chuẩn công bố" |
| **Lấy từ công cụ hay bộ dữ liệu bên thứ ba** | Trích được dòng mã hoặc cấu hình gốc (ví dụ `top_n = 3`: `configs/pipeline.yaml` của XRepoSkill tại commit đã ghim) |
| **Định nghĩa can thiệp** | Con số định nghĩa *cái được kiểm*, không phải tham số suy luận (ví dụ regex I(x)). Phải chốt trước khi có dữ liệu và công bố |
| **Vận hành** | Chỉ quyết định *khi nào* hoặc *bao nhiêu lần* một việc chạy, không quyết định *kết quả*. Phải chứng minh được điều đó (lỗi thì chạy lại hoặc dừng, không bao giờ âm thầm đổi dữ liệu) |

Một con số hay khái niệm **tự đặt**, không thuộc nhóm nào ở trên, thì **không được dùng**. Phải làm một trong ba việc: (a) tìm tài liệu công bố để trích; (b) thay bằng cách làm không cần con số đó (ví dụ báo cáo đường cong thay cho một ngưỡng); (c) hỏi @thuthuy cho phép, và ghi rõ là đầu vào giá trị.

Một con số **phải thử nhiều lần mới chọn được** chỉ hợp lệ khi việc thử dùng một quy tắc chọn đã công bố (ví dụ GRO cho c), làm trên dữ liệu **không** dùng để kết luận, và quy tắc được ghi lại trước.

## R3. Mọi mã và quy tắc phải được review trước khi thực thi

Trước khi chạy bất kỳ mã hay quy tắc mới hoặc vừa sửa nào trên dữ liệu thật hoặc với chi phí thật, phải đi qua **danh sách kiểm tra review** (§4). Kết quả review được ghi vào `docs/review_log.md`: ngày, file hoặc commit, từng mục đã kiểm, phát hiện. Không ghi được review thì chưa được chạy.

## R4. Mọi lỗi phải được ghi lại để không tái phạm

Mỗi lỗi tìm thấy được ghi ở hai nơi:

- `docs/audit_pilot.md`: lỗi là gì, ảnh hưởng gì, sửa thế nào, bằng chứng (test, số đo).
- `docs/lessons_learned.md`: **nguyên nhân gốc** (vì sao lỗi lọt qua), **cách phát hiện**, và **biện pháp phòng ngừa** (một test, một mục trong danh sách review, hay một quy tắc). Mỗi bài học phải biến thành ít nhất một mục kiểm tra trong §4, để lần sau không phụ thuộc vào trí nhớ.

## R5. Không đổi quy tắc sau khi thấy dữ liệu

- Thiết kế và phân tích được đăng ký trước (Nosek et al. 2018).
- Thay đổi chỉ được phép trước khi mở kết quả, phải ghi thành "Ghi chú thực thi" có ngày và lý do.
- Thay đổi không được làm khi đã có lý do nghi ngờ rằng mình đã thấy kết quả. Nếu đã lỡ thấy một phần dữ liệu thì giữ quy tắc cũ và báo cáo giới hạn (ví dụ C7).

## R6. Thuật ngữ, ký hiệu và ngưỡng phải rõ nghĩa (@thuthuy: "Tôi không chấp nhận những ngưỡng mơ hồ và tối nghĩa, mọi thứ phải thực sự rõ ràng để không bị reviewer bắt bẻ")

1. **Định nghĩa trước khi dùng:** mọi ký hiệu và thuật ngữ được định nghĩa trong `docs/glossary.md` §7 trước khi xuất hiện trong bản đăng ký trước, báo cáo hay paper. Định nghĩa phải chính xác (công thức hoặc thủ tục) và kèm nguồn.
2. **Một nghĩa duy nhất:** một ký hiệu không mang hai nghĩa (A43: R từng có 3 nghĩa). Viết tắt phải được giải nghĩa.
3. **Ngưỡng đầy đủ:** mọi ngưỡng ghi đủ giá trị, chiều (một phía hay hai phía), đại lượng áp dụng, và nguồn hoặc nhóm R2.
4. **Không từ đánh giá mơ hồ:** các từ "gần như", "rất", "khá", "hơi", "đáng kể", "mạnh", "yếu", "quy mô nhỏ/lớn" chỉ được dùng khi câu có con số. Phép so sánh có đối tượng ("nhỏ hơn δ", "ít nhất θ") được phép.
5. **Phân loại mức độ bằng hậu quả đã định nghĩa** (K1/K2/K3), không bằng nhãn cảm tính.
6. **Kiểm tự động:** preflight [terms] quét các tài liệu sẽ vào paper (`docs/method_check.md`, bản đăng ký trước E1/E2, `docs/glossary.md`). Phát hiện → FAIL → không commit, không chạy. Tài liệu mới sẽ vào paper phải được thêm vào danh sách `PAPER_DOCS` của `scripts/preflight.py`.

## §3b. Review song song: file nào, theo quy trình nào

Trong khi một thí nghiệm chạy nền (E1, E2), tác vụ kế tiếp được chuẩn bị và review **song song**. Hai tác vụ không bao giờ chạy có chi phí cùng lúc nếu chúng dùng chung tài nguyên (L12, A32).

| Bước | Làm gì | File |
| --- | --- | --- |
| 1. Đọc | Bản đăng ký trước của tác vụ, kể cả mọi ghi chú thực thi và sai lệch D# | `docs/preregistration_*.md` |
| 2. Nguồn | Mỗi khẳng định → một mục trong cấu hình nguồn → workflow `sources` → đoạn trích chứa đúng câu cần dùng | `configs/sources.json`, nhánh `sources-snapshots` |
| 3. Con số | Mỗi con số → một nhóm R2 | `docs/number_provenance.md` |
| 4. Ký hiệu | Mỗi ký hiệu một nghĩa | `docs/glossary.md` §7 |
| 5. Phương pháp | Mô phỏng quy tắc quyết định cuối cùng: tỉ lệ sai và power | `scripts/verify_methods.py` → `docs/method_check.md` |
| 6. Mã | Đối chiếu từng mục §4 dưới đây; test cho từng chỗ sửa | `tests/` |
| 7. Tự động | `python scripts/preflight.py` (cũng chạy trong CI ở mỗi lần push) | `scripts/preflight.py` |
| 8. Chạy thử | Mô hình giả lập trên ≥ 1 task thật, 0 USD | `results/pilot/*dryrun*.json` |
| 9. Ghi review | Mục R-# với từng kiểm tra đã làm và phát hiện | `docs/review_log.md` |
| 10. Chạy, rồi kiểm | `infra_failures`, `endpoint_mismatch`, `patch_apply_failed`, trạng thái kết thúc | file kết quả của lô |
| 11. Lỗi (nếu có) | Lỗi → A#; nguyên nhân gốc → L#; phòng ngừa → mục §4 hoặc kiểm tra trong preflight | `docs/audit_pilot.md`, `docs/lessons_learned.md` |

## §4. Danh sách kiểm tra review (trước khi thực thi)

Mỗi mục lấy từ một lỗi đã xảy ra (số trong ngoặc là mã lỗi ở `docs/audit_pilot.md`).

**Đối chiếu với bản đăng ký trước**
- [ ] Mọi seed, chuỗi ngẫu nhiên, tập task, họ kiểm định (Holm), mức α trong mã **trùng từng ký tự** với bản đăng ký trước (A25, họ Holm của E1).
- [ ] Mọi quy tắc so sánh nhận **cùng dữ liệu** (A26).
- [ ] Mọi phân tích đã cam kết có đủ dữ liệu đầu vào được *lưu* (A28).

**Endpoint và chấm điểm**
- [ ] Endpoint trong mã khớp với định nghĩa của harness gốc trên **mọi** trường hợp biên: danh sách test rỗng, patch không áp được, không có report (A29). Có kiểm khớp tự động khi chạy (`endpoint_mismatch`).
- [ ] Harness dùng đúng bản tác giả bộ dữ liệu chỉ định (README hoặc mã gốc) (A35).
- [ ] Không chấm patch mới bằng report cũ (A21).

**Biến cố xen giữa và dữ liệu thiếu (ICH E9(R1))**
- [ ] Mọi trạng thái kết thúc mà công cụ có thể trả về đã được liệt kê **từ mã nguồn của công cụ**, và mỗi trạng thái được phân loại: do hành vi của chính sách (biến cố xen giữa, giữ lại) hay do hạ tầng (dữ liệu thiếu, chạy lại) (A2, A27).
- [ ] Bước "đã đủ dữ liệu chưa" dùng cùng quy tắc với bước chạy lại (A18, A31).

**Ghi file và tái lập**
- [ ] Không script nào ghi đè kết quả của thí nghiệm khác (A24).
- [ ] Không bước nào lỗi âm thầm: `continue-on-error`, `except` rồi đi tiếp, resume đọc lại kết quả lỗi (A33, A34).
- [ ] Phiên bản của mọi bộ dữ liệu và công cụ bên ngoài được ghim hoặc ghi lại (commit, revision) (A33, A35).
- [ ] Không phân phối lại nội dung không có giấy phép.

**Ngân sách**
- [ ] Trần ngân sách được tính từ **số đã chi thực tế**, không phải từ giả định về chi phí của thí nghiệm trước (A32).
- [ ] Hai tiến trình không dùng chung tài nguyên có thể xóa của nhau (image Docker, đĩa).

**Con số**
- [ ] Mọi con số mới đã được xếp vào một nhóm của R2 và ghi trong `docs/number_provenance.md`.
- [ ] Mọi câu "theo X" trong tài liệu đã có đoạn trích của X trong `sources-snapshots` **chứa đúng nội dung đó** (R1).

**Power của quy tắc quyết định (L11)**
- [ ] Quy tắc quyết định **cuối cùng**, bao gồm hiệu chỉnh bội và mọi điều kiện kèm theo, đã được mô phỏng trên đúng thiết kế (`scripts/verify_methods.py`), cả tỉ lệ sai lẫn power, trước khi đăng ký trước.
- [ ] Quy tắc quyết định theo chuẩn công bố, không chặt hơn chuẩn mà không có lý do đã công bố.

**Ký hiệu và mặc định (L13)**
- [ ] Hàm nhận con số khoa học (α, θ, cách chia α) không có giá trị mặc định. File kết quả không chứa con số mà không phân tích nào dùng.
- [ ] "Theo chuẩn X" ghi rõ một phía hay hai phía, kèm câu gốc.
- [ ] Mỗi ký hiệu có đúng một nghĩa trong `docs/glossary.md` §7. Không dùng từ đánh giá (mạnh, yếu, gần như) khi không kèm con số.

**Bước kiểm phải chặn được (L15)**
- [ ] Mỗi bước kiểm trả mã thoát khác 0 khi thất bại và đứng trước hành động cần chặn (`python scripts/preflight.py --ci && git commit …`). Đã thử với một ca xấu có chủ đích.

**Chạy song song (L16)**
- [ ] Các việc chạy cùng lúc không ghi chung file, thư mục, tên container hay image. Phần tính kết quả vẫn tuần tự và giữ thứ tự cũ.

**Bản sửa và tiến trình đang chạy (L22)**
- [ ] Sau khi commit một bản sửa ảnh hưởng đến kết quả: liệt kê tiến trình đang chạy và thời điểm khởi động. Tiến trình nào khởi động trước bản sửa thì kết quả của nó phải được xử lý theo quy tắc mới trước lô kế tiếp.

**Chi phí (L23)**
- [ ] Sau mỗi lần chạy có chi phí: tổng mới = tổng cũ + phần mới, tính từ bản ghi của từng yêu cầu, không từ danh sách đầu vào của lần gọi.

**Kết quả bị bác bỏ (L25)**
- [ ] Khi một kết quả bị bác bỏ: tìm con số đó ở mọi file (`docs/`, `TODO.md`, `paper/`), gạch đi, dẫn tới mục audit. Khi báo cáo: lấy số từ file kết quả hiện hành, không từ bảng tóm tắt.

**Không xem kết quả trước khi phân tích (L28)**
- [ ] Lệnh đọc file kết quả trong lúc thí nghiệm đang chạy chỉ in trường vận hành (chi phí, token, lỗi, trạng thái), không in `solved` hay `solve_rate` của nhánh skill, không in Z.

**Đề xuất có chi phí (L38)**
- [ ] Mỗi pilot hay thí nghiệm có chi phí phải kèm cận trên của mức tăng δ tính từ dữ liệu đã có, và xác suất qua cổng ở cận trên đó. Cận trên thấp hơn cổng thì không đề xuất.

**Plasmode và độ phủ (L39)**
- [ ] "Giá trị thật" trong mô phỏng được định nghĩa trên tham số của mô hình sinh dữ liệu, đúng đại lượng mà bộ ước lượng nhắm tới. Ở trường hợp không có hiệu ứng, độ phủ phải gần mức danh nghĩa.

**Power của tương quan và chuyển giao (L41)**
- [ ] r kỳ vọng tính từ hiệp phương sai giữa các cấu hình (phần chuyển giao được) và nhiễu đo được của chính phép đo sẽ chạy; con số power ra từ script đã commit. Power < 0,8 thì câu hỏi chỉ là mô tả.

**Mô tả thiết lập trong paper (L49)**
- [ ] Mỗi câu về dataset, n, seed, ngân sách trong paper dẫn được tới `configs/pools/*.json` hoặc bản đăng ký trước (kể cả ghi chú thực thi); con số thiết lập là macro sinh từ file khi có thể.

**Kiểm thử**
- [ ] Mô phỏng hoặc phép toán mảng: assert kích thước kết quả, vì broadcasting âm thầm làm rộng mẫu (R-6).
- [ ] Có test cho từng chỗ sửa; `ruff check`, `ruff format --check` và `pytest` đều qua.
- [ ] Chạy thử miễn phí (mô hình giả lập, không gọi LLM) trên ít nhất một task thật của bộ dữ liệu mới trước khi chạy có chi phí.

## §5. Các mục đang vi phạm R1 hoặc R2 (phải xử lý trước khi dùng)

| # | Mục | Vấn đề | Xử lý |
| --- | --- | --- | --- |
| N1 | Ngưỡng "rule được chọn ở ≥ 10 task" (E2 §5.6, phân tích theo rule) | Tự đặt, không có nguồn | **Bỏ ngưỡng**: báo cáo mọi rule, kèm số task, chỉ mô tả (không suy luận) |
| N2 | Lập luận "chi phí tăng gần bình phương theo số bước" (E1 §2) | Ngoại suy, không có nguồn | Đã thay bằng số đo (lần chạy đắt nhất 0,53 USD < 1,00 USD; `docs/audit_pilot.md` B5) |
| N3 | Mốc cắt dữ liệu huấn luyện "01/2025" của Gemini 3.1 Flash-Lite (E2 §5.6) | Trang gốc tải được nhưng **không chứa** thông tin này; con số chỉ đến từ kết quả tìm kiếm | **Chưa dùng.** Phân tích nhiễm dữ liệu của E2 bị treo cho đến khi trích được câu gốc từ Google |
| N6 | Wikipedia làm nguồn cho Holm, Wald, Ville, ICER, mutation testing | Nguồn thứ cấp | Đã thay bằng nguồn gốc hoặc bình duyệt (A45). Chờ workflow nguồn xác nhận đoạn trích |
| N4 | Phân loại `ContextWindowExceededError` là hành vi của agent | Trước đây chỉ là lập luận của tôi | Cơ sở: ICH E9(R1) phân biệt biến cố xen giữa (thuộc estimand) với dữ liệu thiếu. Trích nguyên văn: "the addendum distinguishes discontinuation of randomised treatment from study withdrawal. The former represents an intercurrent event … The latter gives rise to missing data". Trajectory vượt context là hệ quả của chính chính sách (agent + skill), không phải lỗi bên ngoài. Kiểm lại khi tải đủ định nghĩa "treatment policy strategy" |
| N5 | Số lần thử lại khi chọn rule (4) và khi kiểm định pool (2 lần, cách 90 s) | Nhóm vận hành | Chứng minh không ảnh hưởng kết quả: còn lỗi thì **dừng**, không ghi tập task (`xreposkill_select.py`) hoặc ghi "infra" và loại khỏi pool (`validate_pool.py`) |
