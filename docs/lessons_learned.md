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

## L18. Kết quả tóm tắt không phải là bằng chứng; lưu bằng chứng gốc và đối chiếu số lượng (A52)

- **Xảy ra:**
  - Chỉ file tóm tắt được commit; dữ liệu gốc nằm trên một máy tạm.
  - Ở lần lưu trữ đầu, script bỏ sót 108 trajectory. Lỗi chỉ lộ ra khi **đối chiếu tổng số** (1.040 trên máy so với 932 đã lưu).
- **Phòng ngừa:**
  - Mọi dữ liệu gốc của lần chạy có chi phí được lưu ra ngoài máy tạm sau mỗi giai đoạn.
  - Mỗi lần lưu phải **đối chiếu số lượng** với nguồn (trajectory trên máy, số lần chạy trong file kết quả), không chỉ dựa vào việc script chạy xong không lỗi.

## L19. Tham số dừng phải lấy từ số đo, và một lần dừng giữa chừng phải được ghi sổ (A53)

- **Xảy ra:** `--batch-min` 25 là ước tính, nên một lô dài hơn bị giới hạn cứng cắt ngang.
- **Lỗi đo khi sửa:** lần đo đầu dùng thời điểm tạo run id của harness làm mốc bắt đầu, nên bỏ sót thời gian agent chạy. Cách đúng là đo khoảng cách giữa hai lần ghi kết quả liên tiếp.
- **Phòng ngừa:**
  - Mọi tham số dừng lấy từ số đo: trung vị và lô dài nhất.
  - Lô nào bị cắt thì: ghi chi phí từ trajectory, đổi tên trước khi chạy lại, lưu trữ với trạng thái `aborted`.

## L20. Suy luận của chính tôi phải được kiểm bằng số đo trước khi dùng (A54, A56, R-13)

- **Xảy ra, cùng một ngày:**
  - "1 nhánh cho tải 1, nên 3 nhánh cho tải khoảng 3": đo được là 15,6.
  - "tranh CPU không làm chậm khâu chấm": đúng cho task nhẹ, sai cho bộ test nặng.
  - "bỏ bước xóa image là tiết kiệm": làm driver dừng vì tưởng đĩa đầy.
  - Lần đếm lệnh quá giờ đầu tiên cho 0 vì mẫu tìm sai.
- **Phòng ngừa:**
  - Mỗi khẳng định về hiệu năng hay về "không ảnh hưởng kết quả" phải có **số đo trước và sau**.
  - Mỗi bộ đếm phải được kiểm bằng một **ca chắc chắn có** (sanity check) trước khi tin kết quả 0.

## L21. Không đề xuất cài đặt hay thao tác của @thuthuy khi chưa hỏi tình trạng hiện tại (2026-11-03)

- **Xảy ra:**
  - Tôi khẳng định các secret GitHub chưa có và gợi ý tạo khóa mới, nhưng không kiểm và không hỏi.
  - Thực tế `GCP_SA_KEY`, `VERTEXAI_PROJECT` và `VERTEXAI_LOCATION` đều đã có.
  - Hậu quả: mất thời gian của @thuthuy và lệch khỏi hướng chính.
- **Phòng ngừa:**
  - Trước mọi gợi ý cài đặt, tạo khóa hay cấu hình mà @thuthuy phải làm, **hỏi tình trạng hiện tại trước**. Chỉ gợi ý khi đã biết chắc là thiếu.
  - Không tự kết luận "chưa có" từ việc mình không nhìn thấy.
  - Chỉ đề xuất việc phục vụ trực tiếp mục tiêu đang làm (TODO.md).

## L22. Một bản sửa chỉ có hiệu lực với tiến trình khởi động SAU nó (A57)

- **Xảy ra:** bản sửa A56 được commit lúc 12:26, nhưng E1 đã khởi động lúc 11:48 và một lô bắt đầu lúc 11:51. Python đã nạp mã cũ, nên lô đó vẫn chạy theo quy tắc cũ. Tôi ghi trong A56 rằng "chỉ lô p25 (đã bị cắt) có quá giờ" mà không kiểm lô đang chạy.
- **Phòng ngừa:**
  - Mỗi lần commit một bản sửa ảnh hưởng đến kết quả: liệt kê các tiến trình đang chạy (`ps -eo lstart,cmd`), so thời điểm khởi động với thời điểm sửa.
  - Kết quả của các tiến trình chạy mã cũ phải được xử lý theo quy tắc mới, bằng một script có test, trước lô kế tiếp.
