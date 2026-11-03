# Rà soát lỗi tiềm ẩn của pipeline pilot (trước khi dùng ngân sách lớn)

Cập nhật 02/11/2026. Mỗi mục: đã xảy ra/được phát hiện thế nào → đã sửa chưa → kiểm chứng ở đâu.

## A. Lỗi đã sửa

| # | Lỗi | Ảnh hưởng nếu không sửa | Sửa | Kiểm chứng |
| --- | --- | --- | --- | --- |
| A1 | Lỗi hạ tầng khi tải image ở bước kiểm định pool bị tính là "gold không giải được" | 18/89 task tốt bị loại nhầm | tách `infra_error`, chạy lại 2 lần | run 41375243272: 86/89, 0 lỗi hạ tầng |
| A2 | Container của agent không khởi động (`docker run` exit 125, image chưa tải) bị tính là "agent không giải được" | nhánh không skill bị làm xấu, Z sai (lượt A1 đầu: Z = −0,33 giả) | tải image trước; trạng thái thoát không phải của agent → loại khỏi ghép cặp | `results/pilot/invalid/`; `tests/test_pilot.py::test_infra_failures_are_not_scored` |
| A3 | Bản sửa không rỗng nhưng harness không có report (lỗi hạ tầng phía chấm) bị tính là "không giải được" | như A2, ở bước chấm | chấm lại 1 lần, rồi loại (`HARNESS_INFRA`); patch rỗng vẫn tính là không giải được | `test_score_arm_rescores_and_flags_harness_infra` |
| A4 | `cost_limit` mỗi task không hiệu lực khi LiteLLM không biết giá model (chi phí = 0) | agent có thể chạy quá ngân sách | đăng ký giá với LiteLLM; `MSWEA_COST_TRACKING=default` | `test_cached_pricing_and_registry` |
| A5 | Mã model Pro `gemini-3.1-pro` không tồn tại trong bảng giá | gọi lỗi hoặc chi phí = 0 | `gemini-3.1-pro-preview`; đã gọi thử thành công | `results/pilot/smoke-flash-1.json` |
| A6 | Vertex: location `us-central1` trả 404 | không gọi được | `VERTEXAI_LOCATION=global` | gọi thử 3 model |
| A7 | Gemini Flash mặc định "thinking" tốn ~11× token output | đốt ngân sách | `reasoning_effort: low` cho Flash/Pro | đo trên prompt ngắn |
| A8 | LiteLLM cần `mcp` + `google-auth` cho tool-calling trên Vertex | agent không chạy (ModuleNotFoundError) | thêm vào cài đặt workflow trả phí | bài thử 0,26 USD |
| A9 | Đĩa đầy khi chạy cả pool (image 3,8–7,6 GB/task) | lỗi hạ tầng hàng loạt | chạy theo lô, dọn image sau mỗi lô, lô tự co theo dung lượng trống | `scripts/run_batched_pilot.py`, `tests/test_batched_pilot.py` |
| A10 | Chạy tiếp theo *tên lô* sai khi đổi kích thước lô | bỏ qua nhầm task / chạy trùng | chạy tiếp theo *tập task đã xong* | `test_resume_by_task_and_cap` |
| A11 | Đối chứng dương tính trung bình trên mọi task bị trần (agent đã giải ~75%) | báo "phép đo kém nhạy" sai → dừng oan | chỉ xét trên task nhánh không skill thất bại (≥ 5 task); sửa **trước** khi thấy kết quả B | `test_g1_decision_rules` |
| A12 | Lặp lại thí nghiệm với cùng seed có thể cho kết quả y hệt (Vertex tôn trọng `seed`) | "3 lần lặp" thực chất là 1 | `--model-seed` cho mỗi lần lặp; đối chứng nhiễu = seed + 1 | thử 4 lệnh gọi: cùng seed → giống hệt, khác seed → khác |
| A13 | Trần ngân sách chỉ theo từng lượt | tổng pilot có thể vượt 20 USD | trần **tích luỹ** đọc mọi file kết quả (kể cả lượt lỗi) trước mỗi lô | `test_cap_stops_before_overspending` |
| A14 | Vertex AI coi `seed=0` là **không đặt seed** (proto3 bỏ giá trị mặc định): hai lệnh gọi seed 0 khác nhau, hai lệnh gọi seed 1 giống hệt | giai đoạn B: nhánh không skill + đối chứng dương lấy mẫu ngẫu nhiên, đối chứng nhiễu lấy mẫu tất định → đối chứng nhiễu khác nhánh gốc về *cách lấy mẫu*; quy tắc G1 báo STOP (Z = −0,104, CI 90% [−0,19; −0,02]) | seed bắt đầu từ 1; `arm_config` từ chối seed 0; lượt B cách ly, chạy lại thành `g1-b2` | thử 6 lệnh gọi (02/11/2026); `test_seed_zero_is_rejected`; `results/pilot/invalid/README.md`. **Đính chính (rà soát sau B2):** lỗi API có thật nhưng chưa chứng minh là nguyên nhân STOP của B1; may rủi (p = 0,11) đủ giải thích — xem `docs/review_pilot_b.md` D3 |
| A15 | Trần tích luỹ cộng cả file phân tích (`g1_decision.json` có `spent_usd`) | đếm trùng 3,95 USD → dừng sớm oan | chỉ cộng file kết quả chạy (có `instances`, không `merged_from`) | `pilot_spent_total()` = 6,49 USD sau khi cách ly |
| A16 | File gộp các lô ghi `solved`/`scored` = 0 | bảng chi phí/tỉ lệ giải sai | `usage_summary` ghi `solved`/`scored`; `merge` cộng dồn | `tests/test_batched_pilot.py` |
| A17 | Docker Hub giới hạn pull ẩn danh (HTTP 429, ~100 lần/6 giờ/IP) | lần chạy lại B2 đầu: image không tải được → container không chạy → task bị driver coi là "xong" và bị bỏ qua khi chạy tiếp | image có sẵn thì không gọi registry; thiếu image → `run_pilot.py` thoát mã 75 **trước khi chạy agent**; driver chờ 30 phút rồi thử lại (tối đa 6 lần); **từ 02/11 tải qua `mirror.gcr.io`** (bộ đệm Docker Hub công khai của Google), gắn lại tên docker.io; digest trùng khớp (`sha256:4654890c…` cho sphinx-10673) | `test_registry_limit_waits_and_retries`, `test_pull_via_mirror_tags_docker_io_name` |
| A18 | Chạy tiếp coi task có lỗi hạ tầng ở một nhánh là "xong"; file gộp có thể chứa cặp trùng | mất task hoặc đếm một task hai lần | task có lỗi hạ tầng ở bất kỳ nhánh nào được chạy lại; khi gộp, lô sau thay thế dữ liệu của task đó | `test_infra_failed_tasks_are_rerun_and_replaced` |
| A19 | Quy tắc đối chứng dương của A11 (chỉ xét task nhánh gốc thất bại) **thiên lệch do hồi quy về trung bình**: chọn task theo chính lần chạy gốc thì *mọi* nhánh đều trông như "giúp" | ở `g1-b2`, đối chứng **nhiễu** đạt Z = −0,17 trên 20 task đó, còn tốt hơn đối chứng dương (−0,066) → quy tắc vừa có thể đạt oan vừa không đo đúng điều cần đo | **chưa sửa** (đổi quy tắc sau khi thấy dữ liệu thì không còn là quy tắc đặt trước); đề xuất: chọn task bằng một lần chạy độc lập (nhánh nhiễu), so đối chứng dương với nhánh gốc trên các task đó; hoặc so trực tiếp đối chứng dương với đối chứng nhiễu trên mọi task | `results/pilot/g1-b2.json`; phân tích trong `docs/budget_200.md` |
| A20 | Đĩa đầy khi tải image lớn (matplotlib ~10 GB vì có texlive) bị báo nhầm là "giới hạn registry" | driver chờ 30 phút rồi dừng vì "hết giờ", trong khi chờ không giúp gì | lỗi "no space left" được nhận riêng (mã 76): dọn image, chạy lại ngay với lô bằng một nửa | `test_prepull_reports_full_disk`, `test_full_disk_halves_the_batch` |
| A21 | Harness SWE-bench **bỏ qua** task đã có report dưới cùng `run_id` ("instances already run, skipping"). Chạy lại một lô bị ngắt dưới cùng tên thì có thể chấm patch MỚI bằng report CŨ | điểm không khớp với lần chạy agent | `run_id` riêng cho mỗi lần chấm (`scoring_run_id`) | Đã kiểm: **657/657** patch được chấm khớp với patch của agent, nên lỗi này **chưa từng xảy ra**; `test_scoring_run_id_is_unique_per_attempt` |
| A22 | **Trần 100 bước tương tác với skill**: ở bước xác nhận, nhánh skill chạm trần 16/96 lần, nhánh không skill 11/96 (trung vị 44,5 so với 40 bước). 6/9 cặp "hại" là do nhánh skill bị cắt ở 100 bước | ước lượng hiệu ứng bị kéo về phía "hại" vì một tham số vận hành thấp hơn mặc định của harness (250) | Không đổi phán quyết (đã khóa). Phân tích độ nhạy hậu kiểm, bỏ các cặp bị cắt: −0,011, CI [−0,091; +0,069], p = 0,39, vẫn FAIL. **Thí nghiệm chính:** step_limit 250 (mặc định), và đăng ký trước chiến lược cho biến cố xen giữa "bị cắt bởi trần bước" theo ICH E9(R1) | `docs/g1_verdict.md` §4 |
| A23 | Phân tích "split-half admission" trên SWE-Skills-Bench (`results/sskb_analysis.json`) gán nhãn harmful/beneficial bằng trung bình của **5 requirement giữ lại**. Độ tin cậy split-half của hiệu ứng skill gần 0 (r = 0,03 / −0,17), nên nhãn chủ yếu là nhiễu | các con số "harmful acceptance 30% / 19%" của bộ lọc ngây thơ **không diễn giải được** | **Thay** bằng phân tích sàng lọc rồi xác nhận (`scripts/sskb_screen_confirm.py`): đo hiệu ứng trên nửa giữ lại của các ô được nhận, không gán nhãn từng ô. Không dùng các tỉ lệ cũ trong paper | `results/sskb_screen_confirm.json` |

