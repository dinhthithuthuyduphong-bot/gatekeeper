# Sổ review trước khi thực thi (quy tắc R3, `docs/research_rules.md`)

Mỗi mục: ngày, phạm vi (file hoặc commit), các mục §4 đã kiểm, phát hiện và xử lý. Mã chưa có mục ở đây thì chưa được chạy trên dữ liệu thật hoặc với chi phí thật.

## 03/11/2026, R-1: các bản sửa A24–A35 (commit `9e429f6`, `12f449a`)

Phạm vi: `scripts/run_pilot.py`, `run_batched_pilot.py`, `validate_pool.py`, `export_instances.py`, `analyze_g1_final.py`, `rq1_mini.py`, `xreposkill_select.py`, `missing_tasks.py`, `backfill_exit_status.py`, `src/gatekeeper/harness.py`, `pilot.py`. Đọc toàn bộ diff `e11c9c2^..HEAD`.

| Mục §4 | Kết quả |
| --- | --- |
| Trùng bản đăng ký trước | Seed thứ tự RQ1 nay là `"2027-order"` (A25). Lệnh phân tích E1/E2 đã ghi vào ghi chú thực thi, họ Holm của E1 = 3 skill |
| Cùng dữ liệu cho mọi quy tắc | `decide` cắt 40 trial trước mọi quy tắc (A26) |
| Phân tích cam kết có dữ liệu | `exit_status` được lưu và gộp. **Phát hiện F1:** phân tích *hypothetical* tôi viết bỏ cả task nếu một seed bị cắt, trong khi bản đăng ký trước nói "bỏ các cặp". Đã sửa: bỏ theo cặp, lấy trung bình trên các seed còn lại (`test_hypothetical_drops_pairs_not_tasks`) |
| Endpoint, trường hợp biên | Danh sách F2P rỗng: F = 0 chỉ khi có `tests_status`. Đã đọc mã harness (5.0.2 và bản fork): patch không áp được thì report không có `tests_status`, nên F = 1. Test chạy hỏng (lỗi cú pháp) thì các test F2P vắng mặt bị tính là failure, không phải danh sách rỗng, nên không bị ảnh hưởng |
| Harness đúng bản | Live: bản fork `ad79b85`, `--namespace starryzhang` (README đã lưu ở `sources-snapshots`, id `swebench_live_python_only`) |
| Trạng thái kết thúc | Liệt kê từ `minisweagent/agents/default.py` và `exceptions.py` 2.4.6. Cách phân loại dựa trên ICH E9(R1) (trích ở `docs/lessons_learned.md` L1) |
| Không ghi đè, không lỗi âm thầm | `--out` bắt buộc với E1/E2. Export bỏ qua file không phải pool. Lỗi khi chọn rule thì chạy lại hoặc dừng |
| Ghim phiên bản | XRepoSkill `26fd703`, bản fork Live `ad79b85`, revision dataset ghi vào `data/instances/revisions.json` |
| Ngân sách | Trần E2 tính từ số đã chi. E2 chỉ chạy khi E1 xong |
| Tương thích ngược với E1 đang chạy | `harness_kw` có giá trị mặc định None, nên E1 vẫn chạy như trước (đã kiểm lần chạy lại sau sửa) |
| Kiểm thử | ruff, ruff format, pytest đều qua |

## 03/11/2026, R-2: `xreposkill_select.py` (trước lần chạy đầu)

- Mã gốc được đọc toàn bộ: `retrieval.py`, `llm.py`, `config.py`, đoạn `SKILL_FRAME` của `rollout.py`. Mã chỉ gọi LiteLLM, không chạy lệnh shell, không ghi ra ngoài `out_dir`.
- Nội dung rule không vào repo: chỉ ghi mã rule, số chiến lược và số token. Lý do do LLM viết cho mỗi lựa chọn không được lưu.
- **X-a / X-b:** khi trả lời của model không đọc được thành JSON, hoặc nội dung rỗng vì hết token, mã gốc trả về danh sách rỗng mà không báo lỗi. Giữ nguyên để tái hiện trung thực hành vi của hệ thống gốc. Tỉ lệ "không chọn rule nào" được báo cáo. Nếu tỉ lệ lớn thì dừng và báo @thuthuy (không tự đặt ngưỡng, R2).
- `SKILL_FRAME.format(block=…)`: dấu ngoặc nhọn trong nội dung rule không bị diễn giải, vì chỉ chuỗi mẫu mới được diễn giải.