- **Bổ sung L22 (A57):** một script sửa dữ liệu phải được kiểm bằng cách so **từng bản ghi trước và sau** với nguồn gốc (ở đây: task nào nhánh nào đã chạy), không chỉ bằng test trên dữ liệu giả. Test giả của tôi cho mọi nhánh chạy mọi task, nên không bắt được lỗi tạo cặp bịa.

## L23. Số tiền đã chi phải được tính từ bằng chứng của **mọi** yêu cầu đã gửi, không từ tham số của lần gọi hiện tại (A59)

- **Xảy ra:** tổng chi phí của bước chọn rule phụ thuộc vào danh sách task truyền vào lần gọi. Gọi với ít task hơn thì tổng nhỏ đi, dù không hoàn lại đồng nào.
- **Phòng ngừa:**
  - Mọi bộ đếm chi phí đọc từ bản ghi của từng yêu cầu: trajectory, file kết quả chọn rule, hóa đơn.
  - Sau mỗi lần chạy có chi phí: kiểm số mới = số cũ + phần mới.

## L24. Một lập luận chưa đo không được viết như một sự thật (R-24)

- **Xảy ra:**
  - Tôi viết "lần chạy dài dễ gặp lỗi 429 hơn" như một khẳng định. Đo thật thì 2/2 lỗi xảy ra ở lời gọi đầu tiên.
  - Tôi gọi lỗi hạ tầng là "biến cố xen giữa" theo trí nhớ. Câu gốc của ICH E9(R1) xếp nó vào **dữ liệu thiếu**.
  - Lần đo đầu tiên của tôi cho tỉ lệ giải được 11,7%, sai vì log cũ không còn trong thư mục làm việc. Tôi phát hiện vì nó lệch xa con số đã biết (0,47–0,49).
- **Phòng ngừa:**
  - Mỗi lập luận trong tài liệu ghi rõ là **giả thuyết** hay **đã đo**, kèm số và nguồn.
  - Mỗi phép đo mới được so với một con số đã biết trước khi dùng (sanity check, như L20).
  - Mỗi thuật ngữ chuẩn được đối chiếu câu gốc trong `sources-snapshots`.

## L25. Một kết quả đã bị bác bỏ phải được gỡ ở **mọi** nơi nó xuất hiện (A23, rà soát 03/11)

- **Xảy ra:** con số "harmful acceptance 18,5–29,8%" đã bị bác bỏ ở A23, nhưng vẫn nằm trong bảng của TODO.md. Tôi đọc lại bảng đó và nhắc con số với @thuthuy như một phát hiện.
- **Phòng ngừa:**
  - Khi một kết quả bị bác bỏ: `grep` con số ở mọi file (`docs/`, `TODO.md`, `paper/`), gạch đi và dẫn tới mục audit.
  - Khi báo cáo phát hiện: lấy từ file kết quả hiện hành và đối chiếu sổ audit, không lấy từ bảng tóm tắt.

## L26. Không đẩy quyết định sang @thuthuy mà thiếu lý do, ảnh hưởng và lời khuyên (03/11)

- **Xảy ra:** tôi đưa các lựa chọn (nâng ngân sách, nối tiếp ô E1/E2) mà không nói vì sao @thuthuy phải quyết, ảnh hưởng ra sao tới sức mạnh của kết quả, và tôi khuyên gì. @thuthuy thấy đó là đẩy trách nhiệm.
- **Phòng ngừa:** mọi yêu cầu quyết định theo mẫu ba mục trong `CLAUDE.md` ("Khi cần @thuthuy quyết"), kèm số (power, n, chi phí). Việc kỹ thuật thì tự quyết và ghi lý do.

## L27. Thiết kế giai đoạn sau song song với giai đoạn trước; phương án trội thì tự quyết (03/11)

