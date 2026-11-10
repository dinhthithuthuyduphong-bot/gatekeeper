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