## B. Đã kiểm tra, không có lỗi

| # | Nghi vấn | Kết quả |
| --- | --- | --- |
| B1 | Image SWE-bench còn commit tương lai → agent đọc `git log` thấy lời giải | Không: `git rev-list --all --not HEAD` = 0; HEAD = commit gốc + 1 commit "SWE-bench" không đổi file (django-11333) |
| B2 | Hai nhánh của một cặp chạy khác task / khác image | Không: cùng hàng dataset, cùng image (digest ghi trong log), cùng seed |
| B3 | Key service account lọt vào repo | Không: `.gitignore` chặn `*key*.json`; kiểm `git diff --cached` không có "PRIVATE KEY" trước mỗi commit |
| B4 | `cost_limit` 0,10 USD cắt ngang agent Flash-Lite | Không: chi phí lớn nhất đo được 0,083–0,091 USD/lần (60 bước) |

## C. Còn mở — phải giải quyết trước thí nghiệm lớn (Phase 6)

| # | Vấn đề | Vì sao quan trọng | Đề xuất |
| --- | --- | --- | --- |
| C1 | Trần 60 bước đôi khi quyết định kết quả (astropy-13579: nhánh không skill giải ở bước 57, nhánh gợi ý chạm trần) | trần bước tạo nhiễu, có thể lệch giữa các nhánh nếu skill làm agent đi đường dài hơn | báo cáo tỉ lệ `LimitsExceeded` theo nhánh; thử 100 bước trên 10 task (rẻ với Flash-Lite) để xem hiệu ứng có đổi không |
| C2 | Nhiễu giữa hai lần chạy cùng task là lớn (1/4 cặp lật kết quả ở lô đầu) | σ_S² lớn → cần nhiều trial; ước lượng từ đối chứng nhiễu ở B | dùng ≥ 3 seed mỗi cặp ở thí nghiệm chính, **cách nhau ≥ 10** (1, 11, 21) để không trùng seed + 1 của đối chứng nhiễu; ước lượng σ_S² từ `g1-b2` |
| C3 | Agent dùng nhiều bước đọc lịch sử git | tốn chi phí; hành vi khác với người dùng thật | ghi nhận; không chặn (chặn là thay đổi harness) |
| C4 | Tỉ lệ giải ~75% (chỉ đo trên 4–8 task) | trần: skill chỉ có thể giúp trên ~25% task | đo lại ở B; nếu cao, chọn task khó hơn cho C/Phase 6 |
| C5 | Chi phí tính theo bảng giá LiteLLM, chưa đối chiếu hoá đơn Google | ngân sách lớn cần số thật | đối chiếu Billing Reports sau 24 giờ |
| C6 | Chạy local phụ thuộc container phiên này (key, Docker, đĩa, giới hạn pull Docker Hub theo IP) | máy bị thu hồi giữa chừng; giai đoạn C (86 image) chạm giới hạn 429 → chạy chậm | chạy tiếp theo task đã có, tự chờ khi bị 429 (A17); lâu dài chuyển sang workflow GitHub (cần secrets `GCP_SA_KEY`, `VERTEXAI_PROJECT`, `VERTEXAI_LOCATION`) |
