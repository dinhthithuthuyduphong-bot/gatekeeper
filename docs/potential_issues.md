# Rà soát mọi vấn đề tiềm ẩn, lần 2 (06/11/2026)

**Yêu cầu của @thuthuy:** "tại sao to do gốc đã cảnh báo nhưng vẫn xảy ra sai lầm? hãy rà soát tất cả potential issue lần nữa".

**Mức độ** (`docs/method_check.md` §3):
- **K1** làm sai một con số hoặc kết luận;
- **K2** làm giảm power hoặc thu hẹp phạm vi kết luận;
- **K3** chỉ ảnh hưởng tài liệu hoặc truy vết.

## 1. Vì sao to-do gốc đã cảnh báo mà sai lầm vẫn xảy ra

| # | Cơ chế | Bằng chứng trong repo |
| --- | --- | --- |
| W1 | **Cảnh báo bị "đóng" bằng một định nghĩa, không bằng một phép đo.** Mục "P_s = phân phối task mà I(x) đúng" được tick ✅ khi định nghĩa được viết vào `docs/theory/corrections.md`, trong khi I(x) cài thật có precision ≤ 0,34 | TODO Phase 1 (dòng tick ✅); R16 trong TODO §0.3 |
| W2 | **Lấy δ trên một quần thể, tính n trên quần thể khác.** δ = 0,109 lấy từ SWE-Skills-Bench (task viết riêng cho từng skill), rồi dùng để tính n trên issue tự nhiên. Không nhân với tỉ lệ task liên quan | `docs/g1_verdict.md` §2; `docs/preregistration_e1.md` §2 |
| W3 | **Quy tắc chọn phương án chỉ xét những gì tính được n từ nguồn công bố, trên SWE-bench.** P2 (skill dạng chương trình sửa code) bị loại vì "không có phân phối hiệu ứng đã công bố". Quần thể SWE-smith không được xét, dù bảng 6.1 cho phép | `docs/g1_verdict.md` §2, mục 1 |
| W4 | **Lựa chọn quyết định bị loại chỉ vì giá, mà không trình @thuthuy.** gskill làm nguồn skill bị loại vì "≈ 38 USD mỗi repo" (D-M1). Đây là đánh đổi "mạnh hơn nhưng đắt hơn", tức quyền của @thuthuy (mục 4), nhưng chỉ được ghi thành một sai lệch. Trong khi đó, G1, E1 và E2 tốn khoảng 153 USD (`docs/pilot_postmortem.md`), đều trên quần thể bị pha loãng | `docs/preregistration_main_draft.md` §11b; `docs/preregistration_main.md` D-M1 |
| W5 | **Leo thang trên cùng một quần thể sau mỗi lần thất bại.** E1: 65 → 75 → 91 USD; rồi E2 45 USD; rồi các phép thử SSKB. Mỗi bước sửa thiết kế bên trong thí nghiệm, không quay lại hỏi quần thể có đúng không | `docs/pilot_postmortem.md` dòng 2–3 |
| W6 | **Kiểm tra tự động chỉ phủ hình thức.** Preflight và §4 kiểm nguồn, số, mặc định, khóa bí mật, thuật ngữ. Không mục nào hỏi "thiết kế có đo đúng ước lượng của paper gốc không". Mục này mới được thêm hôm nay (L44, L45) | `docs/research_rules.md` §4 trước 06/11 |
| W7 | **Đọc R13 hẹp hơn văn bản.** "Chỉ benchmark chuẩn" được hiểu là SWE-bench và các bản liên quan; SWE-smith (bảng 6.1) bị bỏ sót | TODO §6.1 so với các bản đăng ký G1, E1, E2 |
| W8 | **Tín hiệu đỏ không được xem.** CI trên `main` đỏ từ commit `adb8426` (02:05 UTC, 06/11) tới hết phiên trước, vì một test đọc file trong `runs/`. CLAUDE.md ghi "CI chạy preflight ở mọi lần push", nhưng không ai đọc kết quả | CI run 42155225411 (A88) |

**Điểm chung:** từng thí nghiệm đều chặt chẽ **bên trong** (đăng ký trước, power, A/A, Holm). Nhưng không có bước nào đối chiếu thí nghiệm với **ước lượng và quần thể của paper gốc**. Cảnh báo của to-do gốc là văn bản, không phải cổng chặn.

**Biện pháp:**
- L44 và L45, kèm hai mục kiểm tra mới ở §4.
- Từ nay, mọi đề xuất có đánh đổi giá và độ mạnh đều trình @thuthuy (W4).
- Sau mỗi lần push, đọc trạng thái CI (W8; A88, L46).

