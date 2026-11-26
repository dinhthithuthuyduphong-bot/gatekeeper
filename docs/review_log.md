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

## 03/11/2026, R-15: hook khởi động phiên và git hook `pre-commit`

- **Hook khởi động phiên** (đồng bộ):
  - lần đầu 4,3 s (cài phụ thuộc bằng `uv`, vì `.venv` do `uv` tạo và không có pip);
  - lần thứ hai 0,8 s (bỏ qua bước cài);
  - đổi `pyproject.toml` thì cài lại (2,3 s); đã khôi phục file.
- Phần nhắc nhở và preflight không bao giờ làm hỏng việc khởi động phiên (`set +e`, `exit 0`).
- **git hook:** thử commit một file chứa khóa giả bằng `git commit` trực tiếp → bị git chặn; file giả đã xóa.
- **Kiểm thử:** ruff, pytest (`tests/test_preflight.py`), `bash -n` cho cả hai hook.

## 03/11/2026, R-16: lưu trữ dữ liệu gốc (@thuthuy: "chọn điều tốt nhất cho việc lưu trữ, đảm bảo dễ kiểm soát")

- **Chọn nhánh git `raw-archive`** thay cho GCS. Cùng chỗ với mã và kết quả, cùng quyền truy cập, có lịch sử, không tốn phí và không cần cấp thêm quyền. GCS cần quyền ghi Storage cho tài khoản dịch vụ và tốn phí.
- **Kiểm trước:**
  - repo **công khai**, nên lô có rule của XRepoSkill (không giấy phép) không được đưa lên;
  - 661 MB dữ liệu gốc không chứa khóa hay đường dẫn tới file khóa.
- **Thiết kế đã review:**
  - nén tất định (đã thử: hai lần nén ra cùng SHA-256);
  - gán log cho nhánh theo tên nhánh dài nhất trước (`control-none` không lấy log của `control-none-seed1`); đã kiểm mọi thư mục log được gán đúng 1 lần, 0 thư mục bị bỏ sót;
  - ghi nhánh bằng lệnh cấp thấp (không đụng thư mục làm việc của E1);
  - quét khóa trước khi ghi;
  - mỗi file < 95 MB (lớn nhất 1,4 MB).
- **Lỗi bắt được khi đối chiếu số lượng:** 932 so với 1.040 trajectory, do lô bị loại và lô bị dừng không được lưu. Đã sửa, nay 1.052/1.052 (trừ lô đang chạy). Lô đang chạy được nhận biết bằng tiến trình đang chạy, không bằng ngưỡng thời gian tự đặt.
- **Tự động:** các script chạy gọi bước lưu trữ sau mỗi giai đoạn (cài bằng đổi tên nguyên tử, không ảnh hưởng tiến trình đang chạy); hook khởi động phiên báo số lô chưa lưu.
- **Kiểm thử:** `verify_archive.py`: 119 lô, 0 chỗ lệch.

## 03/11/2026, R-17: giảm thời gian chạy mà không làm yếu kết quả (yêu cầu của @thuthuy)

- **Đo trước:** khoảng 29% thời gian là xóa và tải image; tải CPU 15,6 trên 4 lõi khi chạy 3 nhánh; bộ test nặng quá giờ khi chấm song song.
- **Ba thay đổi, đều không đổi thiết kế hay ước lượng:**
  - giữ image qua các seed (A54);
  - chấm tuần tự giữa các nhánh (A56);
  - quá giờ khi chấm tính là không resolved, không chấm lại (A56, quy ước của SWE-bench).
- **Review bắt được trước khi chạy:**
  - kiểm dung lượng đĩa sai khi giữ image;
  - giữ image xóa luôn image của tiến trình khác (nên chỉ dùng khi một tiến trình dùng Docker một mình);
  - bước gộp không mang theo danh sách quá giờ và bản vá hỏng;
  - test bắt được lỗi khi gộp lô chạy lại.
- **Chưa làm** (chờ E1 nghỉ giữa hai lần khởi động, vì giữ image cần dùng Docker một mình): chạy thử miễn phí chế độ giữ image với 2 seed xen kẽ.
- **Phần 2 (E2 trên Actions):** đã có dựng lại file hướng dẫn (trùng SHA-256) và thay khối rule kèm bước dò (đã thử). Workflow chưa viết xong; cần @thuthuy thêm 3 secret.

## R-18. Chọn task E2 trên hai khối kiểm định (2026-11-03, trước khi chọn rule cho khối 2)

- **Căn cứ:** bản đăng ký trước E2, mục 3 và ghi chú thực thi 3, 5: lấy 121 task đầu tiên vừa dùng được vừa được kích hoạt, theo đúng `random_order`.
- **Mã:**
  - `make_e2_selection.py`: thêm `--blocks` và `--n`, không có giá trị mặc định.
    - Chặn khi các khối không phủ đúng một đoạn đầu của `random_order`, vì khi đó "121 task đầu" sẽ bỏ qua task chưa kiểm định.
    - Chặn khi một task nằm trong hai khối.
    - Chặn khi chưa đủ n task.
  - `xreposkill_select.py`: `--ids` nhận nhiều file. Kết quả đã có trong `retrieval/` được XRepoSkill đọc lại (`resume=True`, đã đọc mã `retrieval.run_flow_batch`), không gọi lại mô hình. Số token đã ghi vẫn được cộng, nên `spent_usd` là tổng cộng dồn, đúng như `run_e2.sh` trừ vào ngân sách.
- **Kiểm:**
  - Đã kiểm trên dữ liệu thật: khối 1 = `random_order[0:120]` và khối 2 = `random_order[120:200]` (sau khi sắp xếp), cùng một `random_order`.
  - Thêm 2 test.
  - Preflight: PASS.

## R-19. Danh sách việc khi đổi model (`docs/model_switch_checklist.md`, 2026-11-03)

- **Cách soát:** tìm mọi chỗ ghi cứng Gemini hoặc Vertex trong `scripts/`, `src/`, `configs/`, `.github/`, `tests/`, rồi đọc mã liên quan đến tiền.
- **Đã đọc mã:**
  - `load_model_specs`, `litellm_registry`, `estimate_cost_usd`, `traj_usage`, `arm_config`;
  - bộ chặn trường hợp xấu nhất trong `run_pilot.py`;
  - `minisweagent/models/litellm_model.py` dòng 108–126.
- **Số đo dùng trong file:**
  - 1.071 trajectory thật (1.061 Flash-Lite, 10 Flash; 12 của mô hình giả lập bị loại);
  - lời gọi lớn nhất 130.532 token; 1 lần chạy vượt 128.000.
- **Sửa trong lúc soát:**
  - Bản nháp viết rằng sai nhà cung cấp trong `litellm_registry` làm `cost_limit` mất tác dụng. Đọc mã thấy chế độ `default` báo lỗi khi không tính được giá. Rủi ro tốn tiền thật là litellm tính bằng giá khác giá thật. Đã sửa C4.
  - C5: `spent_usd` lấy từ `instance_cost`; token chỉ dùng để tính bù và báo cáo. Đã sửa.
- **Phát hiện mở** (chưa sửa vì chỉ cần khi đổi model; đã ghi trong danh sách):
  - C8: gộp kết quả không kiểm cùng model;
  - C9: preflight không nhận ra key dạng chuỗi;
  - D5: hóa đơn Google chưa được đối chiếu (mục C5 của audit vẫn mở).

## R-20. `scripts/apply_timeout_rule.py` và bước gọi trong `run_e1_inter.sh` (2026-11-03, A57)

- **Căn cứ:** ghi chú thực thi 7 (đã đăng ký trước khi phân tích). Không thêm quy tắc mới, chỉ áp quy tắc đã có lên file do mã cũ ghi.
- **Đối chiếu với `run_pilot.score_arm` hiện tại:**
  - quá giờ ở lần chấm đầu → `TEST_TIMED_OUT`;
  - không có report thì đọc lần chấm lại (trường hợp hợp lệ, không phải quá giờ);
  - bản vá không áp được → `PATCH_NOT_APPLIED`;
  - loss tính bằng `loss_of` như mã chính.
- **Dừng an toàn:**
  - dừng khi một task bị gọi là lỗi hạ tầng vì lý do khác "no report" mà lại có log quá giờ;
  - dừng khi không tìm đúng một thư mục log của lần chấm đầu;
  - file có trường `harness_test_timeout` (mã mới) không bị đụng tới, nên chạy lại nhiều lần vẫn cho cùng kết quả.
- **Kiểm:**
  - 3 test;
  - chạy thử trên 25 file của seed 41 hiện có: không đổi gì;
  - `bash -n run_e1_inter.sh`: không lỗi cú pháp;
  - file gộp của giai đoạn được dựng lại từ các lô ở mỗi lần gọi driver.

## R-21. Luôn tải image trước trong `run_pilot.py` (2026-11-03, A58)

- **Thay đổi:** bỏ điều kiện "chỉ khi có model thật".
- **Ảnh hưởng tới chạy thật:** không, vì trước đây chạy thật cũng đã luôn tải trước.
- **Kiểm:**
  - ruff;
  - test `test_prepull_reports_full_disk` không đổi;
  - chạy lại bước kiểm giữ image với tên mới `kidry2-*`; tiêu chí đạt giữ nguyên như R-17.
- **Bổ sung R-20 (sau lần áp đầu tiên):** sửa 2 lỗi như ghi ở A57.
  - Kiểm tay từng cặp của p25 trước và sau, so với danh sách task mỗi nhánh đã chạy (`exit_status`): chỉ các cặp có cả hai nhánh cùng chạy được tạo hoặc đổi.
  - Thay đổi duy nhất về kết quả: exception-handling/25370 từ "giải được ở lần chấm lại" thành "không giải được (quá giờ ở lần chấm đầu)".
  - Preflight `--ci`: PASS.

## R-22. Chọn rule cho khối 2 và chốt tập E2 (2026-11-03)

- **Kiểm trước khi chạy:**
  - preflight `--ci` PASS;
  - dữ liệu task mới (`data-snapshots`): 120/120 task của khối 1 giống hệt bản cũ.
- **Kiểm sau khi chạy:**
  - 120/120 mục của khối 1 không đổi;
  - kế toán: 0,2946 + 0,1508 = 0,4454 (sau khi sửa A59);
  - tập E2: 121 task, theo đúng thứ tự, khớp `e2_task_sets.json`;
  - SHA-256 của file hướng dẫn dựng lại khớp file gốc.
- **Code:** `spent_on_disk` có test.

## R-23. Sổ ngân sách chung cho E2 trên Actions (2026-11-03, A60)

- **Bất biến:** tổng đã chi cộng tổng đang giữ chỗ ≤ trần.
  - Mỗi lần giữ chỗ chỉ được ghi nếu bất biến này vẫn đúng với bản sổ vừa đọc.
  - Ghi kiểu so-và-đổi: git từ chối lần đẩy không có `--force` khi cha của commit không còn là đầu nhánh.
- **Số dùng:** `WORST` = 2 nhánh × 1 task × 1,00 USD, suy từ đúng các tham số truyền cho driver (không phải số tự đặt). Trần của driver mỗi lần gọi là số đã chi cộng đúng `WORST`, không làm tròn; đã kiểm bằng số rằng nó cho chạy đúng 1 task.
- **Dừng an toàn:**
  - lần gọi không ghi kết quả thì giữ nguyên phần giữ chỗ;
  - số tiền đã ghi không được giảm;
  - giữ chỗ hai lần thì dừng.
- **Kiểm:**
  - 3 test;
  - yaml hợp lệ;
  - chạy thử trên Actions (`budget_usd` 3, 2 job): một job phải chờ job kia trả phần giữ chỗ.
- **Bổ sung R-23 (review lần 2, theo yêu cầu của @thuthuy, trước khi chạy có trả phí):**
  1. **Hết giờ thì phần giữ chỗ bị kẹt.** Khi driver dừng vì thời gian, nó không bắt đầu lần gọi nào, nhưng phần giữ chỗ 2 USD vẫn bị giữ. 20 job sẽ kẹt 40 USD và chặn lần chạy kế tiếp.
     - Nay: `reserve` từ chối sau hạn.
     - Nếu không có thư mục lần chạy mới, coi như không có gì đã chạy và trả lại phần giữ chỗ.
     - Chỉ khi một lần gọi đã bắt đầu mà không ghi kết quả mới giữ lại phần xấu nhất.
  2. **Chạy nối tiếp qua nhiều lần dispatch.** Mỗi job có tối đa khoảng 4,7 giờ cho các lần gọi mới, có thể không đủ.
     - Nay: lần dispatch có trả phí lấy kết quả cũ từ `e2-results` cho đúng shard, để task đã xong không bị chạy lại.
     - Chạy có trả phí bắt buộc 20 shard, để task luôn thuộc cùng một shard.
     - `BASE`: chi phí của các lần dispatch trước không bị ghi hai lần vào sổ.
  3. **Lỗi của chính tôi:** bản viết lại vòng lặp đã bỏ mất quy tắc "một vòng không xong task nào thì dừng" (có ở bản trước và trong `run_e1_inter.sh`). Thiếu quy tắc này, lỗi hạ tầng lặp lại sẽ được chạy lại mãi. Đã thêm lại.
  4. **Ô `guidance_sha256` trống** làm bước kiểm SHA bị bỏ qua. Nay chạy có trả phí bắt buộc phải điền.
  5. **Đã đọc mã mini-swe-agent** (`models/utils/retry.py`): khi lỗi API, agent thử lại 10 lần, chờ theo cấp số mũ 4–60 s. Hết 10 lần thì là lỗi hạ tầng, task được chạy lại ở vòng sau, và quy tắc ở mục 3 chặn vòng lặp vô tận.
  6. **[secrets] chỉ quét file được git theo dõi** (`git grep`) và phần đã stage. File khóa tạm `gha-creds-*.json` do bước xác thực tạo không làm cổng preflight thất bại, và cũng không nằm trong danh sách artifact.
  7. **Giới hạn đã biết, cần người kiểm:** số tiền ghi trong sổ là số tính theo bảng giá của litellm. Hóa đơn Google **chưa từng được đối chiếu** (`docs/audit_pilot.md` C5).

## R-24. Soát E2 đang chạy: ảnh hưởng tới tính hữu dụng của kết quả (2026-11-03, theo yêu cầu của @thuthuy)

| # | Nguy cơ | Kết luận | Bằng chứng |
| --- | --- | --- | --- |
| 1 | Tập phân tích không còn ngẫu nhiên vì dừng theo tiền hoặc thời gian | Không lệch. Task được chia vào shard theo thứ tự ngẫu nhiên đã cố định; việc task có xong hay không phụ thuộc vào thời gian và chi phí của task khác, không phụ thuộc kết quả của chính nó. Dự kiến không bị cắt: chi phí đo được 0,107 USD mỗi lần gọi × 363 lần ≈ 39 < 44,55 | sổ ngân sách: 94 lần gọi, 10,09 USD |
| 2 | Hai nhánh của một cặp chạy khác điều kiện | Không. Cùng lần gọi, cùng seed, cùng runner, chạy song song | `--arm-parallel 2`, `--batch 1` |
| 3 | Runner khác nhau làm lệch phép chấm (quá giờ test) | Đối xứng trong cặp. Quá giờ tính là không giải được, và có phân tích độ nhạy bỏ các cặp đó (ghi chú thực thi 6). Kiểm định task (khối 1 và 2) chạy trên cùng loại runner | `validate-pool.yml` |
| 4 | **Lỗi 429 có thể liên quan đến độ dài lần chạy**, nên việc chạy lại có thể thay mẫu có chọn lọc. Đây là giả thuyết; sửa lại sau khi đo: lần chạy dài giải được ít hơn (p = 6,8 × 10⁻⁴⁷, n = 1.037), nhưng 2/2 lỗi 429 đã gặp xảy ra ở lời gọi đầu tiên. Lần đầu tôi gọi đây là "biến cố xen giữa"; theo câu gốc của ICH thì đây là **dữ liệu thiếu** | **Nguy cơ cần kiểm.** Đã chốt trước khi có dữ liệu: báo cáo tỉ lệ lỗi hạ tầng theo nhánh và phân tích độ nhạy S-infra (ghi chú thực thi 9 của E2, 8 của E1). E1 đã tạm dừng để giảm tải lên Vertex | `merge()` thay cả hai nhánh; file lô giữ lần đầu |
| 5 | Mô hình phía Vertex đổi giữa các lần chạy (nhiều giờ, có thể nhiều lần dispatch) | Kiểm khi phân tích: trường `model` mà API trả về phải giống nhau ở mọi lời gọi (`docs/model_switch_checklist.md` D4) | trajectory ghi `response.model` |
| 6 | `cost_limit` cắt lần chạy | Không: chi phí mỗi agent khoảng 0,05 USD, so với giới hạn 1,00 | sổ ngân sách |
| 7 | File hướng dẫn khác bản đã chốt | Không: SHA-256 được kiểm ở mọi job | `--expect-sha256` |
| 8 | Lỗi chấm trên runner không bị phát hiện (chạy thật không có oracle) | Mỗi job chạy preflight [results] khi kết thúc (`runs == scored + infra`). Khi phân tích kiểm `endpoint_mismatch`, `patch_apply_failed`, `harness_test_timeout`. Chạy thử oracle trên runner đã đạt (run 41636185462 shard 1; lỗi A58 đã sửa) | workflow |
| 9 | Chạy nối tiếp qua dispatch làm task chạy lại hoặc tiền bị tính hai lần | Không. Kết quả cũ được lấy theo đúng shard, 20 shard cố định, và chi phí của lần dispatch trước được trừ ra (`BASE`) | R-23 |

## R-25. Chứng minh lại các định lý từ kết quả đã công bố (`docs/theory/proofs.md`, 03/11/2026)

- **Mỗi bước được gắn nhãn** [ĐN] định nghĩa, [TĐ] tiên đề xác suất, hoặc [CB] kết quả đã công bố, kèm id nguồn và sha256. Bước nào chưa có câu gốc được đánh dấu ⏳.
- **Phát hiện:**
  1. **Giả định SP (superpopulation) chưa được nêu.** Tính hợp lệ của e-process khi mỗi task dùng một lần (`corrections.md` §1.2 lựa chọn (a), RQ1 trong `rq1_mini.py`) cần pool là mẫu i.i.d. từ P_s. Với P_s là chính pool hữu hạn và rút không hoàn lại, Bổ đề E không còn được bảo đảm. Đã thêm vào `corrections.md` và `proofs.md` §0.
  2. **Mẫu số của công thức cỡ mẫu** ở Prop. 9 viết θ², đúng ra là (|STR| − θ)², theo phương trình (17) của Waudby-Smith & Ramdas. Đã sửa.
  3. **Prop. 9 chứng minh được không cần mô hình cộng:** tỉ lệ = 1 + 2 Cov(W, O) / Var(W − O). Đây đúng là đại lượng mà mã tính.
  4. **Theorem 4′ cần giả thiết (iii):** composite được chọn dựa trên dữ liệu thì phải dùng dữ liệu mới để admit. Đã nêu rõ.
  5. Nguồn Holm trong bản lưu là Wikipedia (A64).
- **Còn ⏳:** câu gốc cho TV (Levin & Peres), cho Ville với supermartingale, cho định nghĩa super-population (Miller), cho Holm. Workflow `sources` đang chờ, vì E2 dùng hết 20 job.

## R-26. Chạy lại E1 với tải giảm (2026-11-03 17:05 UTC; A62)

- **Lý do:** E2 còn 7 lần gọi song song (14 agent), so với 40 lúc xảy ra lỗi 429. E1 chạy một mình với 12 agent nhiều giờ liền mà không có lỗi.
- **Thay đổi:** `--workers` 4 → 2 trong `run_e1_inter.sh`, tức 6 agent cho E1 và tổng khoảng 20 agent. Đây là tham số vận hành: chỉ đổi số task chạy cùng lúc trong một nhánh; mỗi cặp vẫn chạy trong cùng một lô. Cùng loại thay đổi như ghi chú thực thi 9 (chế độ M3, ít worker hơn).
- **Theo dõi:** đếm dòng "Error processing instance" (lần chạy hỏng sau 10 lần thử) trong `e1.log`. Thấy lại thì dừng E1.
- **Bộ đếm "Retrying" trước khi chạy lại:** 579 (để so sánh).

## R-27. Bộ chặn chính xác trong driver và ước tính chi phí còn lại của E1 (2026-11-03, A65)

- **Bất biến giữ nguyên:** đã chi cộng trường hợp xấu nhất của lô ≤ trần. Số nhánh lấy từ task set là cận trên của số nhánh thật, vì I(x) có thể loại thêm task.
- **Thứ tự ngẫu nhiên giữ nguyên:** `plan_batch` chỉ lấy một đoạn đầu của danh sách.
- **Có hiệu lực từ lần gọi driver kế tiếp:** mỗi lô là một lần gọi (`--max-batches 1`). Lô đang chạy dùng bộ chặn cũ, chặt hơn, nên vẫn an toàn (L22).
- **Ước tính** (bootstrap, có hoàn lại, trên chi phí từng lần chạy, lấy từ `instance_cost` của 453 trajectory E1):
  - còn 845 lần chạy;
  - tổng cộng dồn: trung vị 114,73; phân vị 95% 118,46; phân vị 99% 120,01; trần 122,26.
  - Giả định: các lần chạy còn lại (seed 51 và 61 trên cùng task) có cùng phân phối chi phí với các lần đã chạy.
- **Kết luận:** rút đề nghị nâng 5 USD cho E1.
- **R-26 bổ sung (18:55 UTC):** E2 còn khoảng 3 lần gọi song song (6 agent), nên E1 trở lại `--workers 4` (12 agent; tổng khoảng 18, dưới mức 20 đã chạy không có lần chạy nào hỏng).

## R-29. Ô MemGovern: mã lọc, hai cấu hình skill, workflow chạy thử miễn phí (2026-11-04; `docs/preregistration_main_draft.md` §11d–11e)

- **Phạm vi:**
  - `scripts/memgovern.py`, `tests/test_memgovern.py`;
  - `arm_config` (`environment`, `dry_run_commands`), `expand_env`;
  - `configs/skills/memgovern-orig.json`, `memgovern-bm.json`;
  - `.github/workflows/memgovern-trial.yml`.
