# Bài học từ các lỗi (để không tái phạm)

Mỗi lỗi ở `docs/audit_pilot.md` (A1–A35) được nhóm theo **nguyên nhân gốc**: vì sao lỗi lọt qua, chứ không chỉ lỗi là gì. Mỗi nhóm kết thúc bằng **biện pháp phòng ngừa**. Mỗi biện pháp đã thành một mục trong danh sách review (`docs/research_rules.md` §4) hoặc một test, để lần sau không phụ thuộc vào trí nhớ. Quy tắc R4: lỗi mới phải được thêm vào đây.

## L1. Coi "không có kết quả" là "kết quả xấu" (A1, A2, A3, A17, A18, A27, A31)

- **Xảy ra:**
  - Image chưa tải, container không chạy hoặc harness không ra report từng bị tính là "agent không giải được" (A1–A3).
  - Theo chiều ngược lại, một hành vi thật của agent (`RepeatedFormatError`) bị tính là lỗi hạ tầng và loại khỏi phân tích (A27).
  - Task lỗi hạ tầng từng bị coi là "đã xong" (A17, A18, A31).
- **Nguyên nhân gốc:** tôi viết danh sách trạng thái **từ trí nhớ**, không đọc mã nguồn của công cụ. Bước "đã đủ chưa" và bước "chạy lại gì" được viết riêng, theo hai quy tắc khác nhau.
- **Cơ sở đúng:** ICH E9(R1) phân biệt *biến cố xen giữa* (thuộc estimand, giữ trong phân tích theo chiến lược đã chọn) với *dữ liệu thiếu* (xử lý trong phân tích thống kê). Trích nguyên văn: "the addendum distinguishes discontinuation of randomised treatment from study withdrawal. The former represents an intercurrent event … The latter gives rise to missing data".
- **Phòng ngừa:**
  - Liệt kê trạng thái **từ mã nguồn** của công cụ (`minisweagent/agents/default.py`, `exceptions.py`) và có test cho từng trạng thái.
  - Một hàm duy nhất quyết định "đã xong" (`done_tasks`), dùng chung cho resume và cho bước kiểm (`missing_tasks.py`).

**Bổ sung L1** (A36, A37, 03/11/2026):
- **Xảy ra:** "không có report" bị coi là lỗi hạ tầng, trong khi nguyên nhân là **bản vá do agent viết** không áp được.
- **Hậu quả:** chạy lại một lỗi do agent gây ra là cho agent **thử lại đến khi thành công**. Đó là chọn lọc, làm lệch kết quả về phía có lợi.
- **Phòng ngừa:**
  - Trước khi xếp một trường hợp vào "hạ tầng", đọc log của chính công cụ để biết *nguyên nhân*. Ở đây là `run_instance.log`, chuỗi `APPLY_PATCH_FAIL` của harness.
  - Chỉ chạy lại những gì chắc chắn không do chính sách gây ra.
  - Chạy thử trên **bộ dữ liệu mới** luôn có thể lộ ra khác biệt môi trường (A36: image Live có file chưa theo dõi).

## L2. Mã lệch khỏi bản đăng ký trước mà không ai phát hiện (A25, A26, họ Holm của E1)

- **Xảy ra:**
  - Seed thứ tự sàng lọc trong mã khác một hậu tố so với bản đăng ký trước.
  - Hai quy tắc so sánh nhận dữ liệu khác nhau.
  - Trong ghi chú việc cần làm, tôi định chạy Holm trên 6 skill trong khi bản đăng ký trước nói 3 skill.
- **Nguyên nhân gốc:** mã được viết **song song** với văn bản, rồi không ai đối chiếu từng dòng. Tôi "nhớ" thiết kế thay vì đọc lại văn bản.
- **Phòng ngừa:**
  - Bản đăng ký trước ghi **lệnh phân tích đầy đủ** (đối số, họ kiểm định, file ra), và lệnh đó là thứ được chạy.
  - Danh sách review có mục "trùng từng ký tự với bản đăng ký trước".
  - Mỗi quy tắc so sánh có test "nhận cùng dữ liệu".