## 2. Danh sách vấn đề tiềm ẩn

### 2a. Ước lượng và quần thể

| # | Vấn đề | Mức | Tình trạng |
| --- | --- | --- | --- |
| P1 | Quần thể đo không phải P_s (A87) | K2 cho kết quả cũ (chúng vẫn đúng cho quần thể đó); K1 nếu kết quả cũ được viết thành kết luận về paper gốc | Đã ghi. **Cần sửa câu chữ trong paper:** mọi câu kiểu "skill không có tác dụng" phải kèm quần thể |
| P2 | Quần thể khớp scope **chưa đủ**: SWE-Skills-Bench đo trên task viết riêng cho từng skill mà 92/98 skill vẫn không hiệu quả. Tác dụng lớn chỉ thấy ở skill **được tối ưu trên chính quần thể đó** (gskill: GEPA tối ưu theo kết quả trên task SWE-smith của repo) | K2 | **Mới, chưa ghi ở `docs/root_cause.md` bản đầu.** Hệ quả: nguyên nhân gốc đầy đủ là "quần thể sai **và** skill không được học trên quần thể đó". Đã bổ sung vào `docs/root_cause.md` §4 |
| P3 | Mức tăng của gskill có thể là **đặc điểm của SWE-smith**: lỗi tổng hợp làm hỏng test có sẵn trong repo, nên skill "chạy test sớm, test là bug report" (trích từ skill học được) có đòn bẩy lớn. Trên SWE-bench thì test FAIL_TO_PASS bị giấu | K2 (giới hạn khái quát hóa) | Chưa kiểm. **Chính là câu hỏi "phụ thuộc scope"** của thiết kế sửa: đo cùng skill trên task tự nhiên của cùng repo (pandas 737, MONAI 374) |
| P4 | gskill chọn skill tốt nhất trên tập val 50 task: có lời nguyền người thắng ở bước chọn | K2 | Kiểm được: chỉ đánh giá trên tập test giữ lại, không dùng val |

### 2b. Skill và agent

| # | Vấn đề | Mức | Tình trạng |
| --- | --- | --- | --- |
| P5 | Skill của G1/E1 viết tay dạng hướng dẫn, không phải chương trình sửa code học từ trajectory (A86) | K2 | Đã ghi; §24 cho thấy chương trình sửa code cũng không khả thi trên SWE-bench |
| P6 | Model yếu: Flash-Lite có tỉ lệ giải nền 0,27 và không làm theo chỉ dẫn (§20 S5). gskill dùng gpt-5-mini; Pro chạm trần trên SSKB (§23a) | K2 | Còn mở. Thiết kế sửa cần đo thử trên 1 repo với Flash-Lite và Flash trước khi chọn |
| P7 | Không có model khác hãng: mọi kết quả đều là Gemini | K2 | Chờ thông tin khóa (mục 2.3) |
| P8 | Cách nạp skill khác bài gốc (SSKB: Claude Code CLI và lệnh `/skill`; ta chèn vào prompt) | K2 | Đã nêu ở R3 của `docs/plan_replication.md`. gskill nạp vào system prompt của mini-swe-agent, **trùng** với harness của ta |

### 2c. Endpoint và chấm điểm

| # | Vấn đề | Mức | Tình trạng |
| --- | --- | --- | --- |
| P9 | Test PASS_TO_PASS chập chờn: ở T4, conan-15705 nộp bản giống hệt bản gốc mà vẫn bị chấm không giải được; 4/7 ca có loss trong (0; 0,01) | K1 tiềm năng cho số tuyệt đối; K2 cho hiệu số ghép cặp | Chưa kiểm (miễn phí): chấm lại bản vá gốc nhiều lần; tính lại chỉ với FAIL_TO_PASS |
| P10 | "Resolved" bỏ sót lỗi hành vi: p6 đo 7,8–11,1% patch qua test vẫn khác bản fix trên đầu vào hợp lệ | K2 | Chỉ dùng ở threats to validity. Phải đọc công trình liên quan trước (R1) |
| P11 | SWE-smith cần harness riêng (`swesmith`), và không phải task nào cũng có problem statement | K1 nếu chấm sai | Chưa kiểm. Phải viết adapter, chạy `test_command` trên repo chưa sửa để kiểm cách đọc điểm (như R1 của plan_replication) |

### 2d. Thống kê