## 03/11/2026, R-3: `make_e2_selection.py` (trước lần chạy đầu)

- Phát hiện một biểu thức kiểm tra viết rối (`extra`). Kết quả vẫn đúng nhưng khó đọc, nên đã viết gọn lại.
- Có test cho thứ tự ngẫu nhiên, cho việc chỉ lấy task dùng được và được kích hoạt, và cho cả ba điều kiện dừng (`tests/test_e2_selection.py`).

## 03/11/2026, R-4: `run_e2.sh` (scratchpad, trước lần chạy đầu)

- Seed chạy xen kẽ theo từng lô (`--max-batches 1` cho mỗi seed): khi chạm trần, mọi task đã chạy đều có đủ 3 seed.
- Trần = số đã chi ngoài các file `g2-e2-*` + 45. Giá trị này không đổi qua các lần chạy lại.
- Dừng nếu seed 61 của E1 còn thiếu task.
- Còn thiếu (chặn chạy): (1) `e2_rows.jsonl` chưa có, vì đang chờ bản xuất; (2) chưa chạy thử miễn phí trên image Live (§4, mục cuối).

## 03/11/2026, R-5: chạy thử miễn phí trên SWE-bench-Live, và các bản sửa A36/A37

- **Chạy thử** (`results/pilot/e2-dryrun.json`, mô hình giả lập, 0 USD): conan-18655 và trimesh-2126. Bước này lộ ra A36: image Live có file chưa theo dõi. Kiểm tiếp thì lộ ra A37.
- **A37, đối chiếu nguồn:** bài SWE-bench, Table 5 (bản đã lưu, id `swebench`: "% Resolved … % Apply"). Mã harness 5.0.2: `run_evaluation.py` ghi `APPLY_PATCH_FAIL`; `reporting.py` đưa task vào `error_ids`, không vào `resolved_ids`.
- **Tương thích với E1 đang chạy:** các lô E1 đã có 0 ca lỗi hạ tầng, nên việc đổi cách phân loại từ lô kế tiếp không làm dữ liệu cũ và mới lệch nhau.
- **Một chỗ lệch tưởng là lỗi, hóa ra không phải:** p của đối chứng dương B3 tính lại theo nhánh `none` là 0,035, khác 0,0105 đã báo cáo. Nguyên nhân: quy tắc v2 so oracle với **đối chứng nhiễu** (`analysis.py`, `positive_z = loss(positive control) − loss(noise control)`). Tính lại theo định nghĩa đó cho ra 0,0107, khớp. Đã thêm ghi chú về nhánh nền vào `docs/review_thresholds.md`.
- Kiểm thử: ruff và pytest đều qua. `test_patch_apply_failure_is_detected_and_scored_unresolved`, `test_dry_run_records_preexisting_untracked_files_only`.

## 03/11/2026, R-6: `verify_methods.py` (kiểm định phương pháp bằng số)

- **Lỗi của chính tôi, bị bắt khi chạy lần đầu:** so sánh mảng (n, s) với q có dạng (n,). Khi s = 1, numpy không báo lỗi mà âm thầm tạo ma trận n × n, nên bước kiểm plasmode lẽ ra cho số sai. Đã sửa (`q[:, None]`) và thêm `assert z.shape == (n, seeds)`.
- **Bài học, bổ sung vào danh sách review §4:** mọi phép toán mảng trong mô phỏng phải assert kích thước kết quả.
- Đầu vào chỉ lấy từ G1 (đã đóng). Không đọc kết quả E1.

## 03/11/2026, R-7: kết quả chạy thử Live sau khi sửa A36/A37 (`results/pilot/e2-dryrun2.json`, 0 USD)