- **Các điểm đã kiểm (§4):**
  1. **Rò rỉ đáp án.** Loại mọi thẻ thuộc **bất kỳ** repo nào của ô (mạnh hơn "cùng repo với task"). Thẻ bị loại ở cả `/search` lẫn `/get_experience`, vì cả hai đọc biến toàn cục `collection` và `experience_data` mà lớp lọc thay thế. Id không có trong bảng thẻ cũng bị loại. Có test.
  2. **Số kết quả không đổi.** `FilteredCollection.query` mở rộng yêu cầu cho tới khi đủ `n_results` thẻ giữ lại, hoặc hết chỉ mục. Có test cho cả hai trường hợp.
  3. **Không sửa mã của MemGovern.** Server được import nguyên vẹn. Hai công cụ được gắn vào container ở chế độ chỉ đọc và gọi qua `bash` (file trong repo không có quyền thực thi).
  4. **Sửa §11d về `top_k`:** server mặc định 5 khi không truyền giá trị, nhưng công cụ `exp_search` mà agent gọi gửi `top_k` = 10 (`topk_default = 10` trong `exp_search.py`; cấu hình agent không đặt `GRAPH_EXP_SEARCH_TOP_K`). Bản gốc dùng 10 như vậy. B-M giữ 5, giá trị mặc định của server, và ghi đây là một khác biệt của biến thể.
  5. **Ghép cặp.** Hai nhánh dùng cùng seed và cùng model. Chỉ nhánh MemGovern có thêm `--add-host` và `-v` (đọc công cụ); nhánh `none` không đổi.
  6. **Không phân phối lại.** Workflow chỉ tải lên tóm tắt kiểm tra và file kết quả. Các file kết quả chỉ chứa id, loss, trạng thái và token, không chứa văn bản prompt. Guidance và trajectory (có nội dung thẻ) không rời khỏi runner.
  7. **Model embedding.** Lấy đúng tên trong server của họ (`Qwen3-Embedding-0.6B`); revision được ghi lúc chạy (`mg_versions.txt`). Nếu số chiều không khớp với chỉ mục, truy vấn báo lỗi và F1 không đạt (lỗi hiện ra, không âm thầm).
  8. **Đường dữ liệu dự phòng trong `exp_search.py`** (`agentic_exp_data_1209`) chỉ được dùng khi server không trả `bug_description`. Server của họ có trả trường này, nên đường dự phòng không được dùng.
- **Preflight:** PASS. **Chi phí:** 0 USD (model giả lập).

## R-30. Plasmode trên dữ liệu thật E1/E2 (2026-11-05; `docs/preregistration_main.md` §8, đăng ký ở commit 6a8b30d trước khi chạy)

- **Kiểm trước khi chạy:**
  - Nền A/A ghép hai lần chạy không skill khác seed của cùng task, nên STR = 0 đúng theo định nghĩa.
  - δ được cấy có kiểm π ≤ 1 (assert).
  - B-X2 gọi đúng `mh_risk_difference` và `Z95` của XRepoSkill tại `26fd703` (import, không chép). Đã thử tay: 3 stratum cho (0,333; 0,272).
  - Holm dùng p anytime-valid.
  - Mọi quy tắc thấy cùng các trial.
- **Chạy thử:** 20 lần lặp mất 1,6 giây. Bản chính 1.000 lần lặp mất 72 giây. Sai số Monte Carlo ≤ 0,016.
- **Pool:** 257 task (E1 và E2), tỉ lệ giải nền 0,368.

## R-31. P1–P3 (2026-11-05; `docs/preregistration_main.md` §9, commit 418280a trước khi chạy)

- **Kiểm:**
  - P1 dùng cùng các ô như §8.
  - Mỗi baseline được kiểm ở 20 lần nhìn (10, 20, …, 200 trial).
  - P3 tách batch1–5 / batch6–10, và các quy tắc chỉ thấy phần sàng lọc.
  - Sai lệch về ước lượng τ² ghi ở Ghi chú thực thi 1.
- **Chạy:** 20 lần lặp thử, rồi 1.000 lần lặp. Kết quả ở `results/plasmode_extra.json`.

## R-32. B3: `--reuse-none` và phép kiểm "model không đổi" (2026-11-05; `docs/preregistration_main.md` §5 và §11)

- **`--reuse-none` (run_pilot, run_batched_pilot):**
  - Nhánh `none` không chạy lại. Loss được lấy từ file kết quả E2 cùng seed.
  - Từ chối file có `model_seed` khác, và từ chối file có hai loss khác nhau cho cùng một task.
  - Có test cho cả hai trường hợp.
  - Bộ chặn chi phí của driver trừ đi một nhánh mỗi task, nên tính đúng số lần chạy thật.
- **`stationarity_check.py`:**
  - Gửi lại đúng lời gọi đầu tiên qua `LitellmModel` của mini-swe-agent, với cấu hình model lấy từ chính trajectory: cùng seed, cùng tham số, cùng công cụ bash.
  - So sánh nội dung, hành động và tên model.
  - Có cổng preflight và trần chi phí.
- **Chạy thử miễn phí (`--dry`):** dựng lại được 344 lời gọi (seed 41: 116, seed 51: 116, seed 61: 112). Mọi lời gọi đều ghi model `gemini-3.1-flash-lite`.
- **Chi phí ước:** khoảng 1.400 token vào và 30 token ra mỗi lời gọi × 688 lời gọi ≈ 0,27 USD; trần 1,0 USD.

## R-33. T1–T3 (2026-11-05; `docs/preregistration_main.md` §14, commit 9596dcb trước khi viết mã)

- **Kiểm trước khi chạy:**
  - e-BH: test tay với K = 4, e = (100; 1; 50; 0,5), α = 0,1, cho đúng 2 bác bỏ (e = 100 và e = 50).
  - e-value của từng ô là E tại n cố định (200), nên hợp lệ cho e-BH.
  - Quy tắc của Library Drift lấy nguyên văn (N_min = 100, τ = 0,10, so trên trung bình toàn bộ trial đã có).
  - Bộ theo dõi kết quả cho giả thuyết "có hại" nhận đầu vào −Z, nên chứng nhận E[Z] > 0.
- **Chạy:** 20 lần lặp thử, rồi 1.000 lần lặp. Kết quả ở `results/lifecycle_plasmode.json`.
- **Giới hạn đã thấy:**
  - Không cài e-detector của Qu et al. (chỉ có một e-process duy nhất từ lúc nhận skill), nên chưa so được với cơ chế thu hồi của họ.
  - Kết quả T3 là điều dễ đoán, vì quy tắc ngây thơ không hề xem dữ liệu của skill ghép.

## R-34. T4 (2026-11-05; §14 và D-M6, commit aabb910 / 055e638 trước khi viết mã)

- **Skill:** `control-oracle-patch` = gợi ý của `control-oracle-tests` cộng thêm bản vá gốc (`{gold_patch}` lấy từ trường `patch`, không bao giờ từ `test_patch`). Test: dòng của bản vá xuất hiện đúng 1 lần, không còn placeholder.
- **Chạy:** `run_t4.sh`:
  - cổng preflight;
  - trần = số đã chi trước T4 (không tính các phần T4) + 6 USD; driver tự chặn khi đã chi + trường hợp xấu nhất vượt trần (`cost_limit` 0,5 × 2 nhánh × 1 task);
  - lô 1 task, seed 41, 250 bước;
  - harness SWE-bench-Live tại máy, cùng commit `ad79b85` như E2;
  - lưu dữ liệu gốc sau mỗi lô;
  - dừng khi `t4_check.py` báo ADMIT (Gatekeeper, K = 1, α = 0,025, theo thứ tự task cố định).
- **Chạy thử miễn phí** (model giả lập, `conan-io__conan-18655`): 2 nhánh đều `Submitted`; 0 lỗi hạ tầng, 0 sai endpoint, 0 bản vá không áp được; đề bài chứa bản vá gốc (7.154 ký tự).
- **Preflight:** PASS.

## R-35. T2b, thu hồi hai bước (2026-11-05; §15, commit fd37f42 trước khi viết mã)

- **Kiểm trước khi chạy:**
  - Σ_k α·6/(π²k²) = 0,02499985 (cộng 99.999 số hạng), tức bằng α.
  - Chuỗi toàn trial có hại (Z = +1) bị thu hồi ở trial 19. Chuỗi toàn trial có ích (Z = −1) không bao giờ bị thu hồi.
  - Bước xác nhận chỉ dùng các trial **sau** lúc báo động.
- **Chạy:** 20 lần lặp thử, rồi 1.000 lần lặp, seed 20271109. Kết quả ở `results/two_stage_retirement.json`.
- **Tiêu chí ghi trước:** thu hồi nhầm ≤ 0,025 **và** độ trễ < 221 trial. **Đạt:** thu hồi nhầm 0/1.000 (cận trên khoảng 0,003); độ trễ 75 trial.
- **Cái giá:** skill có ích bị cách ly nhầm 13% thời gian.
- **Còn phải làm:** viết mệnh đề và chứng minh trong `docs/theory/proofs.md`; rà tài liệu về "báo động rồi xác nhận" trong phát hiện thay đổi.

## R-36. Đường cong nhận nhầm theo độ phủ (§16 và ghi chú 16-1; 2026-11-05)

- **Kết quả** (1.000 lần lặp): khi ngưỡng được chỉnh cho khớp độ phủ 0,5 / 0,7 / 0,8, Gatekeeper, B-X2 và e-BH đều có tỉ lệ nhận nhầm ≤ 0,0003. Plug-in nhìn liên tục: 0,003 / 0,011 / 0,038.
- **Diễn giải đúng:** so tại cùng độ phủ đòi hỏi chỉnh ngưỡng **khi đã biết đáp án**, nên đây là trường hợp tốt nhất cho các baseline. Gatekeeper **không** có lợi thế trên đường cong. Giá trị của nó là bảo đảm có được **mà không cần chỉnh ngưỡng** (ngưỡng = 1/α cố định trước) và vẫn đúng khi bị theo dõi (T1, P1, §13).
- **Hệ quả cho paper:** **không** được tuyên bố "Gatekeeper giảm nhận nhầm tại cùng độ phủ". Endpoint RQ1 gốc **không** ủng hộ tuyên bố đó, và phải báo cáo như vậy.

## R-37. 2.1, pilot skill "repo-test-guide" (§17; 2026-11-05, trước khi chạy có chi phí)

- **Mã và cấu hình đã review:**
  - Skill `configs/skills/repo-test-guide.json`, văn bản đúng nguyên văn §17.
  - Pool `p21-s41_pool.json`: 20 task dùng được đầu tiên của `e2c` theo `random_order`, chưa dùng ở E2 hay T4.
  - Script chạy (scratchpad `run_21.sh`): cổng preflight; seed 41; 250 bước; `cost_limit` 0,5; lô 1 task; `--cap-usd` = tổng chi pilot trước 2.1 + 3,0.
- **Kiểm rò rỉ:** trên 118 task dùng được của `e2c`, `test_cmds` không chứa tên file hay tên test nào của FAIL_TO_PASS (0 trường hợp).
- **Chạy thử miễn phí** (agent giả lập, đúng vòng lặp của script thật theo L37; task `pvlib__pvlib-python-2133`):
  - cả hai nhánh `Submitted`;
  - `infra_failures`, `endpoint_mismatch`, `patch_apply_failed` đều rỗng;
  - hướng dẫn kèm lệnh `pytest pvlib --ignore=pvlib/tests/iotools -rA` có trong quỹ đạo của nhánh skill; 0 lần xuất hiện ở nhánh `none`.
- **Lưu ý vận hành:**
  - Lần kéo image đầu tiên thất bại tạm thời (registry). Kéo thủ công ngay sau đó thì được. Script tự thử lại sau 30 phút, nên không mất tiền.
  - Cổng chi tiêu của script dừng khi "đã chi + lô xấu nhất (2 × 0,5 USD) > trần". Vì vậy chi thực tế không vượt 3 USD, nhưng script có thể dừng trước khi đủ 20 task nếu chi tới khoảng 2 USD. Nếu xảy ra, báo cáo đúng n đã chạy; không nới trần.

## R-38. §18: phép placebo A/A cho việc quy lỗi, độ không đồng nhất (2026-11-05, trước khi chạy)

- **Đối chiếu với bản đăng ký:**
  - Các cặp placebo đúng (51→41, 61→51, 41→61).
  - Quy tắc lỗi chức năng và hồi quy hiệu năng đúng câu gốc của Dong et al.: T = 2,0, min > 1.
  - Có thêm độ nhạy chỉ dùng token.
- **Hai lỗi bắt được khi review, trước khi chạy:**
  1. H18-5 ban đầu tính "tỉ lệ task có ứng viên ở cả 3 seed trên số task có ứng viên", **lệch** câu đăng ký; đã sửa và có test.
  2. CI bootstrap có thể ra nan khi mẫu bootstrap không có ứng viên; đã dùng `nanpercentile`.
- **Dữ liệu:**
  - `run_metrics_e1`: 1.056 lần chạy (720 lần có skill + 336 lần không skill).
  - `run_metrics_e2`: 688 lần chạy (344 lô × 2).
  - 0 lần chạy thiếu dấu thời gian.
  - Hàm `load` dừng nếu gặp cặp trùng.
- **Chạy thử theo L37:** test đầu-cuối trên dữ liệu giả đi qua `heterogeneity`, `summarise` và `power_check`. Tổng cộng 10 test đạt; ruff đạt.

## R-39. §19 phần A, B, D, F (`scripts/placebo_suite.py`; 2026-11-05)

- **Đối chiếu với bản đăng ký:**
  - Luồng A/A dùng `plasmode_real.make_cell` với δ = 0: rút task có hoàn lại, chọn ngẫu nhiên 2 trong 3 lần chạy không skill.
  - B-X2 lấy từ bản XRepoSkill ghim ở `26fd703`.
  - SWE-Skills-Bench: kiểm định đổi dấu chính xác hai phía trên 10 phần tử.
  - Library Drift: N_min = 100, τ = 0,10.
  - e-SR: λ = 0,5, ngưỡng 1/α.
  - Thu hồi hai bước gọi đúng `two_stage_retirement.two_stage`.
  - Thứ tự cặp placebo của D trùng §18; có test kiểm.
- **Lỗi bắt được khi review:** một test ban đầu có `or True`, tức là không kiểm gì. Đã thay bằng phép kiểm tỉ lệ báo động nhầm của e-process dưới nhiễu, với ngưỡng Ville cộng 2 sai số chuẩn.
- **Chạy thử theo L37:** 50 lần lặp, khoảng 4 giây, đi hết A, B, D, F.
  - Lưu ý diễn giải: e-SR báo động ở 100% luồng placebo dài 400. Điều này khớp lý thuyết, vì e-SR chỉ bảo đảm thời gian chạy trung bình tới báo động nhầm (ARL) ≥ 1/α = 40, không bảo đảm xác suất báo động trên cả luồng. Không phải lỗi mã.
- **Công bố:** kết quả B đã xem trong lần chạy thử (ghi chú 19-1).
- 7 test đạt; ruff đạt.

## R-40. §19 phần C, audit bằng skill giả (`scripts/sham_audit.py`, `configs/audit_prompt.txt`; 2026-11-05, trước khi chạy có chi phí)

- **Đối chiếu:**
  - Ba điều kiện đúng §19.
  - Prompt cố định và đã commit trước lời gọi đầu tiên.
  - Cắt 30 message cuối, tối đa 80.000 ký tự (khoảng 20.000 token); bản vá tối đa 8.000 ký tự.
  - Model và tham số lấy từ `configs/models/vertex_gemini.json` (gemini-flash-lite, seed 1), giống agent.
- **Trần chi:** trước mỗi lời gọi, kiểm "đã chi + chi phí xấu nhất của lời gọi tới > trần" thì dừng. Chi phí xấu nhất tính theo số ký tự / 2 token vào, cộng 2.000 token ra.
- **Không lưu văn bản trajectory** vào file kết quả; chỉ lưu quyết định, số token và chi phí.
- **Test:** `parse`; prompt có đủ chỗ điền; `collect` cho đúng 52 cặp có skill thật như §18 (bỏ qua trên CI vì `runs/` chỉ có trên máy làm việc).
- **Chạy thử offline:** dựng đủ 102 prompt, không gọi model. Trung bình 15.274 ký tự, lớn nhất 53.709.

## R-41. §20 S5, đối chứng dương phía "hại" (2026-11-05, trước khi chạy có chi phí)

- **Skill** `configs/skills/control-harm-submit-unchanged.json`, văn bản đúng nguyên văn §20.
- **Task:** 40 task của `harm-minimal-edit` (`configs/pools/s5_pool.json`). Bước 1 dùng 3 task đầu, seed 41 (`s5_probe_pool.json`).
- **Nhánh không skill:** dùng lại từ E1 (`e1none_s{41,51,61}.json`, dựng từ các lô E1; kiểm đủ 40 task ở mỗi seed và không trùng).
- **Cấu hình:** giống `COMMON` của E1 (flash-lite, 250 bước, cost-limit 1,0, batch 4, workers 4). Chỉ khác `--arm-parallel 1`, vì chỉ chạy một nhánh.
- **Trần:** tổng chi pilot trước S5 cộng 7,0 USD; driver dừng khi "đã chi + lô xấu nhất > trần".
- **Chạy thử theo L37** (model giả lập, script thật):
  - `reused_none` trỏ đúng file;
  - `loss_without` khớp E1;
  - văn bản skill có trong trajectory;
  - `infra_failures`, `endpoint_mismatch`, `patch_apply_failed` đều rỗng.

## R-42. Adapter SWE-Skills-Bench và phép thử tín hiệu §22 (2026-11-06, trước khi chạy có phí)

- **Đối chiếu với mã của họ** (commit `4d3450d`):
  - repo clone vào `/workspace/<tên-repo>`, như `lifecycle._clone_repository`;
  - bỏ "cd /workspace/<x> &&" ở đầu lệnh setup, như `lifecycle`;
  - test ẩn chép vào `/workspace/tests/`, như `eval.py`;
  - tỉ lệ pass = passed / (passed + failed + skipped + errors), lấy từ dòng tổng kết của pytest, có cách dự phòng như `_parse_pytest_output`; có test.
- **Lỗi bắt được khi review và chạy thử, trước khi tốn tiền:**
  1. Template SWE-bench của mini-swe-agent cấm sửa test, mà yêu cầu của họ bắt tạo file test. Đã sửa bằng 3 chỗ sửa có kiểm "đúng một lần".
  2. Nộp bằng `git diff` thì mất file mới. Đã chuyển sang chấm ngay trong container.
  3. `docker commit` giữ user root của container dựng. Đã giữ đúng `USER dev` của image gốc.
  4. Ban đầu chỉ chèn `SKILL.md`. Đã cài cả thư mục skill như chế độ "one" của họ; ghi `skill_files`.
  5. Model giả lập thiếu `model_name`. Đã thêm.
- **Chạy thử miễn phí** (model giả lập, nộp ngay):

  | Skill | Kết quả trên repo chưa sửa | Ghi chú |
  | --- | --- | --- |
  | `asyncio-patterns` | 1/15 test qua (batch 1), giống nhau ở hai nhánh | — |
  | `viper-configuration` | 0/15 | `skill_files` = 7 ở nhánh skill |

  - Nhánh không skill không chứa văn bản skill (đếm marker: 0).
- **Proxy:** biến proxy truyền qua `docker exec` lúc dựng, nên không nằm trong image; CA được gắn chỉ đọc.

## R-43. Tính lại power của phép tương quan chuyển giao SSKB (2026-11-06, miễn phí, A83)

- **Mã:** `scripts/sskb_transfer_power.py`. Nguồn số liệu: `ALL_combined_cells.csv` của SSKB (bản clone ghim 4d3450d, MIT; 4 cấu hình × 98 skill chung) và 20 hiệu số theo yêu cầu của §22 (`results/sskb_probe.json`).
- **Kiểm:** α = 0,05 là mức quy ước, truyền bắt buộc qua `--alpha` (không mặc định); xấp xỉ z của Fisher cho tương quan. Số skill 66 = 47 skill image Python + 19 skill image Go trong `tasks/` của SSKB.
- **Kết quả:** hiệp phương sai chéo 3,34 điểm² (sd chuyển giao 1,83 điểm); tương quan giữa các cấu hình SSKB từ −0,105 tới 0,212; nhiễu của mình 29,6 điểm mỗi yêu cầu (9,35 điểm cho 10 yêu cầu); r kỳ vọng 0,091; power 0,178 (một phía), 0,108 (hai phía). Xác nhận đánh giá của reviewer, bác con số 83% trước đó.

## R-44. §23a (model thứ hai) và §23b (sàng lọc–xác nhận) trên SSKB (2026-11-06, trước khi chạy có phí)

- **Đối chiếu bản đăng ký:** §23 commit trước mọi lần chạy có phí; công khai việc đã thấy §22 và dữ liệu SSKB; không chạy thêm `viper` / `asyncio` trên Flash-Lite (giữ quy tắc dừng của §22).
- **Mã đã sửa:**
  1. `sskb_adapter.model_config`: dựng cấu hình model như `run_pilot.py` (kwargs đã đăng ký, gồm `reasoning_effort: low` cho Flash; bảng giá sinh từ `configs/models`).
     - **Lỗi tìm thấy khi review:** bản cũ bỏ qua kwargs của model, nên Flash sẽ chạy với chế độ suy luận mặc định. Đo ngày 02/11: chế độ này tốn khoảng 11 lần token ra, và khác cấu hình đã dùng.
     - Test: Flash-Lite cho đúng cấu hình và bảng giá của §22; Flash giữ `reasoning_effort`; chặn seed 0.
  2. `run_sskb.py`:
     - plan `s23a`, `s23b-screen`, `s23b-confirm`, mỗi plan gắn một model (chạy sai model thì dừng);
     - trần chung cho nhóm `s23b`;
     - cổng chi phí sau 4 lần chạy;
     - `select_confirm` (|D| lớn nhất, hòa thì theo thứ tự; dừng nếu sàng lọc chưa đủ 10 cặp mỗi skill);
     - bỏ việc in tỉ lệ pass trong lúc chạy (L28).
     - Test: số ô, nhóm trần, chọn đúng skill và chiều, chặn khi sàng lọc thiếu.
  3. `scripts/section23_design.py`: xác suất qua quy tắc của 23a theo k; power của 23b. Mức của kiểm định khi không có tác dụng là 0,051.
- **Kiểm §4:**
  - α = 0,05 là mức quy ước, ghi trong bản đăng ký;
  - mốc 6 điểm và quy tắc chọn đặt trước khi chạy;
  - đơn vị xác nhận là batch (2 seed của cùng yêu cầu không độc lập);
  - trần tính từ số đã chi thật;
  - worst cell = cost-limit 1,0 USD.
- **Chạy thử miễn phí:** model giả lập trên batch 1 của 5 skill mới, cả hai nhánh (`runs/sskb-s23-dry`). Kết quả ghi bên dưới khi xong.

## R-45. §24: khảo sát khả năng áp dụng của skill dạng chương trình sửa code (2026-11-06, trước khi chạy trên dữ liệu thật; 0 USD)

- **Đối chiếu bản đăng ký:** §24 commit cùng mã và trước khi workflow chạy trên SWE-Gym. Đã công khai lần chạy thử trên 496 task Live với tập train giả.
- **Đối chiếu paper gốc (mục mới L44):**

  | | Paper gốc | §24 |
  | --- | --- | --- |
  | Skill | Chương trình sửa code có tham số, học từ bản sửa thành công | Hình dạng token của khối sửa trong bản sửa gốc của train |
  | Trial | Áp π, chạy test giữ lại | Chưa chạy (§24 chỉ đếm điều kiện cần) |
  | Loss | 1 − tỉ lệ pass + 0,5 mỗi regression | Không dùng ở §24 |