- **Xảy ra:**
  - Nối tiếp e-process từ E1/E2 sang thí nghiệm chính vừa tiết kiệm tiền và thời gian vừa không làm yếu kết quả, nhưng tôi không đề xuất từ đầu, vì đã thiết kế pilot đứng riêng.
  - Khi nhận ra, tôi lại đưa cho @thuthuy quyết dù đó là phương án trội, làm chậm việc phải xong trước khi phân tích E1/E2.
- **Phòng ngừa:**
  - Mục "Quyền quyết định" trong `CLAUDE.md`.
  - Mỗi giai đoạn mới phải trả lời: dữ liệu có dùng lại được ở giai đoạn sau không, cần chốt gì trước.

## L28. Script vận hành không được in kết quả của nhánh skill trước khi phân tích (A66)

- **Xảy ra:** tôi đọc khối `usage` của file kết quả để tính chi phí, và in luôn `solve_rate` của mọi nhánh.
- **Phòng ngừa:**
  - Mọi lệnh đọc file kết quả trước khi phân tích chỉ in chi phí, token, lỗi hạ tầng và trạng thái.
  - Muốn có tỉ lệ nền thì chỉ in của nhánh `none`, và ghi rõ trong log.

## L29. Mọi bước ghi lên một nhánh dùng chung phải chịu được việc có bên khác ghi cùng lúc (A68)

- **Xảy ra:**
  - Sổ ngân sách E2 đã được thiết kế để chịu ghi đồng thời, nhưng nhánh `raw-archive` thì chưa, dù có hai bên cùng ghi (E1 trên máy cục bộ và bước gom kết quả E2).
  - Bước đăng kết quả không được chạy khi bước trước lỗi, nên một lỗi phụ làm mất đầu vào của bước chạy nối tiếp.
- **Phòng ngừa:**
  - Liệt kê **mọi** bên ghi lên mỗi nhánh. Nếu có hơn một bên, dùng ghi kiểu so-và-đổi kèm thử lại, và có test với hai bản sao của repo.
  - Bước tạo đầu vào cho lần chạy sau phải là `if: always()`.
  - Bước chạy nối tiếp phải dừng khi thiếu đầu vào, không được mặc định "chưa có gì".

## L30. Trước khi chép dữ liệu vào một thư mục, kiểm xem có mã nào đang cộng dồn trên thư mục đó (A69)

- **Xảy ra:** tôi chép kết quả E2 vào `results/pilot/`, đúng chỗ bộ chặn ngân sách của E1 đang cộng dồn số đã chi.
- **Phòng ngừa:**
  - Mỗi thí nghiệm có thư mục kết quả riêng.
  - Trước khi thêm file vào một thư mục, `grep` các chỗ đọc thư mục đó (`glob`, `rglob`), rồi chạy lại các phép tính phụ thuộc (ở đây là `pilot_spent_total()`) trước và sau.

## L31. Không tải dữ liệu lớn lên máy đang chạy thí nghiệm có chi phí (A71)

- **Xảy ra:** tôi tải dữ liệu MemGovern và ba bản clone vào scratchpad khi E1 đang chạy. Đĩa của phiên dùng chung với image Docker của E1, nên một lô bị bỏ qua.
- **Phòng ngừa:**
  - Tải và xử lý dữ liệu ngoài trên GitHub Actions (miễn phí, đĩa riêng).
  - Trên máy chạy E1, kiểm `df -h /` trước khi tải. Chỉ tải khi chỗ trống sau khi tải vẫn ≥ dung lượng của lô kế tiếp.

## L32. Mã bọc ngoài một script phải giữ đúng các giả định về tiến trình của script đó (A72)

- **Xảy ra:** driver đo thời gian theo session. Vòng lặp bọc ngoài của tôi chạy mọi lần trong cùng một session, nên đồng hồ không được đặt lại.
- **Phòng ngừa:** trước khi bọc một script, `grep` các chỗ nó đọc trạng thái tiến trình (`getsid`, `/proc`, biến môi trường). Lần chạy lại đầu tiên phải được xem log để chắc nó làm được ít nhất một lô.

## L33. Câu kiểm phải đọc đúng phần dữ liệu do hành vi cần kiểm tạo ra (A73)

