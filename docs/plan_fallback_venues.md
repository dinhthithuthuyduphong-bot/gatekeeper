# Kế hoạch dự phòng nếu bài bị từ chối ở EASE 2027 (lập 26/11/2026, R-106)

**Quyết định của @thuthuy (26/11):** "tôi vẫn sẽ nộp vào EASE, các hướng khác thì tạo kế hoạch .md tính sau nếu hướng ưu tiên rớt". Bài nộp **research track của EASE 2027**: tóm tắt 15/01/2027, bài 22/01/2027, thông báo kết quả 12/03/2027 (AoE).

Tài liệu này chỉ dùng **sau ngày 12/03/2027**, nếu bài bị từ chối. Chọn venue dự phòng là quyền của @thuthuy (mục 2 của "Quyền quyết định" trong CLAUDE.md). Tài liệu chỉ chuẩn bị thông tin để @thuthuy quyết nhanh.

## 1. Những gì đã kiểm trên nguồn gốc

| Sự thật | Nguồn (`configs/sources.json`) |
| --- | --- |
| Research track báo kết quả 12/03/2027 | `ease_2027_research_cfp` |
| Track RENE: tóm tắt 22/02/2027, bài 01/03/2027, kết quả 12/04/2027; chủ đề có "Benchmark and dataset contamination or leakage"; 10 trang cộng tối đa 2 trang chỉ chứa tài liệu tham khảo | `ease_2027_rnr_track` |
| Short Papers and Emerging Results: tóm tắt 01/03/2027 | `ease_2027_home` |
| Một số bài tốt nhất của research track được mời vào special issue của tạp chí Empirical Software Engineering (EMSE) | `ease_2027_research_cfp` |
| CFP research track không nhắc tới rebuttal hay shepherding | `ease_2027_research_cfp` (đã tìm từ khóa, không có) |

**Hệ quả:** hạn của RENE (01/03) và Short Papers (01/03) rơi **trước** ngày research track báo kết quả (12/03). Vì vậy hai track này không dùng làm dự phòng được, và cũng không nộp song song được (cùng một bài đang được review).

## 2. Các phương án dự phòng (phải kiểm lại CFP trước khi dùng)

Cột "Trạng thái" cho biết mục đó đã được kiểm trên bản gốc chưa. Các mục "chưa kiểm" lấy từ một bản review AI ngày 26/11. Theo R1, phải đưa CFP của venue vào `configs/sources.json`, chạy workflow `sources` và đọc bản gốc trước khi quyết.

| Venue | Hạn (theo review) | Trạng thái | Hợp với bài ở chỗ nào | Việc phải làm |
| --- | --- | --- | --- | --- |
| **EMSE (tạp chí)** | nộp bất kỳ lúc nào | chưa kiểm (chính sách, giới hạn độ dài) | Không bị giới hạn 10 trang, nên đưa lại được toàn bộ chi tiết (bảng kê đầy đủ, mô phỏng, phân tích độ nhạy, phụ lục chứng minh) | Viết bản mở rộng; kiểm chính sách về bài đã nộp hội nghị trước đó |
| **ESEM 2027** | dự kiến giữa tháng 5/2027 | chưa kiểm (chỉ biết lịch năm 2026 qua review) | Venue thực nghiệm, hợp với phần phương pháp và phần đăng ký trước | Kiểm CFP, mẫu định dạng, giới hạn trang, ẩn danh |
| **ICSE 2028, research track** | tóm tắt 24/06/2027, bài 01/07/2027 | chưa kiểm (nguồn thứ cấp) | Venue lớn; chuẩn novelty cao hơn | Kiểm CFP; định vị novelty kỹ hơn nữa so với BiPA, "Dissecting…", Qwen3-Coder-Next |
| **FSE 2028** | chưa công bố | chưa kiểm | như ICSE | Theo dõi CFP |
| **TOSEM (tạp chí)** | liên tục | chưa kiểm | như EMSE | Kiểm chính sách |
| EASE 2027 Posters and Vision | 16/03/2027 | chưa kiểm (trang chủ chỉ liệt kê tới 01/03) | Chỉ là bản rút gọn, không thay thế bài đầy đủ | Chỉ cân nhắc nếu muốn có mặt tại EASE 2027 |
| EASE 2027 AI Models / Data | 15/03/2027 | chưa kiểm | Chỉ hợp nếu tách bộ công cụ kiểm rò rỉ thành một hiện vật riêng | Như trên |
| ASE 2027 | 10/03/2027 | chưa kiểm | Hạn trước ngày 12/03, nên **không dùng được** | — |

## 3. Quy trình sau ngày 12/03/2027 (nếu bị từ chối)

1. **Đọc review thật** như mọi lượt review trước: kiểm từng ý trên PDF và nguồn. Ý đúng thì sửa và ghi R-xxx, A-xxx, L-xxx; ý sai thì phản biện kèm bằng chứng. Không sửa theo ý chưa kiểm.
2. **Phân loại lý do từ chối** để chọn hướng:
   - **Novelty** (reviewer cho rằng đã biết): ưu tiên tạp chí (EMSE, TOSEM), nơi có chỗ để phân biệt đầy đủ với các công trình gần.
   - **Trình bày hay độ dày**: tạp chí cũng là hướng hợp, vì có chỗ cho phụ lục.
   - **Phạm vi hẹp** (một benchmark, một learner): cần thêm thí nghiệm, tức có chi phí. Phải xin @thuthuy duyệt ngân sách trước, kèm ước tính.
   - **Thống kê** (Assumption 1, cách nhóm phép kiểm): sửa chữ và phân tích, 0 USD.
3. **Kiểm CFP của venue được chọn** qua workflow `sources`, rồi lập bảng quy tắc riêng theo mẫu `docs/ease_writing_rules.md`: định dạng, giới hạn trang, ẩn danh, chính sách AI, chính sách open science.
4. **Chuyển định dạng** nếu venue dùng mẫu khác (ví dụ IEEE). Bảng quy tắc của venue mới thay cho [ease] trong preflight.
5. **Gói tái lập:** dùng lại link figshare đã tạo cho EASE nếu venue mới chấp nhận cách đó. Trước khi công bố DOI, kiểm lại ẩn danh (`scripts/check_anonymity.py`).

## 4. Chuẩn bị ngay từ bây giờ (0 USD, không ảnh hưởng bài nộp EASE)

- Ghi lại trong tài liệu này mọi chi tiết đã cắt khỏi bài vì giới hạn trang, kèm vị trí trong repo, để bản mở rộng cho tạp chí dùng lại được.
- Theo dõi các preprint mới về rò rỉ trong benchmark và về tối ưu skill (kiểm lại arXiv cs.SE khoảng một tuần trước 22/01/2027). Công trình mới nào liên quan thì thêm vào nguồn và Related Work trước khi nộp.

**Chi tiết đã cắt hoặc chỉ có trong gói (cập nhật khi sửa bài):**
- Toàn bộ bản đăng ký trước và các ghi chú thực thi: `docs/preregistration_main.md`.
- Mô phỏng độ nhạy đầy đủ cho từng ô: `results/dependence_sensitivity.json`.
- Kiểm chứng phương pháp bằng mô phỏng: `results/method_check.json`, `docs/method_check.md`.
- Phân tích nội dung sau khi có dữ liệu của W7/L2: `results/w7_content_posthoc.json`.