- **Mã:**
  1. `gatekeeper.patches.change_blocks`: tách khối ở dòng ngữ cảnh, đầu hunk và file mới; bỏ file test (cùng `_TEST_PATH`) và file không phải `.py`. Test: tách đúng, bỏ test và `.rst`.
  2. `scripts/survey_edit_shapes.py`:
     - Bộ tách token có xử lý số hex. Lỗi tìm thấy khi review: `0x1F` từng bị tách thành `NUM ID`; đã sửa và có test.
     - `n_min` dùng đúng `BettingEProcess` của §2; có test khớp ngưỡng.
     - `survey`: phủ bởi một skill, phủ bởi thư viện, ô theo repo và ô gộp. Test có ví dụ đã biết đáp án.
- **Kiểm §4:**
  - α, θ, c truyền bắt buộc, không có mặc định;
  - k = 1 là định nghĩa; n_min là số suy ra (ghi trong `number_provenance`);
  - không `continue-on-error` ở bước mới;
  - thiếu task của split thì dừng (`SystemExit`);
  - file kết quả chỉ có hình dạng đã trừu tượng hóa, không chứa mã của bên thứ ba;
  - không ghi đè kết quả khác (file mới `data/survey/edit_shapes.json`).
- **Chạy thử miễn phí:** 496 task thật (Live), cả hai quy tắc chạy hết, kết quả ở §24.

## R-46. Census SWE-smith và phân tích nguyên nhân gốc (2026-11-06; 0 USD)

- **Mã:** `scripts/census_swesmith.py` chỉ đọc metadata đã commit (`data/benchmarks/summary.json`, các CSV); không đọc kết quả của lần chạy agent nào.
- **Kiểm §4:**
  - các ngưỡng 11 / 22 / 31 là n_min đã suy ra ở §24; 100 và 300 chỉ để mô tả;
  - tên repo SWE-smith được đổi theo mẫu `swesmith/owner__name.hash` → `owner/name`. Đã kiểm thủ công trên 5 tên: pandas, conan, jinja, click, MONAI;
  - không ghi đè file khác.
- **Đối chiếu nguồn (R1):** câu của gskill trích từ snapshot `gskill`; README của gskill đọc ở commit `8c7b697` (bản clone chỉ đọc, MIT).

## R-47. Rà soát vấn đề tiềm ẩn lần 2 và sửa test làm CI đỏ (2026-11-06; 0 USD)

- **Sửa:** `tests/test_sskb_adapter.py` đọc fixture `tests/fixtures/e1_litellm_registry.json` (chép nguyên từ `raw-archive`). Nội dung giống hệt file mà §22 đã dùng, nên phép so vẫn kiểm đúng điều cũ.
- **Kiểm:** pytest đầy đủ qua trên container mới (trước đó 1 test fail). `ruff check`, `ruff format --check` đều qua.
- **Tài liệu:** `docs/potential_issues.md` (21 vấn đề, 8 cơ chế); `docs/root_cause.md` §4 bổ sung P2.

## R-48. §25 F0 và F1: mã, môi trường, chạy thử (2026-11-06)

- **Thứ tự, ghi trung thực:** mọi mục kiểm dưới đây được làm trước khi chạy F0 đủ 100 task. Nhưng bản ghi này được viết trong lúc lần chạy đủ đã bắt đầu (0 USD, quy tắc đã đăng ký ở §25). F1 (có phí) chỉ chạy sau bản ghi này.
- **Đối chiếu bản đăng ký:**
  - tập task = tập test của gskill (đúng hàm chia, có test so với mã gốc);
  - patch (a) và (b) như §25;
  - L gọi nguyên `verify_with_patch`, theo đúng luồng của `evaluate_single_task`;
  - S = `run_evaluation` của SWE-smith.
- **Môi trường:** ghi chú thực thi 25-1 (phiên bản kèm căn cứ, image dẫn xuất, `_is_repo_private`).
- **Lỗi tìm thấy khi chạy thử:** A89 (lỗi hạ tầng bị đếm thành điểm). Đã sửa và có test.
- **F1:**
  - Trần đặt trước mỗi lần chạy ("đã chi + 0,30 > 2,0").
  - Chi phí cộng từ `response_cost` của LiteLLM. Chạy thử bằng `mock_response` ghi được 3,6·10⁻⁵ USD, chứng tỏ callback hoạt động (A84).
  - Nếu một lần chạy có steps > 0 mà chi phí bằng 0 thì dừng.
  - Seed 0 bị chặn. Driver chỉ in chi phí và trạng thái (L28).
  - Chạy thử miễn phí trên 1 task thật: container, agent, nộp bài và chấm đều chạy hết.
  - Job `swesmith_f1` trong `pilot.yml` có cổng preflight; mặc định của input `plan` vẫn là pilot cũ.
- **Kiểm §4:** không ghi đè kết quả khác (file mới); dữ liệu MIT (kiểm bằng dataset card); không có mặc định cho tham số khoa học.

## R-49. Ghi chú 25-3: đo chi phí phản chiếu (2026-11-06, trước khi chạy; trần 1 USD)

- **Mã:**
  - `scripts/reflection_cost_probe.py` gọi nguyên `create_swe_fitness_fn` và `LoggingProposer` của gskill.
  - `reflective_item` chép đúng logic của `make_reflective_dataset` (`gepa@8c7b697`); đã kiểm trên một dict mẫu.
  - Trần kiểm trước mỗi lần chạy agent và trước lần phản chiếu.
  - Bảng giá Flash-Lite sinh từ `configs/models`, khớp fixture của §22.
- **Chạy thử miễn phí:**
  - phần agent đã chạy thử ở F1;
  - phần phản chiếu chạy thử bằng `call_llm` giả trên máy này: `extract_skills` trả đúng nội dung khối ```.
- **Workflow:** plan `swesmith-refl` dùng chung các bước môi trường của F1; có cổng preflight; publish lên `pilot-snapshots`.
- **Điểm còn mở:** giá Pro cho prompt > 200k token khác bảng giá của mình. Ghi lại số token để tính lại nếu cần.

## R-50. §25 bước 2: học và chấm skill gskill (2026-11-06, trước khi chạy; trần 26,2 USD)

- **Đồng hồ chi phí (lỗi tìm thấy khi review, A92):**
  - Bản đầu dùng `litellm.success_callback`, nhưng `gskill/cost_tracker.py:48` gán đè danh sách này, nên trần sẽ mù. Đã sửa: bọc `litellm.completion` và chặn `batch_completion` (không đi qua hàm đã bọc).
  - Kiểm bằng `mock_response`, sau khi đã gán đè `success_callback` như gskill làm: chi phí vẫn được đếm (3,25·10⁻⁵ USD trên 1 lần gọi).
- **Chạy thử miễn phí:**
  - `--smoke-test` của gskill với `mock_response` và `--local-rows`: vòng lặp GEPA, `gepa_state.bin`, `summary.json` (có `num_candidates`) đều chạy hết; đồng hồ đếm 20 lần gọi agent và 3 lần gọi phản chiếu.
  - `--resume` chạy tiếp đúng, từ 20 lên 32 lần gọi.
- **Workflow:**
  - plan `swesmith-learn` (input `half`) và `swesmith-eval`;
  - trạng thái chuyển giữa hai nửa bằng `results/s25_learn_run.tar.gz` trên `pilot-snapshots`;
  - chỉ publish file có thật (`git add` một đường dẫn không tồn tại sẽ làm hỏng bước publish).
- **Kiểm §4:**
  - α = 0,025 một phía và Holm trên 2 phép kiểm, ghi trước;
  - power đã mô phỏng (L11), mức sai 0,008 ≤ 0,0125;
  - trần tính từ số đã chi;
  - không xem kết quả giữa chừng: driver chỉ in chi phí.

## R-51. Phép kiểm "model không đổi" §5, sửa A97 và A98 (2026-11-06, trước khi chạy lại; khoảng 0,25 USD trong 40 USD)
- **Thay đổi:**
  - cài `mcp` (A97);
  - `find_traj` chọn lượt mà E2 tính, theo `run_batched_pilot.merge`: task chạy lại ở phần sau thay dữ liệu cũ (A98).
- **Kiểm §4:**
  - quy tắc so sánh và quy tắc ghép không đổi (R5);
  - test 3 trường hợp (một lượt; lượt sau thắng, so theo số chứ không theo chữ; thiếu hoặc nằm ở hai lô);
  - chạy thử miễn phí trên archive thật cho 109/109 task;
  - preflight đạt.
- **Bổ sung sau lần chạy 3 (cùng ngày):** kết quả 109 task: 107 cho câu trả lời giống nhau giữa hai lần gọi, 75 trùng E2, 109 trùng trường `model`; `pair_with_e2 = false`. Quy tắc đã đăng ký áp nguyên (R5): không ghép. Để đọc được *chỗ khác* thay vì suy đoán (L1), script lưu thêm `sig_e2` và `sig_new`, gồm chỉ lời gọi tool và nội dung, rồi chạy lại một lần (khoảng 0,10 USD). Lần chạy này không đổi phán quyết. Kiểm miễn phí trước đó: 34 task lệch rải trên 18/20 lô và không do cách lưu `content` (cả 109 task đều có `content` rỗng và 1 lời gọi tool).

## R-52. Ô memgovern có phí: hai nhánh mới (ghi chú M-3, 2026-11-06, trước khi chạy; trần 24,5 USD)
- **Mã mới:**
  - các mode `cell-dryrun` và `cell-paid` trong `memgovern-trial.yml`;
  - `scripts/memgovern_cell.py` (Gatekeeper trên tiền tố theo thứ tự E2, kiểm chi phí);
  - `scripts/redact_memgovern.py` (che nội dung, fail closed);
  - `archive_raw.py` coi `memgovern` là nội dung bị giữ lại.
- **Kiểm §4:**
  - thiết kế, α, θ, c và các quy tắc dừng giữ nguyên như đã đăng ký; chỉ phần ghép nhánh đổi, theo §5 (R5);
  - kích thước lô là con số vận hành, có lý do ghi trong M-3;
  - trần tính từ trường hợp xấu nhất của Bleve, nên hai track chạy song song vẫn an toàn;
  - test: 5 test cho phân tích (tiền tố, bỏ task lỗi hạ tầng, lượt chạy lại, admit, dừng vì chi phí, tên lô) và 3 test cho phần che (che, fail closed, bắt ID);
  - định dạng thẻ và đầu ra công cụ đã đối chiếu với mã của MemGovern ở `a845658` (`exp_search.py`, `exp_read.py`, `experience_server.py`);
  - chạy thử miễn phí `cell-dryrun` trên 2 task thật trước khi chạy có phí.
- **Chạy thử miễn phí (06/11):**
  - run 42300889696: không chạy task nào, lộ A100;
  - run 42302062618: chạy đủ, nhưng bước che fail closed, lộ A101;
  - **run 42305733426 đạt:** 2/2 task `Submitted` ở cả hai nhánh, `infra_failures` rỗng; mỗi task 1 lời gọi `/search` và 1 lời gọi `/get_experience`; che xong không còn file nào sót; 2 lô lên `raw-archive`.
  - **Kiểm độc lập** trên file đã lưu trữ, dùng 660.427 cửa sổ 60 ký tự lấy từ mọi thẻ (121.475 thẻ, 3 trường): chỉ khớp 2 chuỗi chuẩn trong `test_output.txt` của **cả hai** nhánh, gồm thông báo traceback của Python ("During handling of the above exception, another exception occurred") và dòng phân cách của pytest. Không có nội dung MemGovern nào.
  - Kết luận: được chạy lô có phí 1 (task 0–9, `cap_usd` 24,5).

## R-53. Ô memgovern bản 2 (sai lệch M-4, 07/11/2026 UTC, trước khi chạy)
- **Mã:**
  - `insert_workflow_step`, `base_instance_template` trong `src/gatekeeper/pilot.py`, với khóa `workflow_step_file` của procedure;
  - cấu hình `configs/skills/memgovern-orig-wf.json`;
  - workflow: file `orig_step.json`, tên lô `mg2-s41`, bước kiểm `[M-4]` (in vị trí và số lệnh, không in văn bản).
- **Kiểm §4:**
  - văn bản chèn vào trùng từng chữ với đoạn của bản 1, chỉ khác vị trí;
  - vị trí đã đối chiếu với cấu hình gốc (các bước 1–6);
  - workflow 5 bước của mini-swe-agent 2.4.6 được kiểm từng chữ trên template thật (test chạy trong venv có mini-swe-agent 2.4.6);
  - thêm 3 test;
  - quy tắc kiểm thao tác chốt trước dữ liệu bản 2;
  - không dùng lại nhánh `none` của lô 1, có lý do;
  - trần có lý do;
  - chạy thử miễn phí bản 2 trước khi chạy có phí.

## R-54. Rà soát độ trung thành với mã gốc (07/11/2026, câu hỏi của @thuthuy: "tự implement lại hay xài nguồn public?")
Đối chiếu từng dòng với gepa@8c7b697 (bản clone tạm, không commit) và MemGovern@a845658.

| Thành phần | Nguồn | Kết luận |
| --- | --- | --- |
| Học skill (GEPA, reflection, chọn ứng viên) | `train_optimize_anything.main()` của gskill, gọi nguyên bản; mình chỉ bọc đồng hồ tiền (`gskill_learn.py`) | mã gốc |
| Chạy agent | `SWEHarness.setup_task` / `run_agent` của gskill, `mini.yaml` của gskill; chỉ đổi `cost_limit` (3,0 → 0,30) và `model_kwargs` (seed 41) | mã gốc. Trần 0,30 chưa từng chặn lượt nào: lượt đắt nhất 0,127 USD trên 500 lượt (F1, chấm, hai nhánh không rò rỉ, Bleve 4a). Giới hạn 50 bước do `swe_harness.py:177` của gskill đặt |
| Bộ chấm L | `verify_with_patch` của gskill; luồng điều khiển chép từ `evaluate/mini_swe_agent.py::evaluate_single_task` (no_patch → F2P → cả bộ test) | viết lại luồng 10 dòng, **khớp từng nhánh** (đã so dòng 92–115) |
| Bộ chấm S | `run_evaluation` của SWE-smith | mã gốc |
| Chia train/val/test | `export_swesmith.py::gskill_split` chép lại số học của `load_and_split_data` (`train_optimize_anything.py:381–434`) | viết lại, **khớp từng bước** (lọc `swesmith/<repo>`, dừng khi đủ, seed, shuffle, thu nhỏ theo tỉ lệ, cắt lát) |
| Nhánh không rò rỉ (§25 bước 3) | can thiệp của mình (một commit mồ côi) | không thuộc gskill; ghi rõ là ngoài phạm vi |
| MemGovern | thẻ, chỉ mục, model embedding, server, `exp_search`/`exp_read` và đoạn hướng dẫn: của MemGovern | **harness không phải của họ**: chạy trên mini-swe-agent thay vì SWE-agent; bản 1 đặt hướng dẫn sai chỗ (A102). Kết quả 0/20 chỉ nói về harness này, không được viết là "MemGovern không hiệu quả" |

## R-55. §27 (07/11/2026, trước khi chạy; trần 6,6 USD trong 7 USD)
- **Mã:**
  - `f1_probe.py --subset no-problem-statement`: chỉ chọn task, không đổi task;
  - lưu quỹ đạo (A104);
  - `pilot.yml` plan `swesmith-s27` (repo jinja/pygments; nhánh placebo/trace34/pair; `dryrun`).
- **Kiểm §4:**
  - tài nguyên bên thứ ba dùng nguyên văn: `cmp` với skill gskill đã lưu, `sha256sum -c` với skill placebo;
  - không `--leak-free` (yêu cầu của @thuthuy);
  - quy tắc chọn placebo có nguồn (WebDev-Skills-Bench C2) và chỉ có một ứng viên;
  - quy tắc chọn repo cố định trước (README của gskill);
  - hai nhánh của 27b chạy cùng lúc (§5);
  - phép kiểm chính, chiều và α đã ghi;
  - 27c chỉ mô tả, đại lượng định nghĩa trước;
  - giới hạn khác thời điểm của 27a đã ghi;
  - chạy thử miễn phí trên GitHub Actions cho cả ba nhánh trước khi chạy có phí.

## R-45m. §26m kiểm bộ chấm (2026-11-06, 0 USD)

- **Đối chiếu bản đăng ký:** §26m commit (`bb82047`) trước khi tính lại tác dụng nào. Trước đó chỉ mới thấy số đếm.
- **Mã:**
  - `scripts/harness_audit.py`: nối từng cặp đã đăng ký với báo cáo chấm qua giá trị loss; ba endpoint S, F, B; bootstrap theo task.
  - `scripts/gold_rescore.py`: chấm lại bản vá gốc 3 lần, mỗi lần một run id mới để harness không dùng lại báo cáo cũ (A21); xóa image sau mỗi instance.
- **Kiểm:**
  - Phép tái lập S khớp đúng số đã đăng ký: E1 53 task, E2 109 task, T4 +0,55.
  - Lỗi A89m bị phép này bắt và đã sửa.
  - Test `tests/test_harness_audit.py`: endpoint, quy tắc "trượt ở mọi lần chấm" và ngưỡng ≥ 3 lần, loss 2/3.
  - Quy tắc B không phụ thuộc nhánh.
- **Không gọi LLM**; chỉ dùng CPU và tải image.

## R-46m. §28m bước 2: chấm lại bản vá của agent với mạng (2026-11-06, 0 USD)

- **Mã:**
  - `scripts/s28_manifest.py`: nối cặp đã đăng ký với báo cáo, rồi với bản vá đã chấm, dùng lại `harness_audit.link`.
  - `scripts/s28_rescore.py`: chia shard theo instance; tải image một lần; xóa cả hai tên image (A92m).
  - `.github/workflows/s28.yml`: dựng từ `rescore.yml` (đã chạy thành công, run 42200960814).
- **Kiểm:** 1.200/1.200 bản vá tìm được; chạy thử cục bộ đạt cho Verified và Live; YAML hợp lệ; preflight.
- **Theo quy tắc §4:** quy tắc tập instance được dùng nguyên văn (R5); cách xử lý "không có báo cáo" đặt trước khi có dữ liệu.

## R-47m. Review paper lần 2 (2026-11-07, 0 USD)

- **Phạm vi:** `paper/main.tex` toàn bộ; đối chiếu từng câu mô tả thiết lập với file cấu hình và bản đăng ký trước (L49).
- **Sửa:**
  - Dataset của E1 (A111m).
  - E1: n = 53 mỗi skill (bản đăng ký E1, giai đoạn mở rộng).
  - Thêm đoạn "Experiments" định nghĩa E1, E2, T4, bước học của gskill và scope.
  - Sham: thay cụm "blame it" bằng số đếm 25/25, 3/25, 5/25; giải thích cận dưới là phần vượt quá tỉ lệ do skill tối đa mà dữ liệu cho phép (`scripts/section21.py`, `lower_bound_new`).
  - Gold 33/35: nói rõ là 35 instance có báo cáo đáng ngờ, chấm 3 lần (§26m).
  - Noise floor: đo trên agent và model của mình, nên chỉ là dấu hiệu.
  - RQ3: bỏ cách nói tuyệt đối ("does not predict", "nothing left").
  - Related work: cổng nhận của Qu et al., HDSO, Library Drift, mọi câu trích đều có trong bản lưu.
  - Threats: độ lặp của bộ chấm, model reflection.
- **Kiểm:**
  - Mọi macro mới sinh từ file kết quả, có CHECKS.
  - Ba mục bib mới chờ tác giả từ arXiv (workflow `data`).

## R-56. Review paper lần 3: không còn chỗ mơ hồ (2026-11-08, 0 USD)

- **Yêu cầu của @thuthuy:** "Review paper, không được còn chỗ mơ hồ".
- **Cách làm:**
  - đọc toàn bộ `paper/main.tex`;
  - đối chiếu từng câu về gskill và MemGovern với `docs/reviewer_fidelity.md`;
  - đối chiếu từng định nghĩa với mã đã chạy: `scripts/s25_ab.py`, `src/gatekeeper/eprocess.py`, `scripts/placebo_suite.py`, `scripts/gates.py`, `scripts/noise_floor_audit.py`, `scripts/sham_audit.py`, `scripts/section21.py`, `.github/workflows/pilot.yml`;
  - quét các từ mơ hồ ("about", "barely", "hardly", "nearly", "few", "some") và các câu tuyệt đối.
- **Sửa:**
  - các lỗi của A121;
  - mọi ngưỡng có giá trị, chiều và đại lượng: 1/α = 40; Holm ở mức họ 0,025 trên {S, L} và trên {nội dung, dùng lại}; test dùng lại hai phía; z = 1,96 cho cổng B-X2;
  - các mô hình được gọi tên qua macro.
- **Kiểm:** mọi macro có định nghĩa; CHECKS mới khớp (1.134 lượt, 1 lượt chạm trần, 221 task A/A, 200 trial, 10 trial mỗi lần nhìn, 14/1 lượt chạm 50 bước).

## R-57. Trả lời một review bên ngoài (2026-11-08, 0 USD)

- **Nguồn mới:** đã đọc bản lưu trước khi trích (R1):
  - `skill_issue_2026`, `hack_verifiable_2026`, `paichecker_2026`;
  - `gskill_swe_harness`: câu điều kiện của bộ chấm, nguyên văn `if "PASSED" in test_output or "passed" in test_output.lower(): passed = True`, kèm ngoại lệ "Patch Apply Failed".
- **Tên không tìm được nguồn:** SAVI, SKILLER, PACE. Không trích.
- **Sửa paper (miễn phí):**
  - ξ_s dùng trong thực tế thế nào (Q1);
  - commit và câu điều kiện của bộ chấm (Q2);
  - chỉ đo một kênh rò rỉ (Q3);
  - chỉ có một placebo vì quy tắc chọn ra đúng một skill (Q4);
  - chưa thử lịch sử viết lại; Δ_leak là cận trên (Q5);
  - giá của việc dùng Gatekeeper trong vòng học, và nó không tự chặn được chỉ dẫn khai thác rò rỉ (Q6);
  - chưa làm ablation sửa skill (Q7);
  - auditor đơn lẻ (Q8);
  - đếm lỗi `go` theo nhánh, thăm dò (Q9; macro `go*`);
  - tính đối xứng dưới A/A làm tỉ lệ nhận nhầm của GEPA tăng về 1/2 khi minibatch lớn hơn (Q10).
- **Cần @thuthuy quyết (có phí):** ablation bỏ chỉ dẫn git khỏi skill; thêm placebo; thêm model hoặc repo.

## R-58. §29 ablation: mã, workflow, bản đăng ký (2026-11-08, trước khi chạy)

- **Đối chiếu bản đăng ký:** §29 được commit trước mọi lần chạy.
- **Mã:**
  - `scripts/make_ablation.py`: quy tắc bằng regex, chặn nếu số dòng bị bỏ khác [7];
  - `tests/test_make_ablation.py`;
  - `pilot.yml` plan `swesmith-s29`: hai nhánh song song, trần riêng 1,75 / 2,25 USD, kiểm file và sha256, dừng nếu `budget_usd` < 4,00.
- **Lỗi bắt được trước khi chạy:** bước workflow gọi `make_ablation.py --check` sau `cd /tmp/work`, mà script dùng đường dẫn tương đối. Đã sửa: chạy từ thư mục repo.
- **Theo danh sách §4:**
  - quy tắc can thiệp cố định trước khi có dữ liệu;
  - trần có nguồn (L53);
  - hai nhánh chạy cùng lúc;
  - test không đọc `runs/` (L50).
- **Chạy thử miễn phí** (run 42458146477, model giả lập): **đạt.**
  - 1 task mỗi nhánh; `s29dry_none` có `skills_chars` = 0; `s29dry_ablate` có 2.421 ký tự (2.427 byte, hai emoji 4 byte), trần 1,75 / 2,25.
  - Prompt thật của nhánh ablation chứa "Look for Logic Inversions" và không chứa "git log -n 5" hay "Check Git History".
  - File ghi ra dưới tên `s29dry_*`, không đụng tên thật.
  - Chi phí ghi 3,25·10⁻⁵ USD mỗi nhánh: tính từ token của câu trả lời giả lập, không có lời gọi model.
- **Sau khi chạy (R-58):** 100/100 task mỗi nhánh; `infra_error` 0, `crashed` 0, lượt chạm cost_limit 0. Phân tích chạy đúng script đã commit trước khi có dữ liệu; số khớp CHECKS của `make_numbers.py`.

## R-59. §30 học lại trong môi trường một commit (2026-11-10, trước khi chạy)

- **Đối chiếu bản đăng ký:** §30 commit trước mọi lần chạy. Phần "đã thấy" chỉ gồm lượt học gốc.
- **Mã:**
  - `scripts/gskill_learn.py --leak-free`: bọc `SWEHarness.setup_task` của gskill, chạy đúng `LEAK_FREE_SH` của `f1_probe.py`, kiểm dòng cuối, đếm số lần đạt vào ledger, dừng với mã 6 khi không đạt.
  - `tests/test_gskill_learn_leak_free.py`: lệnh chạy sau `setup_task`; đếm; dừng khi mã thoát khác 0 hoặc dòng kiểm sai.
  - `pilot.yml` plan `swesmith-s30` (arm `learn`, `eval`): lệnh học chép từ bước §25 và thêm `--leak-free`; ba nhánh chấm song song, chờ theo PID; file chạy thử mang tiền tố `s30dry`.
  - `scripts/s30_analysis.py`: thử trên lượt học gốc cho 5/9 ứng viên có dòng lịch sử và 1 dòng ở skill trả về, khớp số đếm tay.
- **Theo §4:** trần lấy từ chi phí đo của lượt cùng cấu hình (L53); nhánh ghép cặp chạy cùng lúc; quy tắc văn bản cố định từ §29; mỗi câu tuyệt đối sẽ có phép đếm (L52).
- **Rủi ro đã nêu:** một lượt học mỗi điều kiện.
- **Chạy thử miễn phí: đạt.**
  - Bước học (run 42774115077, `--smoke-test`, model giả lập): 20 lượt chạy agent, 3 lời gọi reflection, `leak_free_rewrites_ok` = 20 (mỗi lượt chạy agent một lần viết lại), vòng GEPA chạy hết, có `summary.json`.
  - Bước chấm (model giả lập, 2 task): nhánh A và B có `leak_free` = true và dòng kiểm đạt ở mọi task; nhánh C chạy môi trường gốc trên task không có mô tả; trần 1,75 / 2,25 / 1,00; file mang tiền tố `s30dry`.

## R-60. §30 chạy bù (A124, A125), 10/11/2026, trước khi chạy; trần 1,70 USD (@thuthuy: "duyệt trần")
- **Mã:** nhánh `evalrest` của bước chấm §30 chạy song song hai lệnh `f1_probe.py`, cùng cấu hình với lần chấm đầu:
  - không skill, `--leak-free`, `--skip-done results/s30_none.json`, trần 0,70 (20 task);
  - skill mới, `--leak-free`, cùng file skill đã so từng byte, `--skip-done results/s30_skill_valid.json`, trần 1,00 (38 task).
- `results/s30_skill_valid.json` chỉ chứa 62 lượt hợp lệ, nên 38 lượt bị nhà cung cấp từ chối được chạy lại.
- Bộ chấm dùng nguyên văn (SWE-smith `run_evaluation`, gskill `verify_with_patch`).
- **Trần:** 0,018 USD × số task + 0,30, theo chi phí đo ở chính lần chấm đầu (A107).
- **Chạy thử miễn phí** (`dryrun=true`) để kiểm lệnh shell trước khi chạy có phí.

## R-61. Paper: thêm kết quả §30 (2026-11-10, 0 USD)

- **Mã:** `scripts/make_numbers.py` thêm khối §30, đọc `results/s30_analysis.json` và `results/s30_learn_summary_h2.json`. Khối này kèm danh sách đối chiếu với số đã ghi trong bản đăng ký (33/16, b/c 20/3, admit 65, 0/8 ứng viên, 609 metric call, 1/34, 2/34; 0 lỗi hạ tầng). Một số lệch thì script dừng.
- **Kiểm:** chạy lại `make_numbers.py` (worktree `origin/trial`, rows lấy từ nhánh `data-snapshots`). `paper/numbers.tex` chỉ có 25 dòng mới; mọi số cũ không đổi. Mọi macro `\nclean*` dùng trong `main.tex` đều có định nghĩa.
- **Paper:** thêm vào tóm tắt, phần mở đầu, đóng góp, danh sách đối chứng, bảng RQ2 (dòng ‡) và đoạn "Removing the leak while learning". Mục nói Gatekeeper trong vòng học có thêm một câu. Mục mối đe dọa có thêm "One learning run per condition". Nhánh C chỉ được báo là mô tả, như đã đăng ký (R5): không có kiểm định nào được thêm.

## R-62. Paper: trả lời phản biện 11/11 (0 USD; A126, L56)

- **Nguồn (R1):**
  - Waudby-Smith & Ramdas §5, bản lưu trên `sources-snapshots`: "constructing a WoR test martingale only relies on changing the fixed conditional mean µ to the time-varying conditional mean µ^WoR_t := (Nµ − ∑_{i<t} X_i)/(N − t + 1)".
  - gskill tại 8c7b697 (`gskill_seed_candidate`): "random.seed(seed) random.shuffle(all_data)" trước khi chia train/val/test.
- **Mã mới:** `scripts/s31_alpha_family.py`.
  - (a) Chạy lại đúng quy tắc của `s25_ab.py` (nhánh `trial`) trên 8 luồng với α/8. Lần cắt ngưỡng đầu tiên ở α tái tạo đúng 29/50/34/61/50/24/65 và "không admit" (`make_numbers.py` kiểm và dừng nếu lệch).
  - (b) Mô phỏng H₀ khi lấy không hoàn lại. Kiểm tính hợp lý: với hiệu ứng thật +0,20 thì power là 0,66.
  - Chạy lại cùng seed cho file giống hệt từng byte.
- **Test:** `tests/test_s31_wor.py`, tính đúng E[E_n] ≤ 1 trên mọi hoán vị của 4 pool, có một pool nằm đúng biên H₀ (θ = 1/6).
- **Paper:** §III (giả thiết, mệnh đề prop:wor kèm chứng minh, mô phỏng, đoạn về α); §VI mục mới "Reading the admissions as one family (exploratory)"; bỏ mọi câu "same gain"; nhánh C ghi rõ là mô tả; giữ caveat "cận trên"; tóm tắt rút còn 3 kết quả; tách RQ2 thành chuỗi đoạn; thêm Kết luận; mối đe dọa "Order of the trials".
- **Phân tích thăm dò, sau dữ liệu (R5):** cách đọc cả họ không thay quyết định đã đăng ký. Nó được ghi là thăm dò trong paper và trong `docs/preregistration_main.md` §31.

## R-63. Paper: trả lời phản biện thứ ba (M1–M6; 0 USD)

- **M1 (thứ tự ngẫu nhiên so với seed cố định):**
  - Paper nói rõ xác suất của Mệnh đề 1 tính trên thứ tự. Thí nghiệm dùng một lần rút: seed của gskill, cố định trước khi có kết quả, không do nhóm chọn.
  - Kiểm thêm (thăm dò): chạy cùng quy tắc trên 10.000 thứ tự ngẫu nhiên. 7/7 luồng đã admit vẫn admit ở 100% thứ tự; Pygments 0%.
- **Điểm phụ 1 (θ):** dùng hai biên đã có trong bảng thiết kế (0,02 và 0,05; không chọn số mới). Kết quả: 7/7 và 5/7 admission giữ.
- **Điểm phụ 2 (chi phí):** đếm token từ quỹ đạo §30: khoảng 174 nghìn token input và 10 nghìn token output mỗi cặp task; 4,2–11,3 triệu token input cho mỗi admission.
- **M2–M5, điểm phụ 3–6:** cần thí nghiệm có phí. Đã ghi vào mục Threats của paper và chờ @thuthuy quyết. M6 đã có ở §31; tóm tắt ghi thêm "per-admission level".
- **Mã:** `scripts/s31_alpha_family.py` thêm phần (c), (d), (e). Chạy lại thì các phần (a), (b) cho kết quả giống hệt lần trước. `make_numbers.py` thêm các số mới.
- **Kiểm:** paper biên dịch sạch, không tràn lề; 11 trang, phần nội dung kết thúc ở trang 9.

## R-64. §32–§35: phân tích miễn phí, seed thứ hai, 36 task mới (2026-11-12, trước mỗi lượt có phí)

- **§32 (0 USD):** `scripts/s32_analysis.py` đăng ký trước khi tính; nhãn luồng đặt trước; kết quả ghi là thăm dò.
- **§33 (trần 8,35 USD):**
  - Bản đăng ký và `scripts/s33_analysis.py` commit trước lượt có phí; script chạy thử trên file của lần chạy thử miễn phí (`s33dry_*`).
  - Lần chạy thử miễn phí (run 43134720345): bốn nhánh, kiểm rò rỉ đạt ở hai nhánh một commit.
  - Trần mỗi nhánh = dự kiến + một cost_limit (bài học A108, A125).
  - Sau khi chạy (run 43136184298): 100/100 ở bốn nhánh, 0 `infra_error`, 0 crash, 0 lượt chạm cost_limit, 200/200 kiểm rò rỉ đạt; chi 6,06 USD.
- **§35 (trần 3,95 USD):**
  - Bản đăng ký, quy tắc chọn 36 task, workflow và `scripts/s35_analysis.py` commit lúc 01:54–01:56 UTC, trước khi mở bất kỳ kết quả nào của §33 (kết quả §33 công bố lúc 04:08 UTC).
  - File 36 task kiểm trên nhánh `data-snapshots`: 36 dòng, mô tả rỗng cả 36, 0 task trùng với mẫu 350 của gskill; mẫu Jinja không đổi.
  - Lần chạy thử miễn phí (run 43139341873): bốn nhánh chạy, seed 51, cost_limit 0,30, trần 0,85; 1,10; 0,95; 1,05; dòng kiểm rò rỉ đúng ở hai nhánh một commit.
- **§34:** lần chạy thử đầu bắt được lỗi trần (ghi chú thực thi 34-1); chạy thử lại trước lượt có phí.
- **Paper:** hai đoạn §32 (thăm dò), số sinh bằng `make_numbers.py` có đối chiếu với bản đăng ký; biên dịch sạch, 0 tràn lề.

## R-65. §34 sau khi chạy; paper và báo cáo theo hướng mạnh nhất (2026-11-12)

- **§34, trước phần còn lại:**
  - Ghi chú 34-2 commit trước lượt có phí; trần chia theo chi phí đo ở bước 0.
  - `scripts/s34_analysis.py` commit trước khi mở kết quả, chạy thử trên `s34dry_*`.
  - Lần chạy thử miễn phí của phần còn lại: `--skip-done` chọn đúng 30 và 29 task.
- **§34, sau khi chạy (run 43175845986):**
  - 34/34 task ở cả hai nhánh, không task nào trùng giữa bước 0 và phần còn lại (script kiểm).
  - 0 `infra_error`, 0 crash, 0 timeout ở khâu chấm; lượt đắt nhất 0,207 < 0,34.
  - Chi 5,204 USD, trong trần 6,05.
- **Kiểm cờ M2 ở nhánh không skill (L1, trước khi tin số 34/34):** đọc trace của 6 lượt. "Bug Patch" xuất hiện trong kết quả của lệnh đầu tiên `git status && git log -n 5`, không do regex bắt nhầm.
- **Đếm thăm dò thêm sau dữ liệu** (lệnh đầu tiên là `git log`; mở nội dung commit): đưa vào `s34_analysis.py` với nhãn `exploratory_`. Ghi là thăm dò trong bản đăng ký và trong paper ("defined after the data").
- **Một lần đếm nhanh của tôi bị sai:** đếm `r["S"]` theo kiểu đúng/sai thì mọi lượt đều thành giải được, vì S là dict. Không file nào bị ảnh hưởng. Số chính thức lấy từ `s34_analysis.py`, đọc `S["resolved"]`.
- **Paper:**
  - Thêm đoạn §34 vào RQ3 "Across agents and models", kèm một câu ở tóm tắt, phần mở đầu và kết luận. Threats nay ghi "hai model mô tả cùng hãng".
  - Số sinh bằng `make_numbers.py`, đối chiếu với bản đăng ký (khối `fl*`).
  - Biên dịch sạch, 0 tràn lề; references bắt đầu ở trang 10.
- **Báo cáo HTML:** sửa trực tiếp, không chạy `build_report.py`. Thêm một dòng trong bảng bằng chứng, một ý mới, mục h3 §34, dòng chi phí (6,05 / 5,20) và dòng token.

## R-65. §36: phân tích miễn phí và sửa paper (0 USD; A130, A131, L59)

- **Đối chiếu bản đăng ký:** §36 được commit (`bcb8fb7`) trước khi tính. Phần "đã thấy trước" ghi rõ các số đã nhìn lúc rà soát.
- **Ghi chú thực thi 36-1:**
  - Bản đăng ký nói "đề mục đánh số cấp một". Skill sạch dùng đề mục `#` thay cho đánh số, nên hàm `groups` lấy đề mục `#` khi có và đánh số cấp một khi không có.
  - Ở lượt học sạch, quy tắc lịch sử khớp một lần với chữ "uncommitted" trong một bản đề xuất bị loại. Đó không phải chỉ dẫn đọc lịch sử, và được báo đúng như vậy.