## L3. Định nghĩa endpoint tự viết lại thay vì dùng của harness (A29, A21)

- **Xảy ra:** loss = 0 được dùng làm "resolved", nhưng trường hợp FAIL_TO_PASS rỗng thì khác với harness. Trước đó, harness bỏ qua task đã có report (A21).
- **Nguyên nhân gốc:** tôi dịch lại định nghĩa của người khác sang mã của mình, nhưng không kiểm **các trường hợp biên** trong mã gốc (`compute_fail_to_pass` trả về 1 khi danh sách rỗng).
- **Phòng ngừa:**
  - Kiểm khớp tự động ở **mỗi** lần chạy: loss 0 ⇔ cờ `resolved` của harness, mọi chỗ lệch được ghi lại (`endpoint_mismatch`).
  - Pool loại task không có test đích.
  - Mỗi lần dùng harness mới, đọc hàm chấm của nó trước.

## L4. Dùng công cụ mà không đọc hướng dẫn của tác giả (A35, A4, A5, A6, A12, A14)

- **Xảy ra:**
  - Định chấm SWE-bench-Live bằng harness chuẩn, trong khi README của họ chỉ định bản fork riêng (A35).
  - Giá model không đăng ký nên cost_limit = 0 (A4); sai tên model (A5); sai location (A6).
  - Seed 0 của Vertex nghĩa là "không đặt seed" (A14).
- **Nguyên nhân gốc:** giả định rằng công cụ "tương thích" thì cách dùng giống nhau.
- **Phòng ngừa:**
  - Với mỗi bộ dữ liệu hay công cụ mới: tải README hoặc tài liệu gốc qua workflow `sources` và đọc phần "how to evaluate" **trước khi** viết mã.
  - Ghim commit hoặc phiên bản.
  - Chạy thử miễn phí trên một task thật.

## L5. Lỗi âm thầm (A33, A34, A15, A16)

- **Xảy ra:**
  - Bước xuất dữ liệu hỏng nhưng bị `continue-on-error` che (A33).
  - Bước chọn rule ghi lỗi rồi đi tiếp, và resume đọc lại lỗi (A34).
  - File phân tích bị cộng vào chi phí (A15); số đếm mất khi gộp (A16).
- **Nguyên nhân gốc:** ưu tiên "chạy tiếp được" hơn "dừng khi sai". Không kiểm đầu ra so với kỳ vọng (số dòng Live phải là 120, thực tế là 0).
- **Phòng ngừa:**
  - Mỗi bước sinh dữ liệu phải **kiểm đầu ra** (số lượng, khóa bắt buộc) và dừng nếu sai.
  - Không dùng `except` rồi đi tiếp cho dữ liệu nghiên cứu.
  - Danh sách review có mục "không bước nào lỗi âm thầm".

## L6. Một script ghi đè kết quả của script khác (A24)

- **Xảy ra:** `verdict` luôn ghi vào file của G1.
- **Nguyên nhân gốc:** script viết cho một thí nghiệm, rồi được dùng lại cho thí nghiệm khác mà không đổi đường dẫn ra.
- **Phòng ngừa:** khi dùng lại cho thí nghiệm khác thì bắt buộc truyền `--out` (script tự từ chối nếu thiếu). Danh sách review có mục "không ghi đè".

## L7. Thiếu dữ liệu cho phân tích đã cam kết (A28, A16)

- **Xảy ra:** bản đăng ký trước hứa phân tích theo trạng thái bị cắt, nhưng mã không lưu trạng thái đó.
- **Nguyên nhân gốc:** viết bản đăng ký trước xong nhưng không lần ngược từ từng phân tích về dữ liệu cần lưu.
- **Phòng ngừa:** với mỗi mục trong phần phân tích của bản đăng ký trước, ghi rõ trường dữ liệu nào cung cấp nó, rồi kiểm trường đó có trong file kết quả của lô đầu tiên.

## L8. Ngân sách tính từ giả định thay vì số thực (A13, A32)