- **Xảy ra:** tôi tìm chuỗi đầu ra của công cụ trong cả trajectory, nên khớp nhầm với chính đoạn hướng dẫn trong prompt.
- **Phòng ngừa:**
  - Kiểm đầu ra ở đúng vị trí nó xuất hiện (quan sát sau hành động), kèm một bộ đếm độc lập (log của server theo từng endpoint).
  - Một câu kiểm "đạt" mà hai bằng chứng mâu thuẫn nhau (ở đây: 1 lời gọi server nhưng lại có thẻ được đọc) thì coi là không đạt cho tới khi giải thích được.

## L34. Một tính chất của hệ thống bên ngoài (ở đây là tính tất định) phải được đo trên mẫu đủ lớn trước khi dùng làm giả định của thiết kế (A75)

- **Xảy ra:** tôi kết luận "tất định theo seed" từ 2 lời gọi. Đo lại trên 688 lời gọi: 21,5% không lặp lại được.
- **Phòng ngừa:**
  - Mọi giả định về hành vi của API phải có cỡ mẫu và khoảng tin cậy ghi trong `docs/number_provenance.md`.
  - Thiết kế nào dựa vào giả định đó phải có phép kiểm đăng ký trước, như §5 đã có.

## L35. Mọi script phân tích mới phải dùng đúng hàm endpoint đã đăng ký, không tự viết lại ngưỡng (A76)

- **Xảy ra:** tôi tự viết `loss < 0.5` cho "giải được", trong khi định nghĩa đã đăng ký là loss = 0 (`analyze_g1_final.resolved`).
- **Phòng ngừa:**
  - Import hàm endpoint đã đăng ký; không viết lại.
  - Đề xuất thêm một mục vào preflight: tìm `loss_without < ` / `loss_with < ` trong `scripts/` và báo lỗi.

## L36. Pilot dùng để kiểm phương pháp, không dùng để kiểm giả thuyết khoa học (`docs/pilot_postmortem.md`)

- **Xảy ra:** khoảng 153 USD được chi để hỏi "skill có tác dụng không" bằng các thiết kế xác nhận, trong khi dữ liệu ngày đầu (R14, R15) đã cho thấy hiệu ứng quá nhỏ để đo.
- **Phòng ngừa:**
  1. Pilot trước hết chạy đối chứng dương mạnh, đối chứng âm và A/A, với chi phí vài USD.
  2. Trước mỗi lần nâng ngân sách, trả lời bằng số: "nếu kết quả lại là FAIL, ta học được gì mà chưa biết?" Câu trả lời là "không có gì" thì không nâng.
  3. Một tín hiệu cảnh báo về power hay cỡ hiệu ứng phải dẫn tới **đổi thiết kế**, không dẫn tới chạy lớn hơn.

## L37. Chạy thử miễn phí phải chạy đúng script sẽ chạy thật, cả vòng lặp, không chỉ thành phần bên trong (A78)

- **Xảy ra:** tôi chỉ chạy thử driver một lần, không chạy `run_t4.sh`. Lỗi môi trường của câu kiểm dừng sớm chỉ lộ ra ở lần chạy có chi phí.
- **Phòng ngừa:** chạy thử bằng chính script thật, với model giả lập, cho tới ít nhất một vòng ra quyết định trọn vẹn.
- **Bổ sung (A81):** chạy thử bằng **đúng trình thông dịch** sẽ chạy thật. Script nào cần cả gói của repo lẫn litellm thì tách thành hai bước.

## L38. Trước khi đề xuất một pilot có chi phí, tính cận trên của mức tăng từ dữ liệu sẵn có và xác suất qua cổng (A79)

- **Xảy ra:** tôi đề xuất 2.1 với xác suất thành công ghi là "chưa đo". Nhưng dữ liệu E2 ở mục 1.4 đã đủ để tính rằng mức tăng tối đa khoảng 0,09, thấp hơn cổng 0,15.
- **Phòng ngừa:** mỗi đề xuất có chi phí phải kèm hai thứ.
  1. **Cận trên của δ** tính từ dữ liệu đã có: tỉ lệ các lần chạy thuộc loại thất bại mà can thiệp có thể sửa.
  2. **Xác suất qua cổng** ở cận trên đó, bằng mô phỏng.
  - Nếu cận trên thấp hơn cổng, không đề xuất. Nếu không tính được cận trên, ghi rõ vì sao, và để @thuthuy quyết với thông tin đó.