- **Mã:**
  - `scripts/s36_analysis.py`, có test (`tests/test_s36.py`: đảo đúng, tách quỹ đạo, nhóm chỉ dẫn).
  - `scripts/make_figures.py`: dữ liệu cho hai hình pgfplots.
  - `make_numbers.py`: thêm số liệu §36; dừng nếu tên macro không chỉ gồm chữ cái.
- **Kiểm:** lần cắt ngưỡng đầu tiên ở α của hai admission seed 51 tái tạo đúng 53 và 74. Paper biên dịch sạch, không tràn lề; 3 hình đã xem bằng ảnh.

## R-66. §37 giai đoạn 0 của hướng Kaggle (0 USD): đã chuyển sang `kaggle/review_r66.md` trên nhánh `claude/gatekeeper-13-research-nxytoh`

## R-68. §41 kiểm toán lịch sử git và trace (17/11/2026; thăm dò; 0 USD; không gọi model)

- **Mã:** `scripts/history_audit.py`. Mức 1 đọc repo task thật (bản sao `--mirror` của ba repo trong thư mục tạm của phiên, không đưa vào repo); mức 2 và 3 đọc 29 file trace có sẵn trong `results/`.
- **Quy tắc nhận diện sửa một lần, trước khi đọc kết quả theo nhánh:**
  - bộ đầu báo nhầm ở môi trường một commit (8 lượt Bleve có "diff Bug Patch", 1 lượt Jinja có "test bị xóa"), nơi không có gì để thấy;
  - nguyên nhân: `git show HEAD` in cả cây mã với dấu `+`; agent tự `git diff` bản sửa của lỗi đảo nhánh `if`;
  - bộ cuối cho 0 lượt ở mọi nhánh một commit (669 lượt; bản đầu của mục này và của §41 ghi nhầm 730 do cộng tay, được `make_numbers.py` bắt khi đối chiếu ngày 17/11 và sửa trước khi vào paper). Bộ đầu vẫn được tính (`*_loose`).
- **Test:** `tests/test_history_audit.py`, 7 ca, gồm ba ca báo nhầm ở trên.
- **Kiểm chéo bằng tay:** đọc trace `combine_file__yjwp1l4i` của agent thứ hai (`git show --stat` trên commit "Remove F2P Tests", rồi `git checkout <Initial commit> -- tests`, rồi `pytest`) và sáu lượt Bleve bị báo nhầm.
- **Làm trái L60:** từ 16/11 tôi commit lên `main` từ một worktree phụ, bằng `-c core.hooksPath=…` để hook vẫn chạy. Hook đã chạy đủ ở mọi lần; `core.bare` vẫn là `false` ở cả hai thư mục. Từ commit này tôi làm trong thư mục chính, chuyển nhánh ở đó.

## R-69. Paper viết lại cho EASE 2027 (17/11/2026; 0 USD)

- **Mẫu:** `acmart` (`sigconf,review,anonymous`), đúng tùy chọn CFP yêu cầu; không tên tác giả, không đường dẫn repo. 7 trang kể cả tài liệu tham khảo (giới hạn: 10 trang nội dung, thêm 2 trang tham khảo). 0 lỗi, 0 tràn lề.
- **Mạch:** mức tăng → cơ chế → can thiệp → phần còn lại → phạm vi → kiểm tra đo lường (theo meta-review).
- **Thống kê:** chứng nhận = phép kiểm cuối pool (§42, `docs/method_end_of_pool.md`), mệnh đề có chứng minh; ba đại lượng T1–T3; bỏ Định lý 2 cũ (phần chưa chứng minh trên rủi ro kỳ vọng) và Mệnh đề 3 cũ (sai với thủ tục không bao giờ nhận); e-process tuần tự giữ vai trò đã đăng ký; trích PACE là nơi đã công bố thống kê.
- **Dữ kiện mới:** §41 (ba commit, hai kênh rò rỉ) thay câu "cận trên" và câu "một kênh"; §42 (12 quyết định, cấu trúc lượt chạy). "609 rewrites" sửa thành 609 container (một cho mỗi lần chấm). "All agent runs use one model" bỏ.
- **Bảng và hình:** bảng kê thí nghiệm; bảng 12 quyết định (cùng job hay khác lượt chạy, E, ngưỡng 40 và 480, điểm vượt ngưỡng hồi cứu); bảng task không mô tả có mẫu số; bảng các quy tắc quyết định theo mục đích, mức, số lần nhìn; hình cơ chế với nét liền (đo được) và nét đứt (suy ra); biểu đồ mức tăng có khoảng tin cậy; dòng thời gian đăng ký và hai nhóm task.
- **Mọi con số là macro** (`make_numbers.py`, có đối chiếu); thêm khối §41, §42, nhóm task của phép thử C, bảng chéo của cờ theo dõi. Bộ đối chiếu bắt được một lỗi cộng tay của tôi (730 thành 669, §41).
- **Danh mục:** thêm PACE qua `configs/bib_overrides.json` (tên và tác giả đối chiếu với bản lưu); năm của mọi mục lấy từ bản lưu (A134).
- **Chờ @thuthuy:** tên bài (Q3); nội dung khai báo dùng AI (A5, chưa đọc được chính sách ACM); đường dẫn gói tái lập ẩn danh (A4).

## R-70. Minh bạch và gói tái lập ẩn danh: F1–F4, A4 nội bộ (17/11/2026; 0 USD)

**Phạm vi:** `scripts/registration_timeline.py`, `scripts/build_replication_package.py`, `scripts/package_manifest.py`, tùy chọn `--named-only` của `scripts/check_anonymity.py`, và các file kết quả `results/registration_timeline.json`, `results/package_manifest.json`.

**Kiểm theo danh sách §4:**
- **Không có con số khoa học mới.** Các script chỉ đọc git và file kết quả có sẵn.
- **F1, thời điểm đăng ký:**
  - lấy commit đầu tiên chứa dòng tiêu đề (`git log -S`, ngày commit);
  - kết quả đầu tiên lấy từ lần thêm file trên `pilot-snapshots`, theo ngày tác giả, vì ngày commit đã bị đặt lại khi nhánh được viết lại;
  - lần chạy đầu cho thấy mọi mục cùng một thời điểm 01/11. Nguyên nhân là đọc `%cI` và tách khối sai; đã sửa trước khi dùng.
  - Kết quả: 52 dòng, 0 mục có kết quả trước đăng ký.
- **A4, quét danh tính:** lần dựng đầu báo 300 chỗ. Phân loại từng nhóm:
  - phần lớn là của bên thứ ba: tổ chức GitHub và email trong patch của task;
  - 43 chỗ là chữ "thuyết", do từ "Thuy" trần trong danh sách tên;
  - chỗ lộ thật duy nhất nằm trong chính script dựng gói (mẫu REDACT).
- **A4, cách sửa:**
  - bỏ script dựng gói ra khỏi gói;
  - danh sách tên chỉ dùng các dạng đầy đủ;
  - thêm `--named-only`: email và URL tài khoản chỉ bị báo khi chứa một tên. Có test `test_named_only_keeps_named_addresses_and_drops_third_party`. Chế độ mặc định không đổi.
- **A4, kết quả:** lần dựng lại có 2034 file và 0 chỗ lộ. Kiểm thêm ngoài công cụ:
  - `grep` trên mọi file văn bản;
  - `zcat | grep` trên mọi file `.gz` (trace), vì công cụ quét không đọc file nén.
  - Cả hai đều 0 kết quả.
- **F4:** trong thư mục gói, chạy `make_numbers.py --trial trial --rows <rows>`. Kết quả:
  - `paper/numbers.tex` giống hệt bản trong repo;
  - `src/` của gói giống hệt repo, trừ thư mục egg-info.
  - Giới hạn: đây là thư mục sạch, không phải máy cài mới.
- **F2, ý nghĩa trường "L":** ban đầu tôi viết docstring theo trí nhớ ("1 = vẫn lỗi"). Đọc `passed()` trong `scripts/s25_ab.py` thì thấy sai:
  - "S" là bộ chấm chặt, đọc trường `resolved`;
  - "L" là bộ chấm nới, đọc trường `passed`.
  - Đã sửa docstring trước khi commit.
- **F2, còn thiếu:** phiên bản bộ chấm, và mã bản dựng model của nhà cung cấp. Đã ghi trong todo.
- `python scripts/preflight.py --ci`: PASS.