| # | Vấn đề | Mức | Tình trạng |
| --- | --- | --- | --- |
| P12 | Phép kiểm XRepoSkill (§10) và phân tích con trên ô trung tính (§13) là phân tích thêm sau khi có dữ liệu | K2 | Đã ghi rõ; paper phải ghi "thăm dò" |
| P13 | Ngưỡng nhiễu F(n) đo trên một model với tỉ lệ nền 0,27, nên có lợi cho các tuyên bố được đối chiếu | K2 (thận trọng, đúng hướng) | Đã ghi |
| P14 | Kiểm độ không đồng nhất (H18-1) không có power | K2 | Đã ghi; không dùng làm bằng chứng |
| P15 | §22 và §23 có n rất nhỏ (10 batch; §23a k = 4) | K2 | Chỉ báo cáo mô tả |

### 2e. Dữ liệu, tái lập, quy trình

| # | Vấn đề | Mức | Tình trạng |
| --- | --- | --- | --- |
| P16 | **CI đỏ trên `main`** vì `test_model_config_flash_lite_equals_section22_setting` đọc `runs/…/litellm_registry.json`, mà file này không có trong git (A88) | K3 | **Đã sửa:** test đọc `tests/fixtures/e1_litellm_registry.json`, chép từ nhánh `raw-archive`. Toàn bộ pytest qua |
| P17 | §23b dừng dở: mới có 3 dòng (0,777 USD), driver không còn chạy trong container này | K3 | Phải ghi là "bỏ dở, không phân tích" (L12), hoặc chạy tiếp theo đúng plan nếu @thuthuy muốn |
| P18 | `TODO.md`: nhật ký dừng ở 03/11, các mục "Ưu tiên 1" chưa được cập nhật | K3 | Còn mở |
| P19 | Nguồn chưa xác minh: `steegen_2016`, `gemini_31_flash_lite_cutoff` (N3: không phân tích nhiễm dữ liệu được) | K2 | Còn mở |
| P20 | Các commit hôm nay (A86, A87, §24, census) chỉ nằm trên `trial`, chưa lên `main` | K3 | Theo chỉ dẫn của @thuthuy: phiên này làm trên `trial` |
| P21 | Lịch sử git cũ hơn 06/11 00:37 không còn trong repo (commit gốc là `4f6be6e`) | K3 | Ghi nhận; tái lập dựa vào `raw-archive` và `sources-snapshots` |
| P22 | CI chỉ chạy trên `main` và `claude/**`, **không** chạy trên `trial`, là nhánh @thuthuy chỉ định cho phiên này. Các commit `0c6d27b`, `353b6a4`, `913eb7c` chưa được CI kiểm | K3 | **Đã sửa:** thêm `trial` vào `ci.yml`; đọc kết quả CI sau lần push này |

## 3. Hệ quả cho hướng sửa

- **P2 và P3 làm rõ thiết kế sửa phải đo gì:**
  - (a) skill học trên quần thể của scope có tác dụng không: chứng nhận trên tập test SWE-smith giữ lại;
  - (b) tác dụng đó có theo skill sang quần thể khác không: task tự nhiên của cùng repo, và task SWE-smith của repo khác.
- Nếu (a) đạt mà (b) không đạt, đó đúng là luận điểm "should this skill run here?" của paper gốc, đo trên skill thật.
- **Rủi ro lớn nhất:** P6 (model yếu). Phải đo thử trên 1 repo trước khi chi nhiều.

## 4. Rà soát lần 3 (07/11/2026): vấn đề sửa được dưới 5 USD

Phạm vi: model khác hãng tạm dừng, chờ thầy duyệt đề tài (@thuthuy 07/11). Bleve 4c và 4d đã có ngân sách riêng (tối đa 7,5 USD), không tính vào đây. Chi phí ước tính lấy từ số đo của chính các nhánh jinja: 1,44 USD (F1), 1,94 USD (chấm skill), 1,46 và 1,87 USD (hai nhánh không rò rỉ), mỗi nhánh 100 task.

### 4a. Có chi phí (chọn trong 5 USD)