## L39. Trong plasmode, "giá trị thật" phải là đúng đại lượng mà bộ ước lượng nhắm tới, định nghĩa trên tham số chứ không trên mẫu (A80)

- **Xảy ra:** tôi cấy hiệu ứng quanh trung bình mẫu của 3 lần chạy, rồi so CI với phương sai của chính các hiệu ứng đã cấy. Bộ ước lượng thì nhắm tới phương sai của hiệu số xác suất thật.
- **Phòng ngừa:** trước khi chạy mọi kiểm power hay độ phủ, viết rõ một dòng "đại lượng thật = …" theo tham số của mô hình sinh dữ liệu, và kiểm bằng một test: khi τ = 0, độ phủ phải gần 0,95.

## L40. Chuỗi lệnh "kiểm rồi commit" phải dừng khi kiểm thất bại (A82)

- **Xảy ra:** `preflight; git commit` vẫn commit dù preflight báo FAIL.
- **Phòng ngừa:** luôn viết `python scripts/preflight.py && git commit …`. Không dựa vào hook, vì hook chỉ chạy `--ci`, không có lint.

## L41. Tính power cho một phép tương quan hay phép chuyển giao phải dùng đúng thành phần phương sai, đo từ dữ liệu, không dùng phương sai tổng (A83)

- **Xảy ra:** tôi báo power khoảng 83% cho tương quan giữa tác dụng skill của mình và của SSKB. Tôi dùng phương sai tổng của tác dụng skill, trong khi phần có thể tương quan được chỉ là phần **chung giữa các cấu hình** (hiệp phương sai chéo, 3,34 điểm²), và dùng nhiễu của họ thay cho nhiễu đo được ở phía mình (9,3 điểm cho trung bình 10 yêu cầu).
- **Phòng ngừa:**
  1. Viết rõ r kỳ vọng = cov_chung / sqrt(var_bên_A · var_bên_B), với cov_chung lấy từ dữ liệu lặp **giữa các cấu hình khác nhau**, và var mỗi bên gồm cả nhiễu đo được của **chính phép đo sẽ chạy**.
  2. Mọi con số power phải ra từ một script đã commit, không tính nhẩm trong trao đổi.
  3. Power dưới 0,8 thì câu hỏi đó không được làm kết luận chính; chỉ báo cáo mô tả, kèm power đã nêu trước.

## L42. Lần chạy có phí luôn khởi chạy bằng launcher tự đặt môi trường; mã gọi model phải tự dừng khi thiếu khóa (A84)

- **Xảy ra:** tôi gọi driver trực tiếp từ shell của phiên, mà shell này không có biến Vertex. Lời gọi thất bại với chi phí ghi 0, nên trần và cổng chi phí không nhận ra gì.
- **Phòng ngừa:**
  1. Mọi lần chạy có phí, kể cả `--max-cells 1`, đều đi qua launcher trong scratchpad, vì launcher tự đặt biến.
  2. Mã dựng cấu hình model kiểm `_env` của file cấu hình và dừng trước khi gọi model.

## L43. Lệnh chờ một tiến trình phải chờ theo PID, không theo mẫu chuỗi; kiểm chạy trùng bằng mẫu không tự khớp (A85)

- **Xảy ra:** `pgrep -f "<mẫu>"` khớp cả dòng lệnh của chính shell đang chờ, nên lệnh chờ không bao giờ thấy tiến trình kết thúc như mong đợi. Tôi lại kết luận "lệnh chờ đã mất" khi chưa tìm đúng tiến trình.
- **Phòng ngừa:**
  1. Chờ bằng `while kill -0 <PID>`.
  2. Kiểm trùng bằng mẫu `[x]yz`.
  3. Trước khi tạo lệnh chờ thay thế, tìm tiến trình cũ bằng ID tác vụ nền hoặc file output của nó, không chỉ bằng `ps | grep`.
  4. Driver dùng chung một file kết quả không được chạy song song trên cùng plan.
  5. **Bổ sung (A92m):** nối các bước trong một script thay vì dùng lệnh chờ. Sau mỗi lần dừng, kiểm lại bằng `/proc/<pid>/cmdline` rằng không còn tiến trình nào.
  6. Xóa image phải xóa mọi tên (tag) của nó, nếu không đĩa không được giải phóng.