- **Xảy ra:** trần theo từng lượt (A13); trần E2 cộng cố định trên ngân sách đầy đủ của E1 (A32).
- **Phòng ngừa:** trần = số đã chi thực tế (đọc từ các file kết quả) + phần được duyệt, tính lúc chạy.

## L9. Con số tự đặt (A11, A19, A22, các ngưỡng ở `docs/number_provenance.md` §2, N1–N3 ở `docs/research_rules.md` §5)

- **Xảy ra:**
  - Ngưỡng đối chứng dương, CI 90%, step_limit 100, κ ≥ 0,7, "≥ 10 task mỗi rule", "chi phí tăng gần bình phương", và mốc cắt dữ liệu lấy từ kết quả tìm kiếm.
  - A11 còn thiên lệch do hồi quy về trung bình (A19).
- **Nguyên nhân gốc:** chọn con số "hợp lý" theo cảm tính, rồi viết lý do sau.
- **Phòng ngừa:** quy tắc R2. Mọi con số phải vào một nhóm có điều kiện kiểm được. Con số không có nguồn thì thay bằng cách làm không cần nó (đường cong, chuẩn mặc định của công cụ) hoặc hỏi @thuthuy.

## L10. Tham số vận hành ảnh hưởng kết quả (A22, A9, A20)

- **Xảy ra:** step_limit 100 làm nhánh skill bị cắt nhiều hơn (A22).
- **Nguyên nhân gốc:** coi một tham số là "chỉ vận hành" mà không chứng minh nó không đổi kết quả.
- **Phòng ngừa:**
  - Tham số vận hành phải có bằng chứng không ảnh hưởng kết quả (số đo cho thấy giới hạn không chạm, hoặc lỗi thì chạy lại).
  - Nếu ảnh hưởng thì dùng mặc định của tác giả công cụ.
  - Báo cáo tỉ lệ chạm giới hạn theo nhánh.

## L11. Quy tắc quyết định tự đặt, chưa kiểm power (A38, A39, C8)

- **Xảy ra:**
  - Cỡ mẫu tính ở mức α không có hiệu chỉnh bội (A38).
  - Quy tắc "mọi phân tích độ nhạy cùng phải bác bỏ" làm power gần 0 (A39).
  - RQ1 thu nhỏ được thiết kế với 40 trial, trong khi bảng plasmode đã cho biết cần 186–413 trial (C8).
- **Nguyên nhân gốc:**
  - Mỗi thành phần được chọn riêng lẻ mà **không ai mô phỏng toàn bộ quy tắc quyết định** trên chính thiết kế sẽ chạy.
  - Quy tắc "chặt hơn" bị coi là "an toàn hơn", trong khi nó làm mất khả năng phát hiện.
- **Phòng ngừa:**
  - Trước khi đăng ký trước, chạy `scripts/verify_methods.py` cho **đúng quy tắc quyết định cuối cùng**, trên đúng cỡ mẫu, số cụm và mức α. Báo cả tỉ lệ sai lẫn power.
  - Quy tắc quyết định phải theo chuẩn công bố (ICH E9(R1): phép ước lượng chính quyết định, phân tích độ nhạy để báo cáo).
  - Danh sách review §4 có mục tương ứng.

## L12. Thay đổi thiết kế giữa chừng tương tác với quy tắc gộp dữ liệu (A40)

- **Xảy ra:** mở rộng cỡ mẫu tưởng chỉ là "thêm task". Nhưng task mới trùng với task cũ của skill khác, và quy tắc gộp sẽ xóa dữ liệu cũ.
- **Phòng ngừa:**
  - Mọi thay đổi thiết kế giữa chừng (thêm task, seed, nhánh) phải chạy thành giai đoạn riêng, có bước gộp với kiểm tra trùng.
  - Trước khi chạy, kiểm chồng lấn giữa tập mới và tập cũ.

## L13. Quy ước bị gắn nhầm nguồn, và mặc định tự đặt nằm trong mã (A41, A42, A43)