| # | Vấn đề | Ảnh hưởng tới luận điểm | Cách sửa | Chi phí |
| --- | --- | --- | --- | --- |
| P23 | **Quỹ đạo của §25 đã mất (A104).** Luận điểm "skill khai thác commit 'Bug Patch'" mới dựa trên Δ_leak = +0,17 và văn bản của skill, chưa có bằng chứng từ hành vi agent | Reviewer: "các tác giả không chứng minh agent đọc lịch sử git" | Chạy lại nhánh chấm skill jinja (seed 41, cấu hình y hệt, lần này có lưu quỹ đạo). Đo: số lượt chạy dùng `git log` / `git show` / đọc "Bug Patch", và tỉ lệ giải có điều kiện theo việc đó. Đồng thời đo **độ lặp lại** so với lần đầu (seed tất định 107/109 ở §5) | khoảng 1,9 USD |
| P24 | **Chưa tách được phần nào của skill gây ra Δ_leak.** Skill có nhiều chỉ dẫn; chỉ một chỉ dẫn nói về lịch sử git | Reviewer: "+0,17 có thể do phần khác của skill tương tác với rò rỉ" | Thí nghiệm bỏ một phần (ablation): bỏ đúng đoạn "Check Git History… 'Bug Patch'", giữ nguyên phần còn lại, chạy trên thiết lập có rò rỉ. Nếu mức tăng tụt về gần mức không rò rỉ (+0,21), phần chênh do chỉ dẫn đó. Đăng ký trước là phân tích **thăm dò** | khoảng 1,9 USD |
| P25 | **Chưa có A/A trên harness gskill.** Không biết hai lượt chạy không skill khác seed lệch nhau bao nhiêu task | Yếu; phép kiểm đổi dấu trên cặp lệch vẫn hợp lệ, A/A chỉ là kiểm chứng phụ | Chạy lại nhánh không skill jinja với seed 42 | khoảng 1,4 USD |

**Đề xuất:** P23 + P24 ≈ 3,8 USD. Thêm P25 thành khoảng 5,2 USD, vượt 5 USD, nên để sau.

### 4b. Miễn phí

| # | Vấn đề | Cách sửa |
| --- | --- | --- |
| P26 | **Bộ chấm SWE-smith có thể chập chờn** (P9: ở T4 có bản sửa giống hệt bản gốc vẫn bị chấm trượt). Các con số S 53/15/35/14 chưa được chấm lại lần nào | Chấm lại mọi patch đã có (4 nhánh jinja và Bleve) thêm 2 lần, chỉ cần Docker, không gọi model; báo tỉ lệ đổi kết quả |
| P27 | Kết quả Bleve chưa phân tích | Khi 4c/4d xong: A/B/C, LF1/LF2, Δ_leak, Gatekeeper, nhóm có hoặc không có mô tả issue, như jinja |
| P19 | Nguồn chưa xác minh: `steegen_2016`, `gemini_31_flash_lite_cutoff` | Tìm và chụp bản gốc, hoặc bỏ câu dùng chúng |
| P17 | §23b dừng dở | Ghi "bỏ dở, không phân tích" (L12) |
| P18 | `TODO.md` dừng ở 03/11 | Cập nhật |
| P20 | `trial` chưa nhập vào `main`; số A/L/R trùng (A89, A91, L47, R-45, R-46) | Đánh số lại khi nhập; đối chiếu T4 (0,55 so với 0,60) |

### 4c. Kết quả các việc miễn phí (07/11/2026)
- **P19:**
  - `steegen_2016`: **đã xác minh** từ bản sao bài báo lưu ở errorstatistics.com, vì trang của nhà xuất bản trả 403.
  - `gemini_31_flash_lite_cutoff`: **vẫn chưa xác minh**. Trang model trên ai.google.dev không có chữ "2025". Trang Vertex không ghi mốc cắt. URL hướng dẫn Gemini 3, nơi kết quả tìm kiếm trích câu "Gemini 3 models have a knowledge cutoff of January 2025", nay đã chuyển sang một trang khác. **Hệ quả:** paper không được viết "không nhiễm dữ liệu", cũng không dùng mốc 01/2025, cho tới khi có bản chụp chứa đúng câu.
- **P17, P18, P20:** đã làm. Chi tiết ở §23b của bản đăng ký trước, `TODO.md` và `docs/merge_plan_trial.md` (chưa nhập vào `main`).
- **P26: xong.** 224 patch không rỗng của 4 nhánh jinja, mỗi patch chấm lại 2 lần bằng bộ chấm SWE-smith (448 lần; `results/rescore_jinja.jsonl`, `results/rescore_jinja_summary.json`).
  - **0 task đổi kết quả** ở mọi nhánh. 0 lỗi hạ tầng (sau khi bỏ 39 lần chấm hỏng do Docker chưa bật, A105).
  - Bốn nhánh: không skill (38 patch, S 15), có skill (79, S 53), không rò rỉ không skill (41, S 14), không rò rỉ có skill (66, S 35).
  - **Kết luận:** các con số S chính không bị ảnh hưởng bởi bộ chấm chập chờn (P9 không xảy ra trên dữ liệu này).
- Placebo C2 của §27a: đã có nguyên văn định nghĩa trong bản chụp.