## L44. Một quy tắc tự đặt không được loại bỏ phép thử mà kế hoạch gốc bắt làm đầu tiên; phải đối chiếu định nghĩa của paper gốc trước mỗi pilot (A86)

- **Xảy ra:**
  - Pilot dùng skill dạng hướng dẫn trong khi paper gốc dùng chương trình sửa code.
  - TODO R15 ghi rõ phải đo skill dạng chương trình sửa code đầu tiên, nhưng phương án đó (P2) bị loại sau G1 bởi một quy tắc chọn do mình đặt.
- **Vì sao lọt qua:** quy tắc chọn phương án chỉ xét những gì tính được n từ nguồn công bố. Nó không hỏi phương án đó có kiểm đúng giả thuyết của paper gốc hay không.
- **Phòng ngừa:**
  1. Trước mỗi pilot, lập bảng so định nghĩa của paper gốc (skill, trial, loss, I(x)) với cái sẽ chạy, kèm câu trích từ bản gốc. Chỗ nào lệch phải ghi lý do và phạm vi kết luận.
  2. Một quy tắc chọn phương án không được loại một phương án mà kế hoạch gốc bắt buộc, khi chưa báo @thuthuy.
  3. Mục kiểm tra mới trong `docs/research_rules.md` §4.

## L45. Đo trên quần thể mà ước lượng được định nghĩa trên đó; xét mọi đường dự phòng của kế hoạch gốc trước khi kết luận "không khả thi" (A87)

- **Xảy ra:**
  - STR của paper gốc định nghĩa trên P_s (task trong scope của skill), nhưng mọi thí nghiệm đo trên issue tự nhiên, nơi skill hầu như không liên quan.
  - Hiệu ứng bị pha loãng, nên mọi kết quả null và mọi phép tính khả thi đều được tính trên một quần thể sai.
- **Vì sao lọt qua:**
  1. Ràng buộc R13 ("chỉ benchmark chuẩn") được hiểu là "chỉ SWE-bench và các bản liên quan", dù bảng 6.1 có SWE-smith.
  2. I(x) bằng regex được coi là đã định nghĩa P_s, dù precision chỉ ≤ 0,34.
  3. Quy tắc chọn phương án chỉ tính n_có trên SWE-bench.
- **Phòng ngừa:**
  1. Mục kiểm tra mới ở `docs/research_rules.md` §4.
  2. Mỗi phép tính khả thi ghi rõ quần thể và tỉ lệ task liên quan đã đo.
  3. Trước khi kết luận "không khả thi", liệt kê các đường dự phòng của to-do gốc và lý do loại từng đường.

## L46. Cảnh báo phải thành cổng chặn; tín hiệu đỏ phải được đọc (A88, `docs/potential_issues.md` §1)

- **Xảy ra:**
  - To-do gốc cảnh báo đúng chỗ sai (pha loãng, SWE-smith, gskill, edit program), nhưng các cảnh báo chỉ là văn bản.
  - Một cảnh báo bị đóng bằng cách viết định nghĩa (W1).
  - Lựa chọn quyết định bị loại vì giá mà không trình @thuthuy (W4).
  - CI đỏ suốt nhiều commit mà không ai đọc (W8).
- **Phòng ngừa:**
  1. Một mục của to-do chỉ được tick khi có **phép đo** chứng minh nó, không phải khi có định nghĩa.
  2. Mọi phương án bị loại vì chi phí mà mạnh hơn phương án được chọn phải trình @thuthuy, kèm ba điều (quyền, ảnh hưởng, lời khuyên).
  3. Đọc CI sau mỗi lần push; test không đọc file ngoài git.

## L47t. Chỉ số đại diện cho một cơ chế phải được kiểm trên đối chứng không có cơ chế đó (A96)

