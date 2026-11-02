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
| C2 | Nhiễu giữa hai lần chạy cùng task là lớn (1/4 cặp lật kết quả ở lô đầu) | σ_S² lớn → cần nhiều trial; ước lượng từ đối chứng nhiễu ở B | dùng ≥ 3 seed mỗi cặp ở thí nghiệm chính |
| C3 | Agent dùng nhiều bước đọc lịch sử git | tốn chi phí; hành vi khác với người dùng thật | ghi nhận; không chặn (chặn là thay đổi harness) |
| C4 | Tỉ lệ giải ~75% (chỉ đo trên 4–8 task) | trần: skill chỉ có thể giúp trên ~25% task | đo lại ở B; nếu cao, chọn task khó hơn cho C/Phase 6 |
| C5 | Chi phí tính theo bảng giá LiteLLM, chưa đối chiếu hoá đơn Google | ngân sách lớn cần số thật | đối chiếu Billing Reports sau 24 giờ |
| C6 | Chạy local phụ thuộc container phiên này (key, Docker, đĩa) | máy bị thu hồi giữa chừng | chạy tiếp theo task đã có; lâu dài chuyển sang workflow GitHub (cần secrets) |