## R-71. C10: biến thể lịch sử git, plan `swesmith-c10`, hướng dẫn phần có phí (17/11/2026; 0 USD)

**Phạm vi:**
- `scripts/history_variants.py`, `tests/test_history_variants.py`;
- `--history-variant` và `--neutral-message` trong `scripts/f1_probe.py`;
- bước C10 trong `.github/workflows/pilot.yml`, `tests/fixtures/c10_dryrun.json`;
- `docs/guide_paid_steps.md`; A135, L63.

**Kiểm theo §4:**
- **Không có con số khoa học mới trong mã.**
  - Câu trung tính của B không có giá trị mặc định: chạy có phí chỉ đọc từ `configs/c10.json`, file chỉ có sau khi đăng ký.
  - Seed 51 và cost_limit 0,30 lấy từ §35 đã đăng ký.
- **Cấu trúc ba commit** dựa trên §41 mức 1 (1.086/1.086 task). Script vẫn kiểm lại thông điệp của từng task và dừng (mã 3) nếu khác.
- **Tính đúng:** 9 test trên một repo git dựng theo hình task SWE-smith, có remote, mirror và tag, HEAD trên nhánh và HEAD tách rời. Mỗi test kiểm:
  - cây của HEAD không đổi;
  - commit "Remove F2P Tests" có diff giống hệt bản gốc;
  - tác giả và ngày được giữ;
  - A cho đúng mã băm gốc, tức siêu dữ liệu được giữ từng bit;
  - B mang câu trung tính và vẫn có diff lỗi;
  - C và D không còn mã trước lỗi ở bất kỳ đâu trong lịch sử.
- **Chưa kiểm được ở máy của phiên:** cách gc xử lý đối tượng trong file pack của image thật (không có Docker và image). Chuỗi kiểm `t0_present` ghi lại điều này ở mọi lượt. Chạy thử miễn phí ở bước 4 của hướng dẫn kiểm nó trên container thật trước mọi lượt có phí.
- **Lỗi phát hiện khi review:** con số chi phí 0,0746 USD mỗi task của C10 là số dự kiến, không phải số đo (A135, L63). Đã tính lại từ `cost_usd` và `spent_usd` của §33 và §35:
  - 34 task: dự kiến 3,03, trần 5,43 USD;
  - 70 task: dự kiến 5,81, trần 10,61 USD.
- **Con số C6 (5,9 USD)** khớp số đo: §34 đã chi 5,2042 USD, cộng 2 × cost_limit 0,34.
- `bash -n` trên bước workflow đã thay biến: đạt. YAML hợp lệ.

**Bổ sung R-71: kết quả chạy thử miễn phí C10 (run 44016252054, 17/11).**
- Có tám file `results/c10dry_*_test34.json` trên `pilot-snapshots`, mỗi file 1 lượt.
- `history_check` đúng chuỗi mong đợi ở cả tám nhánh, trên container task thật:
  - A: `commits=3 bug_msg=1 t0_present=1`;
  - B: `bug_msg=0 t0_present=1`;
  - C: `bug_msg=1 t0_present=0`;
  - D: `commits=2 bug_msg=0 t0_present=0`.
- Như vậy gc đã xóa cả các đối tượng trong file pack của image thật. Điều này trước đó chưa kiểm được ở máy của phiên.
- Không lượt nào sập.
- `spent_usd` = 0,0000325 mỗi nhánh. Đây là giá LiteLLM tự tính cho câu trả lời giả lập, không có lệnh gọi model nào; chạy thử §35 cho đúng con số này (`s35dry_ship_none.json`).
- Chưa chạy thử `c10all70`.

**Bổ sung R-71 (sau A136):** script đọc ngày dạng raw; test có thêm múi giờ +07:00. Lần chạy thử đầu kiểm bản script trước khi sửa, nên phải chạy thử lại `c10test34` trên commit sửa trước mọi lượt có phí.

**Bổ sung R-71: chạy thử lần 2 (run 44017477445, commit 0ef09dc đã xanh CI), `c10all70`.**
- 16 file (8 nhánh × 2 phần), mỗi file 1 lượt: task đầu của 34 task test và task đầu của 36 task mới.
- `history_check` đúng chuỗi mong đợi ở 16/16 file, cả với bản script đọc ngày dạng raw.
- Không lượt nào sập. Không có lệnh gọi model.
- Mặt máy móc của C10 đã sẵn sàng. Còn lại là bản đăng ký §43 và câu duyệt ngân sách của @thuthuy.

## R-72. Bản đăng ký §43 (C10), `configs/c10.json`, `scripts/c10_power.py`, `scripts/c10_analysis.py` (17/11/2026; 0 USD)

**Vì sao làm trước:** @thuthuy 17/11: "Chọn phần sẽ cải thiện mạnh làm trước". C10 trả lời thẳng lời bắt bẻ D1 của bản review, và mọi khâu trừ tiền đều do tôi làm được. C4′ thì phụ thuộc các ô Kaggle do @thuthuy chạy.

**Kiểm theo §4:**
- **Phép thử chính chỉ có một (A − C)**, chọn trước dữ liệu. Lý do: chỉ cặp này giữ nguyên số commit và thông điệp. Ở các bản nháp trước (todo mục 7 và hướng dẫn), phép so chính là B − D; đổi sang A − C vì cặp đó đúng là phép thử "rò rỉ thuần". Lúc đổi chưa có dữ liệu C10 nào (R5 không áp dụng).
- **Power** mô phỏng đúng quy tắc quyết định cuối cùng (L11): phép kiểm cuối pool trên D_i, cả power lẫn tỉ lệ sai dưới H₀ (≤ 0,0006).
  - Giới hạn: kịch bản H₀ dùng tỉ lệ giải gộp, không theo từng task. Tính hợp lệ của phép thử đã được chứng minh ở `docs/method_end_of_pool.md` và không dựa vào mô phỏng này.
- **Câu trung tính:** quy tắc và danh sách từ cấm được viết sau khi xem 15 thông điệp upstream, trước mọi kết quả của agent. Điều này ghi minh bạch ở §43.
  - Đã mở chính commit upstream: `ada0a9a6` là "update test workflow trigger"; `ee6c734` là "Merge branch 'stable'".
- **Trần:** từ `cost_usd` đã chi (L63). Bước kiểm ngân sách trong workflow đã sửa để chỉ cộng các phần được chạy; trước đó lượt `c10test34` sẽ đòi `budget_usd` ≥ tổng của cả hai phần.
- **Script phân tích:**
  - 2 test tổng hợp: bác bỏ khi chỉ A có lợi; không bác bỏ khi C bằng A; bỏ task thiếu hoặc lỗi hạ tầng.
  - Chạy được trên 16 file của lần chạy thử thật.
  - Script dừng nếu `history_variant` của file không khớp với tên file.
- **Nguồn gốc con số:** 4 dòng mới trong `docs/number_provenance.md`.
- **Còn phải làm trước khi chi:** chạy thử miễn phí lại với `configs/c10.json` thật (câu trung tính thật), sau khi CI của commit này xanh (L64).

**Bổ sung R-72: chạy thử với cấu hình thật (run 44022855259; commit 4c132ab đã xanh CI; 17/11).**
- `c10all70` với `configs/c10.json`: 16/16 lượt có `history_check` đúng, 0 lượt sập.
- Bốn file của B ghi `neutral_message` = "Merge branch 'stable'".
- Bước kiểm ngân sách cho qua với `budget_usd` = 11 (tổng trần 10,83).
- Không có lệnh gọi model. Mọi khâu trước khi chi đã xong; còn chờ câu duyệt ngân sách.

## R-73. Ghi chú thực thi 43-1: trần C10 làm tròn xuống (17/11/2026; 0 USD)

- Lỗi A137: tổng trần 10,8302 USD lớn hơn mức đã duyệt 10,83 USD. Workflow chặn trước mọi lệnh gọi model.
- Sửa `configs/c10.json`: mỗi trần làm tròn xuống 3 chữ số thập phân, tổng 10,825. Đã chạy lại đúng phép kiểm của workflow với `budget_usd` = 10,83: đạt.
- Không đổi gì khác của §43. Chưa có dữ liệu C10.
- **Chưa chạy lại:** @thuthuy báo 17/11 đã tắt API gọi tới tài khoản Vertex AI. Lượt có phí chỉ chạy lại khi @thuthuy bật lại và xác nhận.

## R-74. Ghi chú thực thi 43-2: một lượt 70 task cho mỗi nhánh (17/11/2026; 0 USD)

- **Vì sao:** @thuthuy chỉ muốn trừ vào credit 10 USD. Tổng trần cũ (10,825) có thể vượt credit.
- **Đây là phương án trội:** cùng thiết kế, cùng dữ liệu, trường hợp xấu nhất thấp hơn (8,426 so với 10,825 USD). Tôi tự quyết theo quy tắc quyền quyết định và báo sau.
- **Kiểm:**
  - Bước dựng hàng task của workflow chạy trên dữ liệu thật: 70 hàng, đúng thứ tự (34 task test trước, rồi 36 task mới), cùng một nhãn split.
  - `bash -n` trên bước workflow đạt; YAML hợp lệ.
  - Phép kiểm ngân sách chỉ cộng `caps_all70`: 8,426 ≤ 10,83.
- **Còn phải làm trước khi chi:** CI xanh, rồi chạy thử miễn phí `c10all70` với model giả lập (L64).

## R-75. Phân tích C10 sau lượt có phí; thêm 8 nhánh C10 vào kiểm toán trace; số của paper (17/11/2026; 0 USD)

- **Phân tích chính:** chạy đúng lệnh đã đăng ký, không sửa `scripts/c10_analysis.py`. Kết quả: `results/c10_analysis.json`.
- **`scripts/history_audit.py`:**
  - Chỉ thêm 8 dòng vào `ARMS` (nhãn môi trường "C10 A/B/C/D: …"). Quy tắc phát hiện không đổi.
  - Kiểm: phần level 1 và mọi lượt của 29 nhánh cũ trong `results/history_audit.json` giống hệt bản trước khi chạy (so bằng máy).
- **`scripts/make_numbers.py`:**
  - Các con số §41 về cờ "Bug Patch" (`monConf*`) bỏ qua các nhánh `c10_`, để giữ đúng tập trace mà các giá trị đã kiểm tham chiếu.
  - Thêm macro `cten*` từ `results/c10_analysis.json` và kiểm toán trace, với các phép kiểm khớp (n, số dấu, quyết định, "tối đa" không skill).
  - `paper/numbers.tex` chỉ thêm dòng; mọi macro cũ giữ nguyên giá trị (diff).
- **Paper:**
  - Thêm đoạn "Separating the message from the diff".
  - Threats, Interventions: bỏ câu "we did not separate the two channels in an experiment".
  - Trích Ramdas et al. (arXiv 2210.01948) cho bảo đảm ở thời điểm dừng. Câu trích đã kiểm trong bản chụp `ville_inequality`.
  - Bài dựng không lỗi: 8 trang.
- **Ghi lỗi:** A138, L66 (danh sách §4); ghi chú thực thi 43-3.


## R-76. Kiểm toán điểm cắt theo chi phí của C10; sửa câu chữ trong paper (17/11/2026; 0 USD)

- **Vì sao:** phản biện của @thuthuy cùng ngày nêu hai điều cần kiểm: (1) điều kiện "dự đoán được" của điểm dừng; (2) 45 task có bị chọn theo kết quả không.
- **Mã mới:** `scripts/c10_stop_audit.py`, test `tests/test_c10_stop_audit.py` (2 test).
  - Không có giá trị mặc định cho λ, θ, ngưỡng, kích thước pool cố định.
  - Đọc chỉ file kết quả.
- **Kết quả:** xem ghi chú thực thi 43-4. Phát hiện mới: trên pool 34 task cố định trước, E = 26,65, không bác bỏ.
- **`scripts/make_numbers.py`:** thêm 4 macro (`ctenACEfixed`, `ctenACFirstK`, `ctenACMinAfter`, `ctenFixedN`), kèm kiểm khớp. Mọi macro cũ không đổi.
- **Paper:** đoạn C10 viết lại. Bỏ chữ "certified". Nêu pool cố định 34 task không bác bỏ; nêu giả thuyết hẹp hơn và lý do điểm cắt là thời điểm dừng. Bài dựng không lỗi, 8 trang.

## R-77. Đăng ký §44 (C10R): cấu hình, workflow, trần, power (17/11/2026; 0 USD)

- **Mã mới:**
  - `scripts/c10r_caps.py` (quy tắc L66; test `tests/test_c10r_caps.py`, 2 test);
  - `scripts/c10r_power.py`;
  - `configs/c10r.json` do script sinh.
- **Workflow:** arm `c10r70` trong bước C10.
  - Đọc `configs/c10r.json`, tiền tố `c10r`, seed từ cấu hình. Các arm cũ giữ seed 51 qua giá trị mặc định khi cấu hình không có khóa `seed`.
  - Kiểm `bash -n` trên bước này đạt; YAML hợp lệ.
- **Đã kiểm:**
  - Tổng trần đúng bằng 12,64 dưới phép cộng số thực (L65).
  - Không hàm nào nhận λ, θ, ngưỡng hay phân vị có giá trị mặc định.
- **Còn phải làm trước khi chi:**
  - CI xanh;
  - chạy thử miễn phí `c10r70` (model giả lập);
  - @thuthuy xác nhận credit.
- **Chạy thử miễn phí `c10r70` đạt** (run 44114737043, commit `af7d584`, model giả lập, 1 task mỗi nhánh):
  - 8/8 nhánh: seed 61, trần đúng `configs/c10r.json`;
  - `history_check` đúng chuỗi của từng biến thể (A 3/1/1, B 3/0/1, C 3/1/0, D 2/0/0);
  - câu trung tính chỉ ở B; skill (2.675 ký tự) chỉ ở nhánh có skill;
  - 0 lỗi hạ tầng.
- **Ngân sách:** @thuthuy 17/11 duyệt 12,64 USD, chấp nhận trả phần vượt credit (CLAUDE.md).

## R-78. Phân tích C10R (§44) sau lượt có phí; kiểm toán trace; số và đoạn văn của paper (17/11/2026; 0 USD)

- **Phân tích:** chạy đúng lệnh đã đăng ký (`c10_analysis.py --prefix c10r`) và `c10_stop_audit.py --prefix c10r`. Không sửa script nào.
- **`scripts/history_audit.py`:**
  - Thêm 8 nhánh `c10r_*` (seed 61). Quy tắc phát hiện không đổi.
  - Mọi lượt của 37 nhánh cũ và phần level 1 giống hệt bản trước (so bằng máy).
  - Lần thêm đầu không áp được: dòng mốc đã bị ruff tách thành nhiều dòng, và phép assert của chính bước thêm đã chặn lại. Không có dữ liệu sai.
- **`scripts/make_numbers.py`:**
  - Bảng tra nhánh C10 thêm điều kiện seed 51. Trước đó (môi trường, điều kiện) của seed 61 sẽ ghi đè lên seed 51.
  - Phép đếm cờ của §41 bỏ mọi nhánh bắt đầu bằng `c10` (gồm `c10r_`).
  - Thêm macro `ctr*` kèm kiểm khớp: đủ 70 task ở mọi nhánh, n = 70, 40/0, 41 giải được, 70 lượt thấy diff, quyết định bác bỏ.
  - Mọi macro cũ không đổi (diff).
- **Paper:** đoạn "Separating the message from the diff" viết lại.
  - C10R là phép thử xác nhận trên pool cố định ("certified").
  - Lượt đầu chỉ được báo là cùng chiều, và chỉ hợp lệ dưới giả thuyết hẹp hơn.
  - Bài dựng không lỗi, 8 trang.

## R-79. W5: câu chữ về loại task trong paper (18/11/2026; 0 USD; @thuthuy 18/11: "Tranh thủ làm 2 cái 0usd")

- **Threats, Measurement:** câu "Tasks are synthetic, from three repositories" được thay. Câu mới:
  - Các thí nghiệm về skill dùng task SWE-smith: repo thật, lỗi được chèn, lịch sử do benchmark dựng. Vì vậy kết quả về rò rỉ chỉ nói về các benchmark được dựng theo cách này.
  - Các luồng A/A và mức nhiễu khi chạy lại dùng issue do người viết của SWE-bench và SWE-bench-Live.
- **Kiểm nguồn của câu:**
  - Luồng A/A lấy từ `scripts/placebo_suite.py::aa_tasks` (E1 và E2).
  - Mức nhiễu lấy từ `scripts/plasmode_real.py::RUNS` (`g1-e1all-*`, `g2-e2-*`).
  - E1 là bộ test SWE-bench (`docs/preregistration_e1.md`); E2 là SWE-bench-Live (`docs/preregistration_e2.md`).
- **Trích dẫn mới:** `swebench_iclr` và `swebench_live`. Cả hai đã có trong `configs/sources.json` (`swebench`, `swe_bench_live`); tiêu đề và tác giả đã đối chiếu với bản chụp.
- **Đoạn "Decision rules under A/A":** ghi rõ nguồn task.
- Không con số nào đổi. Bài dựng không lỗi, 8 trang.

## R-80. Đăng ký §45 (W7-b): workflow, cấu hình, bộ chuyển dữ liệu, ô Kaggle, phân tích (18/11/2026; 0 USD)

- **Workflow:** bước §34 có thêm arm `lfnone`: Flash không skill, `--leak-free`, cả 34 task.
  - `budget_usd` và `cost_limit` phải trùng `configs/w7b.json`.
  - Dòng `tail` của bước được sửa để không làm hỏng job khi một file log không có (shell chạy với `-e`).
  - `bash -n` đạt; YAML hợp lệ.
- **`configs/w7b.json`:** trần 3,827 theo quy tắc L66 (cách tính ghi trong file).
- **Nhánh mặc định** (`kaggle/`):
  - `w7_build.py` cùng 2 test. Kiểm khớp quy tắc nhận diện hành động của `ingest.adapt_trajectory` của họ trên cả 102 quỹ đạo của pool A.
  - Một lỗi đã sửa trước khi dùng: phần đầu gzip lưu tên file nên mã băm phụ thuộc đường dẫn. Đã bỏ tên khỏi phần đầu.
  - `w7_run_cell.py`:
    - kiểm loại notebook, ghim commit của XRepoSkill, kiểm sha256 của dữ liệu;
    - chạy `discover` theo khối và chặn chi bằng trường hợp xấu nhất (`max_tokens` 24.000 × giá niêm yết);
    - bản chạy thử thay `llm.chat` bằng hàm giả trả "không có quy tắc".
  - `w7_analyse.py` cùng 2 test. Tên trường đã đối chiếu với `score.py` (`lift`, `z`, `status`) và `audit.py` (`rule_id`, `flagged`).
- **Không chạy được mã của XRepoSkill trên máy của phiên:** lệnh cài bị chặn (18/11), nên ô Kaggle chưa được chạy thử trọn vẹn. Lượt chạy thử trên Kaggle là bước kiểm đầu tiên của nó.
- **Chạy thử miễn phí `lfnone` đạt** (run 44234926039, commit `e7985b3`, model giả lập, 1 task):
  - model `vertex_ai/gemini-3.8-flash`, seed 41, cost_limit 0,34, trần 3,827;
  - `leak_free` = true, `leak_free_check` = `commits=1 refs=1 remotes=0 objects_with_bug_msg=0`;
  - không có skill, 0 lỗi hạ tầng.
- **Ghi chú 45-1:** arm `lfnonerest` trong bước §34.
  - Kiểm `budget_usd` và `cost_limit` theo `configs/w7b.json` (khóa `cap_<arm>`); `--skip-done` trỏ tới `results/s34_lfnone.json`.
  - `bash -n` đạt. Chạy thử miễn phí trước khi chi.
- **Chạy thử miễn phí `lfnonerest` đạt.** Task được chọn không thuộc 17 task của `s34_lfnone`; `leak_free_check` đúng; trần 4,386; cost_limit 0,34. Lượt có phí được khởi động sau đó.

## R-81. `scripts/split_identity.py` (18/11/2026; 0 USD; phân tích trên dữ liệu đã có)

- **Mục đích:** cổng của X1′ (`docs/plan_vs_review.md` mục 10): mọi mã task mà log của một lượt học gskill nhắc tới phải thuộc train hoặc val của bản xuất trên `data-snapshots`.
- **Mã:** đọc lưu trữ bằng `tarfile`, không giải nén ra đĩa; chỉ đọc file log (`training.log`, `run_log.*`, `terminal.log`). Không có con số khoa học nào.
- **Test:** `tests/test_split_identity.py`, 2 test, đạt (một mã ở test, một mã lạ, log rỗng đều cho "không đạt"; đọc được cả `.jsonl` và `.jsonl.gz`).
- **Kết quả:** đạt ở cả ba lượt học đã có (Jinja gốc, Jinja một commit, Bleve gốc).

## R-82. §46 (X2′) và §47 (X1′): workflow, chốt chặn tiền, bộ chạy qua lớp `chroot` (18/11/2026; trước mọi lượt có phí)

- **Đối chiếu bản đăng ký:** §46, §47 commit `48190f6` trước mọi dòng mã của mục này. Trần từng khâu từ `configs/x1.json` (L66); trần cộng dồn 38,96 USD (`CLAUDE.md`).
- **Mã:**
  - `scripts/x1_budget.py`: cộng số đã chi của §46–§47 từ file đã publish (mỗi lượt học lấy `spent_total` lớn nhất của các nửa; mỗi file kết quả lấy `spent_usd`; bỏ `*.cost.json`). Từ chối khi đã chi + trần của khâu kế tiếp > 38,96. Test `tests/test_x1_budget.py`.
  - `scripts/x2_chroot_probe.py`: chạy `scripts/f1_probe.py` không sửa, chỉ trỏ lệnh `docker` của mini-swe-agent và Docker SDK của SWE-smith, gskill vào `chroot_shim` (commit ghim `0b9ea53`, kiểm sha256 của `chroot_shim.py` và `udocker_shim.py` trong workflow). Chạy bằng `sudo -E` vì cần `chroot` và `mknod`.
  - `pilot.yml`, plan `swesmith-x1`, bốn arm:
    - `x2`: hai nhánh nối tiếp (34 task không mô tả, môi trường gốc, seed 41);
    - `learnship`, `learnlf`: đúng lệnh của §25 bước 2 và §30, thẻ mới; nửa hai bị chặn nếu `num_candidates` ≤ 1 (thoát 9), nếu `split_identity.py` không đạt (thoát 8), hoặc nếu chốt tiền không cho (thoát 4);
    - `x1eval`: năm nhánh chạy song song trong một job (thay cho "hai job song song" của §47; vẫn cùng khoảng thời gian), skill phải trùng từng byte với bản sao trong `docs/skills/gskill/`.
  - Chạy thử (`dryrun = true`): model giả lập, tiền tố `dry`, không được cộng vào số đã chi.