- **Xảy ra:** "bản vá trùng với bản hoàn tác commit bị lộ" được dùng làm cận dưới cho việc agent dùng chỗ lộ. Đối chứng không lộ cho thấy chỉ số này vẫn cao khi không có chỗ lộ.
- **Phòng ngừa:** trước khi dùng một chỉ số làm bằng chứng cho cơ chế, đo nó ở điều kiện không có cơ chế. Ưu tiên thí nghiệm can thiệp (bỏ cơ chế đi) hơn chỉ số đại diện.
- **Ghi chú đánh số:** phiên trên `main` đã dùng L47 và L48. Số này sẽ được đánh lại khi gộp `trial` vào `main`.

## L48t. Hệ thống dựa trên công cụ: kiểm thao tác trên model thật và kiểm vị trí hướng dẫn trong prompt (A102)
- **Nguyên nhân gốc:** các phép kiểm khả thi chỉ chứng minh đường ống chạy được: model giả lập được lập trình để gọi công cụ. Không phép kiểm nào hỏi model thật có gọi công cụ không. Hướng dẫn của bên thứ ba được đặt khác chỗ so với cấu hình gốc của họ (trong mô tả issue thay vì trong workflow của agent), và workflow của harness cạnh tranh với nó.
- **Phòng ngừa:**
  - trước khi chạy cả ô, chạy một lô nhỏ trên model thật và báo **tỉ lệ dùng công cụ**, với một quy tắc dừng chốt trước;
  - đối chiếu vị trí từng đoạn hướng dẫn với prompt gốc của hệ thống (đoạn nào nằm trong phần nào của template);
  - mục kiểm tra mới trong `docs/research_rules.md` §4.

## L49t. Sửa một lỗi phụ thuộc thì sửa ở mọi nơi, và biến nó thành phép kiểm tự động (A97 → A103)
- **Nguyên nhân gốc:** A97 được sửa ở đúng job bị hỏng. Một workflow khác có cùng dòng cài đặt thì không được kiểm, nên lỗi lặp lại ở lần dùng tiếp theo.
- **Phòng ngừa:**
  - khi sửa lỗi thiếu gói, `grep` mọi workflow có cùng phiên bản thư viện;
  - thêm một phép kiểm vào preflight (CLAUDE.md, cơ chế 5), ở đây là `[workflow deps]`.

## L47. Mọi phân tích lại trên dữ liệu đã có phải tái lập đúng số đã đăng ký trước khi tính cái mới (A89m)

- **Xảy ra:** script phân tích lại có một giả định sai về giá trị loss của cặp không có báo cáo. Chỉ phép kiểm "endpoint cũ phải ra đúng số cũ" mới bắt được lỗi này.
- **Phòng ngừa:** mỗi phân tích lại có một bước tái lập bắt buộc: số cũ, cỡ mẫu cũ, số cặp nối được. Chỉ đọc số mới khi bước này khớp tuyệt đối.

## L48. Script gọi harness phải nhận interpreter của từng benchmark làm tham số bắt buộc, và "không có báo cáo" không bao giờ được gộp vào một kết luận (A91m)

- **Xảy ra:** script chấm lại dùng interpreter mặc định, mà môi trường đó không có `swebench`. Hàm gán nhãn lại coi "không chấm được" là "hỏng".
- **Phòng ngừa:**
  1. Interpreter của harness là tham số bắt buộc, theo từng benchmark.
  2. Nhãn kết luận chỉ được gán khi mọi lần chấm có báo cáo; còn lại ghi `no_report`.
  3. Chạy thử script trên **mỗi loại** dataset trước khi chạy hàng loạt.

## L49. Mô tả dataset, cỡ mẫu và thiết lập trong paper phải đọc từ file cấu hình của thí nghiệm, không từ trí nhớ hay từ thí nghiệm gần nhất (A111m)

- **Xảy ra:** paper ghi E1 dùng SWE-bench Verified vì pilot G1 và nhiều script chấm lại gọi chung là "Verified". Thật ra E1 dùng bộ test đầy đủ. Cùng lúc, bản nháp ghi E1 có 40 task mỗi skill, trong khi giai đoạn mở rộng đã nâng lên 53.
- **Phòng ngừa:**
  1. Mỗi câu mô tả thiết lập (dataset, n, seed, ngân sách) trong paper phải dẫn được tới một file: `configs/pools/*.json` hoặc bản đăng ký trước, kể cả các ghi chú thực thi.
  2. Ưu tiên macro sinh từ file (như `paper/numbers.tex`) cho mọi con số thiết lập.
  3. Comment trong mã không được gọi tên dataset chung chung khi nhiều thí nghiệm dùng các dataset khác nhau.