- conan-18655, trimesh-2126. Nhánh oracle (patch gold): loss 0, tức resolved. Nhánh `none`: loss 0,667 (F = 1, R = 0). Z = −0,667, đúng kỳ vọng.
- 0 lỗi hạ tầng, 0 chỗ lệch giữa endpoint và cờ `resolved`, 0 bản vá không áp được. Trạng thái kết thúc của cả 4 lần chạy là `Submitted`.
- Bản fork harness của Live (`--namespace starryzhang`), image `starryzhang/...` và đường dẫn report đều chạy đúng với pipeline.

## 03/11/2026, R-8: quy tắc kết luận theo ICH E9(R1) (A39)

- Đọc bản gốc ICH E9(R1) (id `ich_e9_r1`): "To explore the robustness of inferences from the main estimator … a sensitivity analysis should be conducted".
- Mô phỏng 3 quy tắc trên thiết kế E1 trước khi sửa (`docs/method_check.md` §5).
- Quy tắc đã đăng ký vẫn được tính. Test mới: một repo, 30 task giúp → kết luận chính "có ích", S2 không đạt (p nhỏ nhất 0,5), quy tắc đã đăng ký ra "INCONCLUSIVE".
- Không đụng dữ liệu E1.
- Đã gỡ một URL OSF tôi tự đoán cho Steegen (vi phạm R1) trước khi commit.

## 03/11/2026, R-9: mở rộng E1 lên n = 53 (trước khi chạy)

- **Thiết kế:** review phát hiện A40 (chồng lấn 5 task với giai đoạn gốc), nên chuyển sang giai đoạn riêng và thêm script gộp có kiểm trùng.
- **Dữ liệu:** 39/39 task mở rộng có trong `e1_rows.jsonl` và thỏa I(x) của skill tương ứng. 40 task đầu của từng skill trùng tập đang chạy (`make_e1_extension.py` tự kiểm). Mẫu tên file các lô không trùng giữa hai giai đoạn.
- **Ngân sách:** trần 111,26. E2 tính trần từ số đã chi thực tế, nên phần mở rộng tự động được trừ.
- **Tài nguyên:** script E2 đợi cả `g1-e1x-s61` xong (hai giai đoạn đều xóa image Docker sau mỗi lô).
- **Phân tích:** `_truncated` đọc trạng thái theo cặp với dữ liệu gộp. `no_skill_unresolved` ưu tiên lần xuất hiện đầu tiên. Có test.
- **Lỗi của tôi bị bắt:** (1) các test tôi thêm import `analyze_g1_final` chỉ chạy được nhờ test khác đã sửa `sys.path`, nên đã chuyển sang biến nạp sẵn ở đầu file; (2) một test của tôi kỳ vọng sai giá trị.
- `bash -n` cho cả hai script chạy. ruff và pytest đều qua.

## 03/11/2026, R-10: rà soát mọi chuẩn, ngưỡng và ký hiệu

- **Cách làm:** trích mọi hằng số trong mã đang chạy (grep), rồi đối chiếu từng mục với `docs/number_provenance.md`. Kiểm mọi nguồn trong `sources-snapshots` có chứa đúng câu được trích không.
- **Đã đối chiếu thêm từ bản gốc:**
  - prior, c và aGRAPA (Waudby-Smith & Ramdas);
  - công thức sai số Monte Carlo (Morris et al.);
  - quy tắc kết luận (ICH E9(R1)).
- **Sửa:** A41 (α một phía), A42 (mặc định tự đặt), A43 (ký hiệu). Mọi con số bị ảnh hưởng đã được **tính lại**: bảng thiết kế plasmode, kiểm định phương pháp, C10.
- **Còn chờ bản gốc:** quy ước power 80% (qua Lakens 2022), McHugh 2012, Steegen 2016, mốc cắt dữ liệu của Gemini. Không mục nào trong số này được dùng cho một kết luận.
- Kiểm thử: test được sửa cho cách chia α tường minh và cho θ = 0 hợp lệ. ruff và pytest đều qua.

## 03/11/2026, R-11: đưa quy trình vào file tự nạp và kiểm tra tự động