- **Xảy ra:**
  - "0,05 (ICH two-sided convention)" bị dùng cho một phép kiểm một phía.
  - θ = 0,05 và α = 0,05 mặc định được ghi vào file kết quả.
  - θ = 1e-9 chỉ để lách một ràng buộc không có cơ sở.
  - Ký hiệu trùng nghĩa.
- **Nguyên nhân gốc:**
  - Viết lý do sau khi đã chọn số.
  - Không phân biệt kiểm một phía với hai phía.
  - Để giá trị mặc định trong hàm, nên con số đi vào kết quả mà không ai quyết định.
- **Phòng ngừa:**
  - Mọi hàm nhận con số khoa học (α, θ, cách chia) **không có giá trị mặc định**.
  - Mỗi câu "theo chuẩn X" phải ghi rõ **một phía hay hai phía** và trích câu gốc.
  - Mỗi ký hiệu chỉ một nghĩa (`docs/glossary.md` §7).
  - Danh sách review có mục tương ứng.

## L14. Rà tay bỏ sót; quy trình phải nằm trong file được tự động nạp và trong kiểm tra tự động (A44, A45, A46)

- **Xảy ra:**
  - Lượt rà tay bỏ sót 4 con số mặc định.
  - Một công cụ lấy nguồn âm thầm làm mất bản tốt.
  - 5 nguồn là Wikipedia mà không ai để ý.
- **Nguyên nhân gốc:** quy trình nằm trong trí nhớ của người làm (hoặc của tôi, vốn không có trí nhớ giữa các phiên). Các kiểm tra lặp lại được làm bằng tay.
- **Phòng ngừa:**
  - **`CLAUDE.md`** ở gốc repo được nạp tự động ở mọi phiên. File tóm tắt R1–R5, quy trình 8 bước và các điều cấm.
  - **`scripts/preflight.py`** tự động hóa phần kiểm được bằng máy của §4: mặc định khoa học, nguồn, kết quả, khóa bí mật, lint, test. File chạy ở **mọi lần push** (CI).
  - Mỗi lỗi mới có thể kiểm bằng máy phải được thêm thành một kiểm tra trong preflight, không chỉ một dòng trong tài liệu.

## L15. Một bước kiểm không chặn được thì không phải là bước kiểm (A47)

- **Xảy ra:** bước kiểm khóa bí mật in ra số dòng khớp nhưng không bao giờ dừng commit.
- **Phòng ngừa:**
  - Mọi bước kiểm phải **thất bại bằng mã thoát khác 0** và đứng **trước** hành động cần chặn (`check && action`).
  - Mỗi bước kiểm phải được thử với một ca xấu có chủ đích (khóa giả, mặc định giả) để chứng minh nó chặn được.

## L16. Chạy song song cần rà mọi tài nguyên dùng chung (A49)

- **Phòng ngừa:** trước khi cho hai việc chạy cùng lúc, liệt kê mọi file, thư mục, cổng, tên container và image mà chúng ghi hoặc đọc. Mỗi thứ phải riêng, hoặc chỉ đọc. Danh sách review §4 có mục này.

## L17. Mỗi phiên tự kiểm tra và tự nhắc, thay vì dựa vào trí nhớ (A50, yêu cầu "tuân thủ ở mọi phiên")

- **Cơ chế (do công cụ thực thi, không do tôi nhớ):**
  - `.claude/hooks/session-start.sh` chạy ở **mọi** lần bắt đầu, tiếp tục, xóa và tóm tắt phiên. Hook:
    - cài phụ thuộc;
    - cài git hook `pre-commit` (preflight không đạt thì git từ chối commit);
    - in quy tắc R1–R6 và mã lỗi, bài học, biên bản review mới nhất;
    - báo Docker và các giai đoạn dở dang;
    - chạy preflight.
  - Các script chạy có chi phí có cổng preflight.
  - CI chạy preflight ở mọi lần push.
- **Khi dừng một tiến trình giữa chừng:** dừng sau cả bước dọn dẹp của nó, hoặc tự dọn trước khi chạy tiếp.