- **Chạy thử miễn phí (18/11):**
  - `x2` (run 44282349106): đạt. Nền `chroot` dựng trên Actions từ image gốc (Python 3.10.16 ở đường dẫn của image; 959 nhánh task); kiểm sha256 của hai file shim đạt; hai nhánh chạy đủ; chốt tiền in đúng (0 đã chi, trần 0,664 rồi 1,199). Lộ lỗi A143 (`sudo` bỏ qua `-E`), đã sửa và thêm bước kiểm xác thực dưới quyền root; chạy thử lại sau khi sửa.
  - `learnship` nửa 1 (run 44282355273): đạt; file `dryx1ship_*` đã publish, không đụng file của §25, §30.
  - `x2` sau khi sửa A143 (run 44284213638): đạt; dòng kiểm in "root sees credentials: Credentials project set: True"; không còn cảnh báo của `sudo`.
  - `x1eval` (run 44284229151): đạt; năm nhánh, mỗi nhánh đúng `leak_free`, độ dài skill và tập task đã đăng ký; 0 lỗi hạ tầng.
  - `learnship` nửa 2 (run 44285918172, chạy lại sau A144): đạt; `split_identity` đạt trên log của nửa 1; tiếp tục từ thư mục của nửa 1. Cổng `num_candidates` bỏ qua ở lượt thử (model giả lập không sinh ứng viên), có hiệu lực ở lượt thật.
  - `learnlf` nửa 1 (run 44286802938, chạy lại sau A144): đạt; file `dryx1lf_*`.
- **Kết luận R-82:** mọi nhánh của §46–§47 đã chạy thử đạt. Lượt có phí chờ: (1) ngày 20/11 (@thuthuy); (2) @thuthuy cho biết trần 10 USD của project Vertex tính theo ngày hay theo tháng.


## R-83. Ghi chú 47-1 và 47-2: trần Vertex 20 rồi 25 USD; khâu chấm còn hai nhánh (18/11/2026; trước mọi lượt có phí)
- **Thay đổi:** `configs/x1.json` (`approved_total` 25,00; bốn khâu một commit có `"vertex": false`); `scripts/x1_caps.py` (mô phỏng cùng seed 4701 và cùng thứ tự; đã so từng trần riêng: không đổi); `pilot.yml` (chốt cộng dồn đọc `approved_total` thay vì số viết cứng; arm `learnlf` bị từ chối; `x1eval` chỉ chạy `ship_none`, `ship_skill`, chặn theo tổng trần 4,837 của các nhánh `score_` có `vertex` true).
- **Danh sách §4:** không còn số viết cứng ở hai nơi (L66: trần lấy từ một file); mọi nhánh bị bỏ khỏi Vertex vẫn được ghi, không xóa (R5); tổng các trần riêng 21,200 ≤ 25,00.
- **Chạy thử miễn phí** `x1eval` (run 44289845659, commit 3b924c7, lúc trần còn 20; số trần chỉ là giá trị đọc từ file nên 47-2 không đổi đường chạy): đạt. Chỉ hai file `dryx1eval_ship_{none,skill}` được ghi lại trên `pilot-snapshots` (commit d21cec2); mỗi file 2 task, `leak_free` false, skill 0 và 2.421 ký tự, trần 2,08 và 2,757, 0 lỗi hạ tầng.
- **Kết luận R-83:** đạt. Lượt có phí vẫn chờ 20/11 và chu kỳ trần 10 USD của project Vertex.

## R-84. Ghi chú 47-3: trần Vertex 35 USD, cả hai lượt học lại trên Vertex (18/11/2026; trước mọi lượt có phí)
- **Thay đổi:** `pilot.yml` trở về đúng mã đã chạy thử ở R-82 (commit f11b26a), chỉ khác: trần cộng dồn đọc từ `configs/x1.json` (`approved_total` 35,00) thay số viết cứng 38,96 (kiểm bằng `git diff f11b26a`: 4 dòng). `configs/x1.json`: mọi nhánh `"vertex": true`; trần riêng không đổi (so từng số với bản trước 47-1). §48 rút lại.
- **Danh sách §4:** chốt chặn tiền lấy từ một file (L66); biên trước khâu chấm được tính và ghi (35,00 − 10,491 − 24,106 = 0,403 USD) cùng hành động khi chạm (dừng, báo); không đổi thứ tự hay tính đồng thời của năm nhánh chấm (R5).
- **Chạy thử miễn phí, từng lượt một (L71):**
  - `x1eval` (run 44293902633): đạt; năm nhánh `dryx1eval_{ship_none, ship_skill, lf_none, lf_skill, lfskill_ship34}`, `leak_free` đúng từng nhánh, skill 0 hoặc 2.421 ký tự, trần 2,08 / 2,757 / 2,115 / 2,734 / 0,805, 0 lỗi hạ tầng (như R-82).
  - `learnlf` nửa 1 (run 44294779733): đạt; sổ chi `dryx1lf_learn_ledger_h1.json` giống hệt bản của R-82 (trần 14,5; 20 + 3 lệnh gọi giả lập).
- **Kết luận R-84:** đạt. Lượt có phí vẫn chờ 20/11 và chu kỳ trần 10 USD của project Vertex.

## R-85. Ô W7 (§45), bước kiểm trần sau lượt chạy thử pool A (18/11/2026; trước mọi lệnh gọi có phí của bộ học)
- **Đối tượng:** `kaggle/notebooks/w7_run_cell.py` commit `fa2c5f4` (nhánh mặc định); ghi chú 45-3.
- **Đã kiểm:**
  - Lượt chạy thử pool A: mọi bước chạy; 62 cặp trên 31 issue, đúng số đăng ký; 372 lệnh gọi giả lập = 62 × 3 × 2.
  - Mã XRepoSkill tại `26fd703` (chỉ đọc): `discover.py` `for attempt in range(retry_on_guard_reject + 1)`; `judge.py` `for _attempt in (1, 2)`; `merge.py` chia lô khi `finish_reason == "length"`; `llm.py` `call_with_retry(max_attempts=4)` với lỗi tạm thời.
  - Bước kiểm sau khi sửa: số lần hỏi lại đọc từ `configs/pipeline.yaml` lúc chạy; merge và judge được kiểm trước khi chạy; lệnh gọi thất bại tính theo mức xấu nhất (`litellm.failure_callback`).
  - Test `kaggle/tests/test_w7_cell_guard.py` (3 test, đạt); `ruff` đạt; preflight đạt.
- **Danh sách §4:** L66 (trần là chốt chặn, không phải dự toán); L69 (đủ mọi khâu); L72 (mọi lần gọi của mã bên thứ ba).
- **Giới hạn còn lại:** cận trên của merge (2 lệnh gọi mỗi ứng viên) là cận vận hành, không phải số đọc từ mã; chia lô đệ quy không có giới hạn trong mã. Bước kiểm vẫn dừng trước merge nếu cận đó vượt trần.
- **Kết luận R-85:** đạt. Khối đo chờ @thuthuy duyệt trần (xấu nhất 6,05 USD hạn mức).

## R-86. Ghi chú 47-4 (cảnh báo rủi ro) và 47-5 (bắt đầu 21/11) (18/11/2026; trước mọi lượt có phí)
- **Mã mới:** `scripts/x1_alerts.py` (A1–A5), test `tests/test_x1_alerts.py` (7 test: không cảnh báo khi sạch; A1, A2, A3; A4 ở đúng ranh 24,509; A5 cả hai chiều; tiền tố `dry` chỉ đọc file `dry` và bỏ A5; thư mục sau thắng; cảnh báo đã xác nhận không chặn). `configs/x1_ack.json` (rỗng). `pilot.yml`: gọi cảnh báo sau từng nhánh của `x2`, sau mỗi nửa học, sau khâu chấm; cảnh báo làm job thất bại với mã 10; tải thêm `best_skills.txt` của các lượt trước để A5 đọc ở khâu sau.
- **Danh sách §4:** ngưỡng của mỗi cảnh báo lấy từ số đã đăng ký hoặc suy ra (bảng ở ghi chú 47-4), không có số tự đặt (R2); không cảnh báo nào đổi quy tắc hay cách đọc (R5); hàm nhận con số khoa học không có giá trị mặc định (chỉ `--prefix` có mặc định là chuỗi rỗng).
- **Chạy thử miễn phí, từng lượt một (L71), commit 4ca58b0:** `x2` (run 44299442557): `dryx1_alerts_x2_none`, `dryx1_alerts_x2_skill` không cảnh báo; `x1eval` (run 44300585006): `dryx1_alerts_x1eval` không cảnh báo; `learnship` nửa 1 (run 44301759741): `dryx1_alerts_learnship-h1` không cảnh báo. Cả ba job đạt.
- **Kết luận R-86:** đạt. Lượt có phí đầu tiên không trước 21/11 (ghi chú 47-5) và chờ chu kỳ trần 10 USD của project.

## R-87. Ô W7 (§45), bước kiểm trần theo từng lệnh gọi (19/11/2026; trước mọi lệnh gọi có phí sau khối đo)
- **Đối tượng:** `kaggle/notebooks/w7_run_cell.py` commit `3e23bce` (nhánh mặc định); ghi chú 45-4.
- **Đã kiểm:**
  - Mã XRepoSkill tại `26fd703` (chỉ đọc): `llm.chat` gọi `litellm.completion` qua `call_with_retry` ở thời điểm gọi, nên bọc `litellm.completion` bắt được mọi lần thử, kể cả thử lại; `BudgetStop` không thuộc lỗi tạm thời nên không bị thử lại; discover bắt mọi ngoại lệ của từng lượt phân tích và ghi vào `failed.jsonl`, nên ô dựa vào cờ `stopped` (không dựa vào mã trả về) để hoàn tác khối.
  - Hoàn tác: xóa file mới, cắt file cũ về kích thước trước đơn vị, trên cả thư mục lượt chạy (ứng viên, transcript, `cost_log.jsonl`, `failed.jsonl`, đầu ra merge, judge).
  - Chi phí mỗi lệnh gọi tính ngay trong hàm bọc từ `usage` của lời đáp, không qua callback chạy sau, nên phần giữ chỗ chỉ được trả sau khi chi phí thật đã cộng.
  - Test `kaggle/tests/test_w7_cell_guard.py` (6 test) và mọi test của `kaggle/tests` đạt; `ruff` đạt; preflight đạt.
- **Danh sách §4:** L66, L69, L72, L74.
- **Giới hạn:** chế độ chạy thử dùng model giả lập ở `llm.chat`, nên không đi qua hàm bọc; hàm bọc chỉ được kiểm bằng test. Lượt có phí đầu tiên dùng nó là bước đo tiếp (trong trần 6,10).
- **Kết luận R-87:** đạt.

## R-88. Trần bước học W7 (§45, ghi chú 45-5; 19/11/2026; trước bước học đầy đủ)
- **Đối tượng:** `kaggle/scripts/w7_caps.py` (commit `cadacba` của nhánh mặc định); `kaggle/results/w7/w7_caps.json`.
- **Đã kiểm:**
  - Số đo đọc thẳng từ `cost_log.jsonl` của hai file zip; tổng discover 1,73796 USD theo giá niêm yết, khớp số ô báo (proxy) cho cùng các lệnh gọi; 15 ứng viên đếm từ thư mục `candidates/`.
  - Danh sách loại (`lookup`, `verification`, `replay`, `search_recipe`) và cỡ lô 32 đọc từ mã XRepoSkill tại `26fd703` (`schemas.py`, `configs/pipeline.yaml`).
  - Test: hàm khớp đường thẳng; mô phỏng tính đủ discover, merge và judge trên một ví dụ tính tay.
  - Hạn mức tháng sau khi cộng các trần: 82,7 ≤ 100.
- **Danh sách §4:** L66 (trần = phân vị + dự trữ), L69 (đủ mọi khâu), L72 (mọi lần gọi), L74 (chốt chặn từng lệnh gọi; cận so với số đo).
- **Giới hạn:** pool B chưa có số đo riêng; merge chỉ có 3 lệnh gọi đo được. Hai giả định này được bước kiểm theo từng lệnh gọi che: nếu trần không đủ, lượt dừng ở trần và chờ @thuthuy.
- **Kết luận R-88:** đạt.

## R-89. Phân tích C4′ (`kaggle/scripts/c4p_analyse.py`; 19/11/2026; trước khi đọc kết quả của Haiku)
- **Đối tượng:** script ở commit `45561e0` của nhánh mặc định; ghi chú 40-12 của `kaggle/preregistration_s40.md`.
- **Đã kiểm trước khi chạy trên dữ liệu thật:**
  - Đại lượng đúng 40-5: D = (Z_gốc − Z_một commit)/2, Z = fails(skill) − fails(none), fails = không giải theo S; cùng dấu với §33, §35 và `scripts/c10_stop_audit.py` (D < 0 là skill giúp nhiều hơn ở môi trường gốc).
  - E dùng `end_of_pool_log_e` (λ = 0,5, θ = 0), ngưỡng 120 = 3/α; test tính tay: hai task D = −0,5 cho E = 1,25².
  - Pool: 34 task test không mô tả lấy từ file kết quả §34 (34 mã, không trùng), cộng các task của khối extra (khối ≥ 10); chỉ lấy task đủ 4 nhánh và báo task thiếu.
  - Mẫu tải gói đúng chuỗi đã chốt ở 40-10.
- **Danh sách §4:** R5 (quy tắc chốt trước), L68 (mọi con số ghi chú chép từ đầu ra của lệnh).
- **Kết luận R-89:** đạt.

## R-90. Phân tích W7 pool B và đếm nội dung hậu kiểm (22/11/2026)
- **Đối tượng:** `kaggle/scripts/w7_analyse.py` (đã review cùng §45, không sửa) chạy với `--alpha 0.025 --min-issues-b 5` như đăng ký; script mới `kaggle/scripts/w7_content_posthoc.py` (commit `96ffde1`, nhánh mặc định).
- **Đã kiểm:**
  - Đại lượng chính là G theo §45 (A149: báo cáo trước đó ghi nhầm H); `reject_G` được đọc từ đầu ra, không tính tay.
  - Dữ liệu: pool A từ `w7_A_final_run.zip` (sha256 ở 45-9), pool B từ zip sha256 `a00aec3c…`; giải nén có kiểm đường dẫn; 24 cặp, 12 issue khớp lượt chạy thử.
  - Script hậu kiểm: ghi rõ trong docstring và trong JSON là không đăng ký; mẫu đặc điểm cố định trong file; bỏ `failed.jsonl`; chỉ đếm quy tắc mang G; test `kaggle/tests/test_w7_content_posthoc.py` (đếm mỗi issue một lần, bỏ quy tắc không mang G, bỏ file lỗi).
  - Câu kết luận chép nguyên văn ô "Không bác bỏ, A cao" của bảng diễn giải đặt trước (R5); kết quả hậu kiểm không thay câu này.
- **Danh sách §4:** R5, L68 (số chép từ đầu ra), L79 (chép định nghĩa đại lượng từ bản đăng ký).
- **Kết luận R-90:** đạt.

## R-91. Đưa X1′, X2′, C4′, §38/A′ và W7 vào bài (22/11/2026; @thuthuy: "Chỉnh sửa latex")
- **Đối tượng:** `scripts/make_numbers.py` (khối mới sau `ctrNoneMax`), `paper/main.tex`, các file kết quả chép sang `results/`.
- **Đã kiểm:**
  - Mọi số mới là macro sinh từ file kết quả; script dừng nếu số không khớp ghi chú đã đăng ký (47-8, 47-9, 40-27, 38-6, 38-11, 45-10) hay nếu quyết định khác (gpt-oss bác bỏ, nano và Haiku không, không model khác hãng nào qua Holm, W7 không bác bỏ).
  - Chạy lại `make_numbers.py` trước khi sửa cho `numbers.tex` giống hệt bản cũ; sau khi sửa, hai lần chạy cho cùng kết quả.
  - Câu chữ dùng đúng câu đã chốt ở `docs/reviewer_fidelity.md` (gpt-oss, XRepoSkill) và câu diễn giải đặt trước (38-9, 38-11, 45-10). Phần nội dung W7 ghi "read post hoc".
  - Đọc lại PDF và sửa bốn câu nói quá bằng chứng trước khi commit: "agents ... gain nothing" (chỉ đúng cho Haiku; Flash có skill 34 so với 31), "rerunning twice" (thực là hai lượt mỗi môi trường kể cả lượt gốc), "not the commit's name" (C10R: riêng diff cũng không tạo mức tăng), "with one commit ... downloaded" (16 task tính trên mọi nhánh).
  - Biên dịch: 0 tràn ngang; 9 trang kể cả tham khảo (nội dung khoảng 7,5 trang ≤ 10). Một cảnh báo tràn dọc 1,15pt ở trang tham khảo cuối.
- **Danh sách §4:** R2 (số có nguồn), R5, L58 (câu nhân quả có hai nhánh chỉ khác đúng nguyên nhân), L79 (diễn giải số theo câu của nguồn).
- **Kết luận R-91:** đạt.

## R-92. Đối chiếu bản review AI của paperreview.ai (22/11/2026; @thuthuy dán vào chat)
- **Bản review** do công cụ AI tạo, trên bản thảo ngày 22/11; khuyên nhận bài. Không thay bản review của thầy ngày 16/11.
- **Điểm review sai hoặc chưa chính xác (không sửa bài theo):**
  - "the deleted tests ... not separately varied except partially via C10": C10 giữ commit xóa test giống hệt ở bốn lịch sử, nên kênh này hoàn toàn không được thay đổi, không phải "một phần".
  - "a third [agent] resolves many tasks ... using history/testing channels": số liệu chỉ cho thấy Haiku tự đọc lịch sử; không có số nào trong bài về việc Haiku dùng test bị xóa.
  - "Reliance on proprietary models": từ bản 22/11 có một agent mã nguồn mở (gpt-oss) được chứng nhận.
- **Điểm đúng, đã sửa trong bài (0 USD, không đổi số):**
  - Câu hỏi 2 (metadata của C10): `scripts/history_variants.py` giữ nguyên tác giả, người commit, ngày giờ và thông điệp gốc trừ phần biến thể đổi; thêm câu này vào đoạn C10.
  - Câu hỏi 1 (commit xóa test): thêm câu nói rõ commit này giống hệt ở bốn lịch sử nên tự nó không tạo khác biệt, và việc bỏ nó chưa được thử.
  - Câu hỏi 10 (đối chứng chuẩn cho benchmark): thêm đoạn Discussion "A control for benchmarks built this way", dựa trên kiểm tra đã dùng ở lượt học lại và kết quả A′ (11/18).
- **Điểm đúng nhưng cần thí nghiệm hoặc nguồn mới (thuộc quyền @thuthuy hoặc R1; chưa làm):** bộ kiểm ngữ nghĩa độc lập (câu hỏi 5), nhiễu prompt cho GEPA (câu hỏi 8), biến thể bỏ commit xóa test (câu hỏi 1), các công trình liên quan reviewer nêu (STING, SWE-ABS, SWE-Explore, agentic shortcutting): chưa đọc bản gốc nên không trích dẫn.
- **Điểm đã có trong bài:** tỉ lệ bản vá đảo ngược (câu hỏi 4), so sánh cùng job S1 với J1 (câu hỏi 6), cổng hợp lệ trong vòng học vẫn nhận skill rò rỉ (câu hỏi 9).
- **Kết luận R-92:** đạt; bài 9 trang, 0 tràn ngang.

## R-93. X3′ (§49): bộ trace che mù và script phân tích (22/11/2026; trước khi có nhãn)
- **Đối tượng:** `scripts/x3_build.py`, `scripts/x3_analyse.py`, `tests/test_x3.py`, `results/x3_codes.json` (bảng mã; không đặt tên `*key*.json` vì quy tắc chặn khóa bí mật của `.gitignore`).
- **Đã kiểm:**
  - Tập trace: 104 = 25 + 9 + 34 + 36, đúng tầng mà `results/history_audit.json` dùng (cùng bộ lọc task không mô tả, bỏ lượt sập và lỗi hạ tầng).
  - Che mù: test xác nhận bộ trace không chứa `instance_id` hay tên nhóm; mã T001–T104 theo hoán vị cố định (seed 4901, số vận hành). Trang gán nhãn không chứa điểm S, L hay nhãn máy.
  - Phân tích: test tính tay ma trận 2 × 2, số đồng thuận, việc đếm "khôi phục và chạy test" vào Q3 của máy, và kiểm tra nhãn hợp lệ (Q4 = "na" đúng khi Q2 = "no"). Không có ngưỡng, không có khoảng tin cậy (toàn bộ tầng, không lấy mẫu).
- **Danh sách §4:** R5 (quy tắc trước dữ liệu), R6 (định nghĩa Q1–Q4 cố định), L58.
- **Kết luận R-93:** đạt.

## R-94. Kết quả X3′ vào bài (25/11/2026)
- **Đối tượng:** sửa `scripts/x3_analyse.py` (A151), `results/x3_labels.json`, `results/x3_analysis.json`, khối §49 trong `scripts/make_numbers.py` (macro `xh*`), đoạn "What the agent saw", bảng kê và Threats của `paper/main.tex`.
- **Đã kiểm:** nhãn xuất từ trang khớp CSV ở 104/104 mã; phân tích chạy đúng quy tắc §49, không đổi sau khi thấy số; câu trong bài theo câu đặt trước; `make_numbers.py` dừng nếu 104, 96, 52 khác hoặc các nhóm Q4 không cộng đủ 96; biên dịch 0 tràn ngang, 9 trang.
- **Danh sách §4:** R5, L79, L80.
- **Kết luận R-94:** đạt.

## R-95. Đối chiếu ba bản đánh giá AI ngày 25/11 (@thuthuy gửi): hai bản tiếng Việt và bản PDF của paperreview.ai
- **Bản PDF** trùng bản đã đối chiếu ở R-92; không có điểm mới.
- **Điểm sai, không sửa (kiểm trên PDF hiện tại):** Table 2 "đảo cột None/Skill" và "mất tiêu đề cột E" (ảnh trang 3: None 15, Skill 53, cột E có tiêu đề); "Rungit log", "thiếu τ", "thiếu ngoặc đóng ở câu R" (mã nguồn đúng; lỗi do công cụ trích chữ của bên review); `\mathbb{E}` "giống chữ B" (ký hiệu kỳ vọng chuẩn); Table 5 "ô trống" (các ô không áp dụng đã có "--"; ô trống duy nhất là dòng tiếp nối cùng mục đích).
- **Điểm chưa kiểm được, không làm theo:** chính sách tác quyền ACM "14/05/2026" yêu cầu khai báo AI trong Methods, và các con số về EasyChair, tỉ lệ nhận 27%: chưa đọc bản gốc (trang ACM bị chặn khi tải, A5a). Theo R1, không sửa bài theo các khẳng định này; chờ @thuthuy gửi bản chép trang chính sách.
- **Điểm đúng, đã sửa (0 USD):** tham khảo trùng (A152); tóm tắt nói quá ở seed thứ hai, câu "post hoc" lỗi thời, câu "chưa chạy Flash một commit" lỗi thời (A153); thêm giải thích vì sao phép so tương phản S3 ít power (hệ số cược 1 ± λ/2); thêm số nhánh A của C10R dùng test bị xóa (0/70); thêm khoảng chênh chroot − Docker 0,15 [−0,09; 0,38].
- **Điểm đúng nhưng cần quyết định hay việc khác:** URL gói tái lập ẩn danh (A4, Q6 chờ @thuthuy); kiểm định ngữ nghĩa độc lập (thí nghiệm mới, không khuyên); nhánh Flash có skill ở môi trường một commit (thí nghiệm mới, có phí).
- **Kiểm:** số mới là macro do `make_numbers.py` sinh và kiểm (12/34, 0, 0,15); biên dịch 0 tràn ngang, 9 trang, 40 tài liệu tham khảo; preflight thêm `[bib duplicates]`.
- **Kết luận R-95:** đạt.