## L50. Sau mỗi push phải đọc kết luận CI; test không được phụ thuộc vào `runs/` hay `logs/` (A112m)

- **Xảy ra:** một test đọc file trong `runs/`. Ở máy làm việc file có sẵn nên preflight qua; trên runner file không có nên CI đỏ suốt 28 giờ. Tôi chỉ chạy preflight cục bộ mà không đọc kết luận CI.
- **Phòng ngừa:**
  1. Sau mỗi push lên `main`, đọc kết luận của workflow CI. CI đỏ thì sửa trước mọi việc khác.
  2. Test cần dữ liệu thật thì dùng bản cố định nhỏ trong `tests/fixtures/`, kèm phép kiểm "bản cố định trùng bản gốc" khi có bản gốc; hoặc dùng `skipif` có lý do rõ khi dữ liệu không thể cố định.
  3. Trước khi commit một test mới, chạy nó một lần khi đã tạm cất `runs/`.

## L51. Văn bản sinh tự động từ trang web phải được đọc lại bằng mắt ít nhất một lần, và quy tắc trích phải có phép kiểm âm (A113m)

- **Xảy ra:** `make_bib.py` cắt tiêu đề từ phần đầu trang bằng một mẫu chuỗi; mẫu đúng cho vài trang, sai cho trang HTML của arXiv. Phép kiểm "không còn VERIFY" qua, nên tôi coi bib là xong mà không đọc các tiêu đề.
- **Phòng ngừa:**
  1. Ưu tiên metadata có cấu trúc đã kiểm (arXiv API) hơn văn bản cắt từ trang.
  2. Script trích văn bản phải dừng khi gặp chữ của giao diện trang.
  3. Sau mỗi lần sinh bib, đọc toàn bộ các tiêu đề đã đổi (`diff`).
  4. **Bổ sung:** `preflight.py --ci` bỏ lint và test (CI chạy chúng thành bước riêng), nên trước commit phải chạy `python scripts/preflight.py` **đầy đủ**. Commit `45e10d1` chỉ qua `--ci` và làm CI đỏ vì một dòng dài 116 ký tự; đã sửa ở commit sau.
  5. **Tái phạm L40 (07/11):** lệnh `python scripts/preflight.py 2>&1 | tail -2 && git commit` commit và push dù preflight FAIL, vì mã thoát của ống là của `tail`. Commit `effa2de` lên `main` với lỗi sắp xếp import. Từ đây: preflight ghi ra file, lấy `rc=$?`, chỉ commit khi `rc = 0`; không bao giờ đặt preflight trước dấu `|`.
  6. **Phòng ngừa bằng máy:** git hook `pre-commit` (`scripts/git-hooks/pre-commit`) chạy preflight **đầy đủ**, kể cả ruff và pytest, nên lỗi lint chặn được commit dù lệnh gọi có bị ống làm mất mã thoát.

## L52. Câu chữ đã duyệt cho paper phải được kiểm lại khi có dữ liệu mới, và mọi câu "không bao giờ / mọi / không đổi" phải có một phép đếm sinh từ file (A121)

- **Xảy ra:** câu "trần chi phí không bao giờ chặn" được viết khi mới có 500 lượt chạy. Sau đó thêm 634 lượt, trong đó 1 lượt chạm trần, nhưng câu không được kiểm lại. Một câu khác viết "unchanged" cho hai số 15 và 14.
- **Phòng ngừa:**
  1. Mỗi câu tuyệt đối trong paper ("never", "every", "unchanged", "all") phải đi kèm một macro đếm sinh từ file kết quả, và một giá trị kiểm trong CHECKS của `make_numbers.py`.
  2. Khi thêm file kết quả mới, chạy lại các phép đếm của `docs/reviewer_fidelity.md`.
  3. Phiên bản phần mềm ghi trong paper phải đọc từ workflow đã chạy, theo từng loại thí nghiệm.