- **`CLAUDE.md`** (tự nạp ở mọi phiên) và **`scripts/preflight.py`** (chạy trong CI ở mỗi lần push).
- **Lần chạy đầu tiên của preflight bắt được:** 3 θ mặc định và 1 θ = 1e-9 mà lượt rà tay bỏ sót (A46); nguồn bị ghi đè (A44).
- **Nguồn Wikipedia được thay** (A45).
- **Kết quả đã kiểm không đổi:** `simulation.json` tái lập giống hệt (chỉ khác dấu thời gian); bảng thiết kế với θ = 0 giống hệt bản cũ.
- **Dữ liệu gốc không sửa:** các lô E1 p07–p13 (trước A42) giữ nguyên trường cũ; preflight chỉ kiểm file có `format_version` ≥ 2.

## 03/11/2026, R-12: bước kiểm khóa bí mật (A47)

- Toàn bộ cây ở `4bf5e3d` đã được kiểm bằng `git grep` với dấu hiệu PEM và `private_key`: **không có khóa**. Không file nào có tên chứa key, secret hay cred được theo dõi.
- Thử bằng khóa giả được stage (`zz_fake_key_test.txt`): preflight [secrets] báo FAIL và trả mã thoát 1. File giả đã được gỡ khỏi stage và xóa.
- Từ nay mỗi commit chạy `python scripts/preflight.py --ci && git commit …`.

## 03/11/2026, R-13: chạy song song các nhánh trong một lô (@thuthuy chọn để kịp mốc thứ Năm)

- **Đo trước:** 13,7 task/giờ. Còn khoảng 41 giờ việc, bằng đúng thời gian còn lại. Tải CPU khoảng 1,0 trên 4 lõi; RAM trống 14 GB.
- **Thiết kế:**
  - Giai đoạn 1 (agent, chấm điểm) chạy song song.
  - Giai đoạn 2 (loss, phân loại, chi phí) tuần tự theo thứ tự nhánh cũ, nên file kết quả có cùng cấu trúc.
  - Mặc định `--arm-parallel 1` giữ nguyên hành vi cũ.
- **Tài nguyên dùng chung đã rà:**
  - thư mục nhánh: riêng;
  - mã lần chấm (run id) của harness: riêng theo nhánh;
  - container: tên riêng theo run id;
  - file báo cáo của harness: tên riêng theo run id;
  - image: chỉ đọc, đã tải trước;
  - bảng giá LiteLLM: **dùng chung, đã sửa (A49)**.
- **Bỏ lệnh dừng giữa các nhánh:** bước kiểm trường hợp xấu nhất trước khi chạy đã đảm bảo tổng chi phí ≤ ngân sách.
- **Chạy thử miễn phí** (`results/pilot/par-dryrun.json`, 3 nhánh song song, 2 task Verified): oracle loss 0, `none` và nhánh hướng dẫn loss 0,667; 0 lỗi hạ tầng, 0 chỗ lệch, 0 bản vá hỏng. Log cho thấy 3 tiến trình agent khởi chạy cùng lúc.
- **Chuyển đổi:** không sửa script đang chạy (bash đọc script dần dần). Script mới `run_e1_par.sh` được chuyển sang ở **ranh giới lô**: chờ thêm một file kết quả, dừng nhóm tiến trình cũ, rồi chạy script mới. Không lô nào bị bỏ dở, không khoản chi nào không được ghi.
- ruff và pytest đều qua. `bash -n` cho các script.

## 03/11/2026, R-14: quy tắc R6 (thuật ngữ, ký hiệu, ngưỡng) và kiểm tra [terms]

- Trước đây quy tắc này chỉ là một ý trong R2 và một mục §4, không có kiểm tra tự động. Nay là R6 riêng ở cả `docs/research_rules.md` và `CLAUDE.md`.
- **Quét các tài liệu sẽ vào paper:** 13 câu khớp. Trong đó 8 câu là phép so sánh có đối tượng (hợp lệ) và 5 câu mơ hồ thật, đã sửa bằng con số hoặc định nghĩa: "quy mô nhỏ" (×2), "mẫu nhỏ", "θ nhỏ thì cần nhiều trial…", "rất nhiều quyết định".
- **Thử với ca xấu cố ý** (L15): câu mơ hồ cài vào bị bắt; câu so sánh, câu có số và lời trích nguyên văn không bị bắt (`tests/test_preflight.py`).