## R-96. Đối chiếu ba bản đánh giá AI thứ hai ngày 25/11 (một bản tiếng Việt chấm "weak accept / major revision", một bản "4,0/5", một bản paperreview.ai mới)
- **Điểm sai (không sửa):**
  - "J1/J2 là hai run khác ngày": Table 1 ghi "2 runs, same day"; khác run thì đúng, và bài đã có S1/S2 cùng job (0,16).
  - "E của C10 phải là 1,25⁴⁰ ≈ 7,5×10³": 40 task âm gồm 39 task D = −1/2 và 1 task D = −1, nên E = 1,25³⁹ × 1,5 = 9,0×10³. Bài nay ghi rõ (macro `ctrACFull`, `make_numbers.py` kiểm E đúng dạng này).
  - "Giới hạn 0,042 chỉ nằm ở Threats": nằm ở mục 3; nay thêm câu nói rõ 0,042 là sai số của T2, còn T1 giữ được cận của mệnh đề.
  - "Table 1 thiếu cột registered/post hoc": đã có cột Analysis.
  - "Bản review 3,5 nói end-of-pool post hoc": đã sửa ở R-95 (C10, V1–V3 đăng ký trước).
- **Điểm đúng, đã sửa (0 USD):** tóm tắt nói test C xác nhận "it" → "the dependence there" (C chỉ trên task không mô tả, xác nhận cơ chế, không xác nhận tỉ trọng); đoạn phần còn lại nói rõ đó là phần còn lại khi bỏ hai commit này, chưa phải phần chứng minh thuộc về skill; trích dẫn placebo và mục Holm (A155); khóa tham khảo gõ tay (A154 đóng).
- **Điểm đúng nhưng cần quyết định của @thuthuy:** tên bài (Q3: nhân cách hóa "The Learner", phạm vi "a published learner"); người gán nhãn thứ hai cho X3′ (0 USD, cần một người); thí nghiệm mới (lặp thêm lượt học, tắt mạng, kiểm ngữ nghĩa, bỏ commit xóa test): không khuyên trước khi nộp; rút gọn mục 4.7 và 3: bài còn 1,5 trang trống, không bắt buộc.
- **Chưa kiểm được:** ProdCodeBench, DDBENCH, SkillOpt, SkillMorph, CASD (chưa đọc bản gốc, R1).
- **Kiểm:** `make_bib.py` 40 mục, 0 VERIFY; `make_numbers.py` kiểm E của A − C; biên dịch 0 tràn ngang, 9 trang.
- **Kết luận R-96:** đạt.

## R-97. Đối chiếu ba bản đánh giá AI thứ ba ngày 25/11 (mô phỏng hội đồng "+1,33"; bản "4,0/5"; bản "weak accept / major revision" đọc lại bản sửa)
- **Tài liệu đã tải (R1):** chuẩn IRR và chuẩn Benchmarking của ACM SIGSOFT Empirical Standards (`sigsoft_irr_supplement`, `sigsoft_benchmarking_standard`, workflow `sources` run 45597581868); CFP EASE 2027 tải lại với từ khóa mới. Trang chính sách tác quyền ACM vẫn 403 từ runner; `conf.researchr.org`, `www.acm.org`, `acmsigsoft.github.io` bị chặn trong phiên.
- **Điểm sai (không sửa):**
  - Table 2 "đảo cột ở 8/10 hàng", "thiếu tiêu đề cột E"; "Rungit", "thiếu τ", "dính chữ chú thích a82/b79", "acceptance. py": kiểm trên PDF (ảnh trang 3, `pdftotext`), đều không có; là lỗi trích chữ của bên review (chữ mũ dính vào số, từ dính khi trích).
  - Bảng 5 "gộp nhầm ô giữa Gatekeeper và end-of-pool": mã nguồn hai dòng tách riêng; "--" nay có chú thích.
  - "EASE 2027 không có vòng rebuttal", "tỉ lệ nhận 27%", "chính sách ACM 14/05/2026 bắt buộc khai báo AI trong Methods": CFP tải lại không có chữ "rebuttal", "generative", "acceptance"; chính sách ACM chưa đọc được. Không sửa bài theo các khẳng định chưa kiểm được.
  - "Chuẩn SIGSOFT coi IRR là thuộc tính thiết yếu, một người gán là chưa đạt": chuẩn cho phép một người gán khi có lý do ("e.g. the ratings are uncontroversial") và coi là phê bình không hợp lệ "Criticizing use of a single rater when the data is such that there is no reason to suspect different raters would reach different conclusions". Đúng một phần: Q4 là phán đoán nên thiếu người thứ hai là giới hạn thật.
  - "Abstract thiếu khoảng tin cậy cho 0,17": tóm tắt đã có [0,06; 0,28].
  - "Chưa có bảng registered/post hoc": Table 1 có cột Analysis.
  - "Chuyển 4.7 sang phụ lục để gọn": CFP tính phụ lục vào 10 trang ("including all figures, tables, appendices"), nên không lợi trang.
- **Điểm đúng, đã sửa (0 USD):** lý do một người gán cho Q1–Q3 kèm trích chuẩn IRR, và giới hạn còn lại cho Q4; 45% ghi là ước lượng điểm, hiệu không được chứng nhận trên 100 task, phép thử đăng ký là C; kết luận thêm khoảng tin cậy và bỏ chữ "confirm" cho seed thứ hai; hai lượt học mỗi môi trường cho Fisher p = 1/6; R và S2 dưới ngưỡng 480; chú thích "--" ở Bảng 5; chi phí tái chứng nhận rút còn một câu.
- **Thuộc quyền @thuthuy:** tên bài (Q3); URL gói tái lập (Q6); người gán thứ hai cho Q4 (0 USD, cần một người); CCS Concepts (acmart báo bắt buộc với bài trên 2 trang; cần cây phân loại ACM CCS, trang ACM bị chặn); khai báo AI (cần bản chép chính sách ACM); thí nghiệm mới (placebo thứ hai, thăm dò kênh khác): không khuyên trước khi nộp.
- **Kiểm:** biên dịch 0 tràn ngang, 9 trang, 41 tài liệu tham khảo, `make_bib.py` 0 VERIFY; preflight.
- **Kết luận R-97:** đạt.

## R-98. Quy tắc viết bài cho EASE 2027 từ nguồn đã tải, và sửa bài theo quy tắc (25/11/2026; 0 USD)
- **Yêu cầu (@thuthuy):** "tìm tất cả thông báo liên quan tới EASE và đọc sau đó tạo thành 1 rule chuẩn mực để follow viết report"; "viết rule xong thì sửa bài theo rule".
- **Nguồn đã tải (R1):** workflow `sources`, các commit 79da304, 4ed96d1 và 52bc5d8.
  - Các trang EASE 2027: CFP Research Papers, trang chủ, track RNR. URL lấy từ chính các liên kết trong trang (`fetch_sources.py` nay ghi các liên kết khớp `link_keywords`), không đoán.
  - Chính sách Open Science của SIGSOFT.
  - Các chuẩn General, Benchmarking, Meta-Science, Simulation, cùng các phụ lục Open Science, Information Visualization, IRR, Registered Reports. Mỗi chuẩn được xét theo mục "Application" của chính nó.
  - Trang chính sách ACM về tác giả và AI vẫn trả về 403.
- **Sản phẩm:**
  - `docs/ease_writing_rules.md`: 69 quy tắc (đếm các mã E- ở §1–§8), mỗi quy tắc có câu nguyên văn và khóa nguồn, cùng bảng tình trạng §9.
  - Preflight [ease]: dòng `\documentclass` và `\acmConference` khớp CFP; Data Availability đặt sau Conclusion và trước tài liệu tham khảo; không có `\author`, `\affiliation`, `\email` hay `acks`; không viết "the author" ở số ít; không có cụm ngôi thứ nhất nói về công trình cũ; không có tên chủ repo. Chú thích LaTeX được bỏ qua, `\%` được giữ.
  - `scripts/ease_pdf_check.py`: đếm phần chính và số trang chỉ có tài liệu tham khảo. Trang bắt đầu REFERENCES được tính là phần chính, tức đếm theo hướng chặt. Kiểm thêm metadata Author.
  - `tests/test_ease_rules.py`: 6 test.
- **Sửa bài (A156, A157):**
  - Tóm tắt, phần mở đầu và kết luận: phần gain còn lại là gain khi không có hai commit, được các phép kiểm đã đăng ký nhận và được phép end-of-pool nhận khi đọc lại post hoc; đó không phải gain đã chứng minh đến từ skill. Lượt học lặp lại ghi "an observation, not a rate" và "agrees with it". Kết luận ghi "gskill's learner".
  - Gọi tên phương pháp theo Empirical Standards. Không thêm trích dẫn cho từng chuẩn: bản gốc không ghi năm, và nhiều mục không năm cùng nhãn làm hỏng kiểu ACM.
  - Lý do chọn repo, trích câu "we learn repository-specific skills for jinja and bleve" (`gskill`) và docstring của `train_optimize_anything.py`, nơi Pygments là ví dụ. Bài trích khóa `gskill_train_config`; đoạn trích chứa câu này nằm trong snapshot `gskill_seed_candidate` của cùng file. Preflight [bib duplicates] chặn việc trích cả hai khóa.
  - Giả định của sign test.
  - NumPy 2.4.6 với seed cố định, qua macro `\nsimNumpy` lấy từ `results/method_check.json`.
  - Chú thích bảng inventory: phân tích post hoc là thăm dò.
  - Chú thích hình paired gains: nêu thông điệp. Kiểm số: cận dưới của các nhánh một commit là 0,13, 0,09 và 0,09, đều lớn hơn 0.
  - Data Availability: chuỗi model, seed, hash, trace, và phần không phân phối lại kèm lý do. Đã kiểm từng mục với `build_replication_package.py` và `package_manifest.py`.
  - Use of AI Tools: "an author", việc gán nhãn, trách nhiệm của tác giả.
- **Tái lập mô phỏng:** `verify_methods.py` chạy lại với cùng seed cho `results/method_check.json` giống hệt bản cũ, chỉ thêm trường `environment`. `make_numbers.py` chỉ thêm đúng một macro.
- **Kiểm:**
  - Biên dịch: 0 tràn ngang, 9 trang (phần chính tới trang 8, 1 trang tài liệu tham khảo), 41 tài liệu tham khảo, `make_bib.py` 0 VERIFY.
  - `ease_pdf_check.py` đạt.
  - `check_anonymity.py` trên `paper/` chỉ báo URL tài khoản của các công trình bên thứ ba trong tài liệu tham khảo, không có danh tính của ta.
  - Preflight đạt.
- **Còn chờ @thuthuy:**
  - Kho lưu trữ và giấy phép của gói (E-A4, E-O3, E-O4; Q6).
  - Bản chép chính sách ACM về AI (E-AI1).
  - Tên bài (Q3).
  - CCS Concepts: cần cây phân loại ACM.
- **Kết luận R-98:** đạt.

## R-99. Chọn phương án tốt nhất cho các mục còn chờ của EASE (25/11/2026; 0 USD)
- **Yêu cầu (@thuthuy):** "chọn điều tốt nhất để lọt vào ease mà không bị trừ điểm gì". Đây là ủy quyền cho các mục Q3 (tên bài) và Q6 (nơi đặt gói, giấy phép). Riêng việc tải gói lên mạng vẫn cần tài khoản của @thuthuy.
- **Nguồn mới (workflow `sources`, commit ee81dc2):**
  - Tải được: `sigcse_2027_ai_policy`, `sigchi_acm_ai_policy_guidance`, `disclose_data_dbr_howto`.
  - Bị 403: `acm_ccs2012` (bản lưu trữ lỗi SSL) và `acm_publications_faq`.
  - URL lấy từ kết quả tìm kiếm web hoặc từ liên kết trong chính sách SIGSOFT, không đoán.
- **Quyết định và lý do:**
  1. **Khai báo AI (A158):** mô tả chi tiết trong mục Setting, theo câu ACM được trích nguyên văn ở trang SIGCSE 2027. Vẫn khai báo việc hỗ trợ viết, vì cách đó đúng với cả bản chính sách cũ và mới.
  2. **Mẫu ACM (A159):** bỏ ba lệnh tắt phần tử bắt buộc; thêm CCS và `\Description`.
     - Hai khái niệm CCS lấy nguyên văn từ `continuous_skill_eval_2026`, một bài cùng chủ đề trình bày theo mẫu ACM.
     - Mức ưu tiên dùng mặc định của acmart, không đặt con số.
  3. **Tên bài:** "A Published Skill Learner Found the Leak: Controls for Evaluating Learned Coding-Agent Skills".
     - Ứng với điểm M3 của review 1: claim chỉ cho một learner, khớp Threats.
     - Bỏ "Certifying" theo lời khuyên Q3 từ trước.
  4. **Gói:** figshare với link riêng tư ẩn danh.
     - Đây là phương án trội so với Zenodo. Theo hướng dẫn mà chính sách SIGSOFT dẫn tới, Zenodo chỉ ẩn danh được khi công bố công khai ngay ("the file will be publicly accessible and indexed in Zenodo"). figshare cho link riêng tư trong lúc review, rồi công bố có DOI khi bài được nhận. Cả hai đều được chính sách SIGSOFT chấp nhận là kho lưu trữ.
     - Giấy phép: CC-BY 4.0 cho dữ liệu và tài liệu, MIT cho mã. Cả hai thuộc các ví dụ của chính sách SIGSOFT.
     - Văn bản MIT chép nguyên văn từ file LICENSE của một gói MIT đã cài. Tên chủ bản quyền để ẩn danh.
     - Nội dung bên thứ ba trong trace giữ giấy phép gốc.
- **Mã:**
  - `ease_pdf_check.py`: thêm E-F9 (cảnh báo "mandatory" trong log) và E-A4 (link còn là placeholder; chuẩn hóa gạch và khoảng trắng vì `pdftotext` bỏ gạch ở chỗ ngắt dòng, lỗi này bắt được khi chạy thử).
  - `build_replication_package.py`: ghi `LICENSE` và `LICENSE-DATA.md`.
  - Test: 8 trong `tests/test_ease_rules.py`.
- **Kiểm:**
  - Biên dịch: 0 tràn ngang; log không còn cảnh báo nào của acmart; phần chính tới trang 9.
  - `ease_pdf_check.py` chỉ còn lỗi E-A4. Lỗi này đúng như dự kiến: macro `\anonpackage` chờ link figshare.
  - Gói dựng thử: 2152 file, quét danh tính 0 chỗ lộ. `make_numbers.py` chạy trong gói cho `numbers.tex` giống hệt bản trong repo (F4).
  - Preflight đạt.
- **Còn lại cho @thuthuy:** tải `replication_package.zip` lên figshare theo `docs/figshare_upload.md`, rồi gửi link riêng tư để thay macro `\anonpackage`.
- **Kết luận R-99:** đạt.

## R-100. Phản biện ba bản review AI ngày 25/11 (bản "R1 +1, R2 0, R3 −1"; bản "+1.33"; bản "3.55/5") và sửa các điểm đúng (0 USD)
- **Cách kiểm:** mỗi khẳng định được đối chiếu với PDF (`pdftotext`, `pdfinfo`), mã nguồn `.tex`, danh sách repo của tài khoản (`list_repos`) và các nguồn đã tải (`docs/ease_writing_rules.md`).
- **Điểm sai, không sửa:**
  - "Table 2 đảo cột None/Skill ở 7/10 hàng; thiếu tiêu đề cột E": PDF in J1 None 15, Skill 53, và tiêu đề có 𝐸. Đây là lỗi trích chữ của bên review (lặp lại khẳng định đã bác ở R-97).
  - "Rungit", "𝔹[Z_i|C]", "mất τ": PDF in "Run git log -n 5", "E[𝑍𝑖 | 𝐶]", "Kendall's 𝜏".
  - "Chính sách ACM cập nhật 14/05/2026", "tỉ lệ nhận khoảng 27%", "mời viết cho số đặc biệt EMSE", "thang EasyChair −3..+3": không có trong CFP hay các nguồn đã tải. Không dùng.
  - "Rút gọn mục 3, chuyển Proposition sang gói": giữ nguyên. Mục 3 là đóng góp 4 (chứng nhận này bao phủ những gì), và bài đã viết "We claim no new method".
  - "Novelty hẹp vì Kozyrev et al. đã xóa .git": Related Work đã nêu khác biệt (họ dựng sẵn môi trường không có `.git`; ta đo phần gain do lịch sử đóng góp, và learner tự viết chỉ dẫn).
  - "Nhiều tài liệu là blog hay GitHub issue": các báo cáo rò rỉ lịch sử git được công bố dưới dạng issue. Đây là giới hạn vốn có của nguồn, không phải lỗi trích dẫn.
- **Điểm đúng, đã sửa:**
  1. **Năm 2026 trên khối ACM Reference và ô bản quyền:** thêm `\acmYear{2027}`, `\copyrightyear{2027}` (A160).
  2. **Tên "Gatekeeper" làm lộ tác giả:** `list_repos` cho thấy repo `-gatekeeper-p6` để công khai. Bài nay gọi là "the registered e-process". Preflight [ease] chặn tên repo trong bài. Gói tái lập đổi tên sang `evalgate` trong 157 file và cả file `.gz`; dựng lại: 0 chỗ còn tên cũ, `numbers.tex` giống hệt, test đạt (A160).
  3. **Bốn RQ tường minh** ở phần mở đầu, mỗi RQ trỏ tới mục trả lời nó (E-G1).
  4. **Tóm tắt từ 335 xuống 256 từ**, đưa kết quả cùng job và đã đăng ký lên trước:
     - C cho 36 so với 0; C10 cần mã trước khi có lỗi;
     - con số trên 100 task ghi "arms in different runs";
     - phần gain còn lại: "passes the registered tests and, read post hoc, an end-of-pool test".
  5. **Họ phép kiểm:** một đoạn ở mục 3 nêu C10 là một phép kiểm (ngưỡng 40), V1–V3 là một họ ba phép (120), 12 quyết định là một họ (480), và không có hiệu chỉnh xuyên thí nghiệm.
  6. **Phát hiện về scorer L** (no-op qua 206/216) đưa vào danh sách đóng góp.
  7. **Một người gán nhãn:** ghi ngay cạnh con số "relied on the diff".
  8. **Bảng 2:** chú thích rằng ở hàng P cột "None" là nhánh placebo; thêm khoảng cách sau chữ mũ a, b.
  9. **Bảng 5:** điền hai ô "Intended use" còn trống.
- **Thuộc quyền @thuthuy:**
  - Để repo `-gatekeeper-p6` ở chế độ private trong lúc review (tài khoản).
  - Tải gói lên figshare (Q6).
  - Người gán nhãn thứ hai cho Q4 (0 USD, cần một người).
  - Thí nghiệm mới (agent nền mạnh hơn, thêm lượt học): có phí, không khuyên làm trước khi nộp.
- **Kiểm:**
  - Biên dịch: 0 tràn ngang, không còn cảnh báo acmart; phần chính tới trang 9; PDF không còn chữ "Gatekeeper"; năm in là 2027.
  - `ease_pdf_check.py` chỉ còn E-A4 (link figshare).
  - Preflight đạt.
- **Kết luận R-100:** đạt.

## R-101. Phản biện ba bản review AI 25/11, lượt 2 (bản "+1/+1/0 khi giả định có gói"; bản Word "+2/+2/+2"; bản "3.6/5") và sửa các ý đúng (0 USD)
- **Cách kiểm:** đối chiếu với PDF (`pdftotext`), mã nguồn `.tex`, snapshot của các nguồn (`skill_issue_2026`, `sskb_paper`) và `results/sskb_analysis.json`.
- **Ý sai, không sửa:**
  - "Bảng 2 đảo cột None/Skill; thiếu tiêu đề E", "𝔹[Z_i|C]", "mất τ", "Rungit": sai, bác lần thứ ba (R-97, R-100). PDF in J1 = 15, 53; có 𝐸; "E[𝑍𝑖 | 𝐶]"; "Kendall's 𝜏"; "Run git log -n 5".
  - "Bảng 3 ghi 5/34 thay vì 15/34": PDF in 15/34.
  - "Dòng 508 thiếu gạch ở -n 5", "dòng 653 thừa ngoặc ((E=0.03": PDF in "git log -n 5" và "(𝐸 = 0.03 on 54 tasks)".
  - "Tỉ lệ nhận 26,1% (ccfddl)", "thang EasyChair", "mời viết cho EMSE": không có trong nguồn đã tải; không dùng.
  - "Rút mục 3 còn một nửa, chuyển Proposition sang gói": giữ nguyên. Review 3 đánh giá Assumption 1 là rủi ro lớn nhất, nên mục này cần đủ chặt hơn là ngắn hơn. Đây cũng là đóng góp 4.
  - "Rút Bảng 1 còn 6–8 dòng": không rút, vì bảng là bản kê đầy đủ, phục vụ E-C4 (minh bạch) và E-R1 (đăng ký hay post hoc). Thay vào đó thêm cột RQ để mỗi thí nghiệm gắn với một câu hỏi.
  - "Thêm báo cáo tunix #3017": tìm web không ra nguồn nào. Theo R1 không thêm; nếu @thuthuy có đường dẫn thì bổ sung.
- **Ý đúng, đã sửa (A161):**
  1. Câu trích Kozyrev et al. nay giữ nghĩa gốc (quá khớp vào các PR huấn luyện), cùng một câu nêu khác biệt với bài này.
  2. Related Work chia thành ba đoạn: skill học được; rò rỉ và scorer yếu, kèm các bản vá đã có; cổng thống kê. Nêu khác biệt: các công trình trước nghiên cứu agent tìm ra rò rỉ trong một lần đánh giá, còn bài này nghiên cứu learner viết rò rỉ vào một văn bản được dùng lại.
  3. Discussion thêm đoạn "After the benchmark is fixed", trả lời câu hỏi "benchmark đã vá thì bài học còn lại là gì".
  4. Mục 4.1: "nine skill admissions and the contrast C". Mục 4.5: J2 và B2 đạt cả ngưỡng họ 480, S2 thì không.
  5. Mục 3: định nghĩa c tại chỗ; nguồn của 0.109; một câu nói Assumption 1 cho phép gì và loại trừ gì.
  6. Bảng 1 thêm cột RQ.
- **Ý đúng nhưng cần người hoặc tiền (thuộc quyền @thuthuy):**
  - Người gán nhãn thứ hai cho Q4 và hệ số κ.
  - Kiểm ngữ nghĩa thủ công trên khoảng 20 bản vá của J2.
  - Biến thể C10 bỏ commit "Remove F2P Tests" (có phí).
  - Thêm repo hoặc agent nền mạnh hơn (có phí).
- **Kiểm:** biên dịch 0 tràn ngang, không còn cảnh báo acmart; phần chính tới trang 9, tài liệu tham khảo trang 10. `ease_pdf_check.py` chỉ còn E-A4. Preflight đạt.
- **Kết luận R-101:** đạt.

## R-102 (trước khi chạy). Phân tích độ nhạy của phép end-of-pool khi các task phụ thuộc nhau (0 USD, chỉ mô phỏng)
- **Vì sao:** cả hai review lượt 3 (25/11) và các lượt trước đều coi Assumption 1 là rủi ro lớn nhất. Giả định này không kiểm được trên dữ liệu. Simulation Standard (E-S) và General Standard ("discusses study's realism, assumptions and sensitivity of the results") yêu cầu báo cáo độ nhạy.
- **Thiết kế, chốt trong `scripts/dependence_sensitivity.py` trước khi chạy:**
  - Ba kịch bản phụ thuộc theo thứ tự chạy:
    - (a) AR(1) trong từng nhánh;
    - (b) AR(1) chung cho cả hai nhánh;
    - (c) sự cố làm hỏng L task liên tiếp với xác suất 1/2 ở mỗi nhánh. Kịch bản này thuộc trạng thái chạy C, nên được báo như sai số của T2.
  - Lưới: ρ ∈ {0,2; 0,5; 0,8}, L ∈ {5; 10; 20}. Đây là lưới độ nhạy, không phải ngưỡng; mọi ô đều được báo cáo.
  - Hai giả thuyết không giống mô phỏng của mục 3: đồng nhất, và ±0,3 dịch về trung bình 0.
  - 12.000 lần lặp mỗi ô (MCSE khoảng 0,0014), seed 20261125, tỉ lệ nền của 100 task Jinja.
  - Copula Gauss giữ đúng tỉ lệ giải của từng task (có test).
- **Cách báo cáo:** tỉ lệ chứng nhận sai lớn nhất của từng kịch bản, so với α = 0,025, cho cả phép end-of-pool và sign test, ghi đúng như kết quả ra.

## R-102 (kết quả) và R-103. Phân tích độ nhạy đã chạy; phản biện hai bản review AI lượt 3 (25/11) và sửa các ý đúng (0 USD)
- **Kết quả R-102** (`results/dependence_sensitivity.json`, chạy sau commit f54122a; báo đủ mọi ô):
  - Độc lập: phép end-of-pool ≤ 0,0008.
  - AR(1) trong từng nhánh: ρ = 0,2 cho 0,0018 và 0,0010; ρ = 0,5 cho 0,0037 và 0,0043; ρ = 0,8 cho 0,0187 và **0,0276**.
  - AR(1) chung cho hai nhánh: ≤ 0,0027.
  - Sự cố L = 5, 10, 20: ≤ 0,0082.
  - Sign test đã đăng ký: 0,0638 ở ρ = 0,8 và 0,0335 ở L = 20.
  - MCSE khoảng 0,0014.
  - Diễn giải trong bài: phép end-of-pool bền hơn sign test với dạng vi phạm này; chỉ tương quan mạnh trong một nhánh mới đưa nó tới mức α. Các macro in 4 chữ số để không làm tròn 0,0276 thành 0,03.
- **Phản biện:**
  - "Mục 4.7 là phần mới bổ sung" (review 2): không đúng, mục này đã có từ các bản trước. Không ảnh hưởng gì.
  - "Rút Bảng 1 còn 8 dòng, chuyển phần còn lại sang gói" và "rút mục 3 còn một nửa" (review 1): giữ nguyên, lý do như ở R-101. Bảng 1 là bản kê đăng ký và post hoc, phục vụ E-C4 và E-R1. Mục 3 nay còn mang thêm phân tích độ nhạy mà review 2 yêu cầu, tức đúng phần mà hai review coi là rủi ro lớn nhất.
  - "Kiểm ngữ nghĩa độc lập": cần người; thuộc quyền @thuthuy (như R-101).
- **Ý đúng, đã sửa:**
  1. **Bảo vệ Assumption 1** (review 2, ưu tiên 1): mục 3 thêm đoạn "Sensitivity to dependence between tasks" với kết quả trên.
  2. **Hình tổng quan thiết kế** (review 1, ưu tiên 1): Hình 1 nối môi trường, learner, skill, agent, scorer và quyết định, gắn RQ1–RQ4. Đã sửa một mũi tên cắt ngang hộp scorer, phát hiện khi xem ảnh dựng.
  3. **Tóm tắt** từ 256 xuống khoảng 231 từ. Câu đầu nói rõ gain là theo "the benchmark's tests" (review 2: "benchmark-resolved"). Giữ hai chữ giới hạn "arms in different runs" và "an observation, not a rate".
  4. Ký hiệu chỉ báo $\mathbb{1}$ in ra khó đọc (thấy trên ảnh trang 2), đổi sang $\mathbf{1}$.
- **Kiểm:**
  - Test mới 3 (`tests/test_dependence_sensitivity.py`): copula giữ đúng tỉ lệ giải, sự cố làm hỏng đúng L task liên tiếp.
  - Biên dịch: 0 tràn ngang; phần chính tới trang 9, tài liệu tham khảo trang 10.
  - `ease_pdf_check.py` chỉ còn E-A4.
  - Preflight đạt.
- **Kết luận R-103:** đạt.

## R-104. Phản biện hai bản review AI lượt 4 (25/11) và sửa các ý đúng (0 USD)
- **Ý đúng, đã sửa:**
  1. **Độ nhạy cho e-process tuần tự đã đăng ký** (review 2: phân tích độ nhạy "cho e-process"). Mô phỏng R-102 chỉ phủ phép end-of-pool và sign test.
     - Đã thêm e-process, tính trên đúng các mảng Z đã sinh, không rút thêm số ngẫu nhiên.
     - Các số cũ của R-102 giữ nguyên (đã kiểm từng ô).
     - Bản vector hóa khớp từng hàng với lớp `BettingEProcess` (test mới).
     - Kết quả: ≤ 0,0099 khi phụ thuộc vừa phải; 0,0291 ở ρ = 0,8 trong từng nhánh.
     - **R5:** đây là phần mở rộng sau khi đã thấy kết quả R-102. Docstring của script và mục này ghi rõ điều đó. Mở rộng này không đổi kịch bản, lưới hay seed nào.
  2. **Nhãn RQ4 trong Hình 1 nằm dưới hai ô** (review 1): nay ghi "RQ4 (scorer, rules)" và "RQ4 (what is certified)".
  3. **Bảng 1 nhóm theo RQ**, có đường kẻ giữa ba nhóm. Đây là phương án trội so với việc bỏ dòng: người đọc thấy mạch của bài mà bảng vẫn là bản kê đầy đủ.
- **Phản biện, giữ nguyên:**
  - "Rút Bảng 1 còn 8 dòng" (lần thứ ba): như R-101 và R-103; thay bằng nhóm theo RQ.
  - "Chuyển chứng minh Proposition 3.1 sang gói": chứng minh chỉ dài 4 dòng, nên chuyển đi gần như không tiết kiệm chỗ. Reviewer thống kê cần thấy nó trong bài, và chính review này cho Soundness lên 5 sau khi đọc mục 3.
  - Review 2 kể C, C10, các agent khác và mục 4.7 như phần "mới trong bản này": các phần này đã có từ trước. Không ảnh hưởng gì.
  - "Kiểm ngữ nghĩa độc lập", "người gán nhãn thứ hai": cần người, thuộc quyền @thuthuy (như R-101, R-103).
  - "Biến thể C10 bỏ Remove F2P Tests", "các kênh khác": đã nêu ở Threats; cần chi phí.
- **Kiểm:**
  - Test: 4 trong `tests/test_dependence_sensitivity.py`.
  - Biên dịch: 0 tràn ngang; phần chính tới trang 9.
  - `ease_pdf_check.py` chỉ còn E-A4.
  - Preflight đạt.
- **Kết luận R-104:** đạt.

## R-105. Phản biện bản review AI (Gemini, 25/11); sửa các ý đúng sau khi @thuthuy đồng ý; tài liệu đọc kèm cho reviewer (0 USD)
- **Đồng ý của @thuthuy:** "Ok, sau khi sửa cho tôi thêm 1 file word để reviewer ko còn review lệch". Đồng ý cho mục 1–4 của bản phân tích; không đổi tên L2, theo lời khuyên.
- **Ý sai, không sửa** (kiểm trên PDF và mã nguồn):
  - Bảng 5: 0.0032 lệch hàng. Sai: 0.0032 ở hàng "Registered e-process".
  - Bảng 1: hàng G ghi "same job (79/100)"; hàng H và X3 ghi "same job". Sai: G ghi "same job"; H, X3 ghi "–".
  - Bảng 2: đảo cột, thiếu tiêu đề E. Sai lần thứ năm.
  - "Rungit", τ, 𝔹, "Fix ix": lỗi trích chữ của bên review.
  - PACE trích ở mục 5: sai, đã trích ở mục 3.
  - URL của [2] bị cách: chỉ là xuống dòng.
  - [22], [27]: review không nêu lỗi cụ thể.
  - "CORE A", "26,1%", "không có rebuttal", "75–92%": không có trong nguồn đã tải.
- **Ý đúng, đã sửa (A162):**
  - [6] và [13]: escape `~`, `--`, backtick trong `make_bib.py`.
  - Bảng 3: chú thích c cho hàng A.
- **Waudby-Smith & Ramdas, bản JRSS B:** đã tải hai nguồn qua workflow `sources`:
  - trang arXiv abs: không có "Journal reference";
  - bản NSF PAR: chỉ ghi "To be read before The Royal Statistical Society … May 23rd, 2023".

  Chưa nguồn nào xác nhận tập, số, trang của bản đăng. Theo R1 giữ trích dẫn arXiv. Nếu @thuthuy có trang của tạp chí hoặc DOI thì sẽ đổi.
- **Tài liệu đọc kèm cho reviewer (file Word):**
  - `scripts/reviewer_guide_data.py` trích mọi bảng từ `main.tex` và thay macro bằng giá trị trong `numbers.tex`, tức đúng các số PDF in ra. Script dừng nếu còn macro chưa thay.
  - `scripts/reviewer_guide.js` dựng `reader_companion.docx` gồm: các lỗi trích chữ đã kiểm, ký hiệu, năm bảng dạng văn bản, kết quả chính kèm mục, phân biệt đăng ký và post hoc, những gì bài không khẳng định, và các sự thật về hội nghị đã đối chiếu CFP.
  - Đây là tài liệu nội bộ, **không nộp kèm bài**, vì không nằm trong giới hạn trang và không phải phần của bài.
- **Kiểm:**
  - Biên dịch: 0 tràn ngang; phần chính tới trang 9.
  - `ease_pdf_check.py` chỉ còn E-A4.
  - File Word chuyển sang PDF và được xem từng trang (4 trang).
  - Preflight đạt.
- **Kết luận R-105:** đạt.

## R-106. Phản biện bản review "cơ hội tại EASE 2027" (file .md) và bản Gemini lượt 2; sửa theo hướng tốt nhất; kế hoạch dự phòng (26/11/2026; 0 USD)
- **Quyết định của @thuthuy:** "Sửa theo hướng tốt nhất, tôi vẫn sẽ nộp vào EASE, các hướng khác thì tạo kế hoạch .md tính sau nếu hướng ưu tiên rớt".
- **Kiểm nguồn (commit nguồn trước khi dùng):**
  - Năm preprint mà review nêu đều có thật, đã tải qua workflow `sources`. Mỗi câu trích được đọc cùng đoạn bao quanh (L85).
  - Con số "33/38" mà review gán cho DeepSWE không có trong bản gốc, nên không dùng.
  - Trong CFP research track: special issue EMSE có; rebuttal và shepherding không được nhắc tới.
  - Ở RENE: chủ đề "contamination or leakage" và các mốc ngày đều có trong CFP.
- **Ý sai, không dùng:**
  - "Đã báo upstream SWE-smith #252": repo không có dấu vết nào.
  - "Up to 4×" (CAIS): trang ACM bị chặn, chưa kiểm được.
  - "ACM cập nhật chính sách tháng 6/2026": chưa kiểm được.
  - Xác suất nhận bài, base rate, phân tích từng thành viên PC: là suy luận.
  - Bản Gemini lượt 2 chấm trên PDF cũ: các ý trong đó đã được xử lý ở R-101 và R-105, hoặc đã bác.
- **Đã sửa trong bài:**
  1. **Related Work** trích và phân biệt với bốn bài:
     - BiPA: nhiễu chọn lọc, khác với gain thật nhưng đến từ rò rỉ; một phép replay kiểu A/A sẽ vẫn cho gain này qua.
     - Dissecting: chỉ dẫn do người viết.
     - Qwen3-Coder-Next: khai thác nằm trong trọng số RL.
     - DeepSWE: agent tìm ra rò rỉ trong một lần đánh giá.

     Thêm Agent Skill Evolution làm bằng chứng phụ rằng một rule thêm vào có tác dụng.
  2. **Phần mở đầu:** số gskill công bố (55→82, 24→93, gpt-5-mini), kèm câu "we do not test those numbers".
  3. **"Answer to RQ1–RQ4"** ở cuối các mục trả lời từng RQ. Mọi số trong các câu này là macro.
  4. **Khai báo AI:** một script sinh mọi con số từ dữ liệu thô, và chạy lại trong gói thì cho kết quả giống hệt (đã kiểm F4). Không viết rằng CI dựng lại số, vì workflow Paper chỉ dựng bảng và biên dịch.
  5. **Bib:** năm mục mới, tác giả và tiêu đề kiểm trên snapshot qua `bib_overrides` (0 VERIFY).
- **Kế hoạch dự phòng:** `docs/plan_fallback_venues.md`. Ghi rõ mục nào đã kiểm, mục nào chưa; RENE và Short Papers không dùng làm dự phòng được vì hạn trước 12/03.
- **Kiểm:**
  - Biên dịch: 0 tràn ngang; phần chính tới trang 9.
  - `ease_pdf_check.py` chỉ còn E-A4.
  - Preflight đạt.
- **Kết luận R-106:** đạt.

## R-107. Sửa theo bản review VALVE (đã duyệt) và phản biện bản review "Clear Accept sau đối chiếu định dạng" (26/11/2026; 0 USD)
- **Đã duyệt (@thuthuy: "Sửa theo hướng tốt nhất"):**
  - VALVE ở Related Work và trong Answer to RQ3, viết ở mức "consistent with ours"; không dùng số gain của VALVE, không khẳng định VALVE khai thác rò rỉ.
  - #252 ở mục Setting: mọi branch của ta kết thúc bằng Remove F2P Tests, nên không thuộc nhóm bị lỗi.
  - #256 ở Threats: lỗi này chỉ có thể làm giảm số task giải được, và chưa được đo trên các lượt của ta. Log SWE-smith không có trong `raw-archive`.
  - Trích "Coding or Cheating?" và "Shortcutting the Fix".
  - Sửa độ chính xác của câu Dissecting (hai model Qwen, ablation trên SWE-Bench Pro) và DeepSWE (phần audit SWE-Bench Pro).
- **Bản review "Clear Accept":**
  - **Đúng, đã sửa:**
    - Ký hiệu chồng nghĩa C, A, D (A163): bốn lịch sử của C10 đổi tên.
    - Cột b/c ở Bảng 2: macro sinh từ `s42_end_of_pool.json`; b − c = Skill − None ở cả 10 hàng.
    - Chú thích "--" của Bảng 5 trỏ tới mô phỏng ở mục 3.
    - UTBoost trích bản ACL 2025, Long Papers, trang 3762–3774, xác nhận trên PDF của ACL Anthology (`utboost_acl`).
  - **Không xác nhận được, giữ nguyên:**
    - PatchDiff "ICSE 2026" và SWE-bench-Live "NeurIPS 2025 D&B": trang arXiv không ghi venue.
    - Waudby-Smith "JRSS B": như R-105.
  - **Sai hoặc đã sửa từ trước:**
    - [13] ký tự `~`: đã sửa ở R-105; bên review dùng PDF cũ.
    - URL của [2] bị cách: chỉ là xuống dòng.
    - "Chính sách ACM 14/05/2026", tỉ lệ nhận 21–27%, xác suất 80–90%: không có trong nguồn đã tải.
    - Mười lỗi trích chữ mà bản review tự "giải oan": khớp với file đọc kèm R-105.
- **File Word đọc kèm:** thêm tên các lịch sử C10, cột b/c, và nghĩa của A và C.
- **Kiểm:**
  - Biên dịch: 0 tràn ngang. Có một tràn dọc 1,15pt khi dàn trang; không phải dòng chữ tràn lề, và CI chỉ kiểm tràn ngang.
  - Phần chính tới trang 10 (giới hạn 10); tài liệu tham khảo ở trang 10–11.
  - `ease_pdf_check.py` chỉ còn E-A4.
  - `make_bib.py` 0 VERIFY. Preflight đạt.
- **Kết luận R-107:** đạt.

## R-108. Phản biện hai bản review AI 26/11 (bản "+1/+1/+1, ~50%" và bản "Clear Accept +3/+2/+1"); sửa các ý đúng (0 USD)
- **Review 1, ý đúng và đã sửa (A164):**
  - **#256:** thay khẳng định chưa đo bằng phép đo (`scripts/apply_check.py`, có test). 1.092/1.092 patch không rỗng áp sạch bằng lệnh đầu tiên, nên chuỗi dự phòng không chạy; 0/952 patch rỗng được chấm giải được. Phép đo này cũng thay cho việc "chấm lại bằng chuỗi lệnh 6cd91d8" mà review đề nghị: khi chuỗi dự phòng không bao giờ chạy thì chuỗi đã sửa cho cùng kết quả.
  - **Dissecting:** bốn model Qwen (hình 57 của bản gốc).
  - **72.1%:** tỉ lệ trajectory, SWE-bench Multilingual có mạng, bản v2.
  - **Commit tổ tiên được coi là hợp lệ:** trích nguyên văn hai câu, "an ancestor of HEAD such as HEAD~1, this is ALLOWED" ([33]) và "honest work" ([22]). Commit mà skill đọc là cha của HEAD, nên các audit đó không bắt được nó. Luận điểm này tăng novelty.
- **Review 1, ý sai:**
  - "Thứ tự tác giả VALVE (Xiaomin Li đứng đầu)": PDF của VALVE ghi Yifan Wang đứng đầu, đúng như bib.
  - "Bài chưa nói đã đếm tip của từng branch": bài viết "We read every task branch … all 1086 have exactly three commits"; script là `history_audit.py` trong gói. Nay `apply_check.py` còn kiểm lại tip của từng branch được chấm.
- **Review 1, không làm được hoặc thuộc quyền @thuthuy:**
  - Bản ACM CAIS'26 của gskill: trang ACM trả về 403, không đọc được bản gốc, theo R1 giữ bản blog.
  - Responsible disclosure: việc ra bên ngoài; làm lúc này có nguy cơ lộ danh tính trong review ẩn danh.
  - Rút gọn mục 3 và Bảng 1: đã phản biện ba lần.
- **Review 2, ý đúng và đã sửa:**
  - **Ký hiệu $c$ chồng nghĩa** (A164, do chính R-101 đưa vào). Tỉ lệ cược không còn dùng ký hiệu.
  - **Ghi chú ở Bảng 1:** S1–S3, L2 không phải hai scorer S, L; mã C không phải trạng thái lượt chạy C.
  - **p của sign test cho R và S2** ($2.4\times10^{-4}$, $4.6\times10^{-4}$, macro). Câu trong bài nay nói rõ cả hai được phép thử đã đăng ký nhận nhưng thấp hơn ngưỡng 480.
- **Review 2, ý sai hoặc không xác nhận được:**
  - **"Từ mồ côi 'URL.' làm bài thành 11 trang":** không vi phạm. Phần chính kết thúc ở trang 10, trong giới hạn 10 trang; trang 11 chỉ có tài liệu tham khảo, CFP cho phép tới 2 trang như vậy. Sau lượt sửa này phần chính dài hơn vài dòng nhưng vẫn trong trang 10.
  - **"Bốn tài liệu đã có bản đăng":** Ahmed et al. (FSE Companion 2026) — trang arXiv không ghi venue. Wang et al. (ICSE 2026) và SWE-bench-Live (NeurIPS 2025) — đã kiểm ở R-107, không có. Waudby-Smith (JRSS B, DOI 10.1093/jrsssb/qkad009) — DOI trả về 403. Theo R1 giữ bản arXiv.
  - "Chính sách ACM 14/05/2026", tỉ lệ nhận 21,1%: không có trong nguồn đã tải.
  - Chấm điểm +3/+2/+1 hay xác suất: là phỏng đoán.
- **Kiểm:**
  - Biên dịch: 0 tràn ngang; phần chính tới trang 10; tài liệu tham khảo ở trang 10–11.
  - `ease_pdf_check.py` chỉ còn E-A4.
  - `make_numbers.py` chỉ thêm macro, không đổi số cũ.
  - Preflight đạt.
- **Kết luận R-108:** đạt.

## R-109. Link figshare vào bài (26/11/2026; 0 USD)
- **@thuthuy tải gói lên figshare** và gửi link riêng tư. Gói được dựng lại ngay trước đó từ commit cc3e64c; quét danh tính 0 chỗ lộ, không còn chữ "gatekeeper".
- **Trong bài:** macro `\anonpackage` nay là `https://figshare.com/s/70588a3513293ea61176`. Đã bỏ tham số `?file=…` để link trỏ tới cả item chứ không chỉ một file.
- **Kiểm:**
  - `ease_pdf_check.py` **PASS** toàn bộ: số trang, metadata Author rỗng, không còn cảnh báo "mandatory", không còn chỗ giữ chỗ.
  - 0 tràn ngang. Preflight đạt.
  - Việc mở link trong cửa sổ ẩn danh để thấy không lộ tên do @thuthuy kiểm, vì máy làm việc này không vào được figshare.
- **Lưu ý:** gói trên figshare ứng với bản bài lúc cc3e64c. Nếu bài còn đổi số liệu hay mã trước khi nộp, phải dựng lại gói và thay file trên cùng item. Link riêng tư giữ nguyên khi thay file.
- **Sự cố khi ghi sổ:** lần chạy đầu dừng ở bước sửa TODO (câu cần thay đã đổi từ R-106). Commit 3d… chỉ mang link và bảng quy tắc; TODO và mục này được bổ sung ở commit sau. Không ảnh hưởng gì tới bài.

