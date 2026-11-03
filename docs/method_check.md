# Kiểm định phương pháp bằng số (03/11/2026)

Câu hỏi của @thuthuy: các con số có **đáng tin** (tỉ lệ kết luận sai đúng như lý thuyết hứa) và có **tác dụng** (đủ sức phát hiện hiệu ứng có thật) không?

- **Mã:** `scripts/verify_methods.py`. **Kết quả:** `results/method_check.json`.
- **Phương pháp:** mô phỏng plasmode (Franklin et al. 2014). Tỉ lệ giải của từng task lấy từ nhánh không skill **đã đo** ở G1 (32 task × 3 seed). **Không dùng dữ liệu E1** (R5).
- **Hiệu ứng thử:** các mốc của SWE-Skills-Bench (0,02; 0,05; 0,109) và lớn hơn. Skill dịch tỉ lệ giải của mỗi task thêm δ, cắt trong [0, 1]. Hiệu ứng thực hiện được (`eff` trong bảng) nhỏ hơn δ, vì task đã giải chắc chắn thì không thể cải thiện.
- **Số lần lặp:** n_sim = 12.000 cho kiểm tính hợp lệ (sai số Monte Carlo < α′/10), n_sim = 2.500 cho power (sai số ≤ 0,01). Công thức sai số √(p(1−p)/n_sim): Morris, White & Crowther 2019, bảng chỉ số hiệu năng ("Rejection % (power or type I error)"); **đã đối chiếu bản gốc** (arXiv 1712.03198).
- **Kiểm plasmode:** tỉ lệ bất đồng P(Z = +1) trong mô phỏng là 0,055, nằm trong khoảng đã đo 0,04–0,08.
- **Kiểm phép tính:** kiểm định chính xác bằng tích chập trùng khớp với liệt kê đủ 2¹² cách đổi dấu, trên 50 bộ dữ liệu.
- **Lỗi tìm được trong chính script kiểm định khi review:** `rng.random((n, s)) < q` với q có dạng (n,) âm thầm tạo ra ma trận n × n khi s = 1. Đã sửa và thêm assert về kích thước (review R-6).

## 1. Đáng tin: tỉ lệ sai khi H₀ đúng (δ = 0)

| Thiết kế | Mức danh nghĩa | Kiểm định chính | Kết luận "vững" (chính + S1 + S2) | Đạt? |
| --- | --- | --- | --- | --- |
| E1 (n = 40, 3 seed, 8 repo, mức Holm đầu 0,025/3) | 0,0083 | 0,0012 | 0,0001 | ✅ (bảo thủ) |
| E2 (n = 119, 3 seed, 65 repo) | 0,025 | 0,0162 | 0,0135 | ✅ |
| A/A E1 (n = 40) | 0,05 | 0,0055 | – | ✅; tỉ lệ thực bằng 1/9 mức danh nghĩa (C9) |
| A/A E2 (n = 119) | 0,05 | 0,0233 | – | ✅ |
| Gatekeeper RQ1 (40 trial, α = 0,025/7, D2) với skill trung tính hoặc có hại (δ ≤ 0) | 0,0036 | 0 / 12.000 | – | ✅ |

**Kết luận:** mọi phương pháp đều **hợp lệ**: tỉ lệ sai ≤ mức danh nghĩa. Tỉ lệ thực thấp hơn mức danh nghĩa (0,0012 so với 0,0083; 0,016 so với 0,025) vì dữ liệu rời rạc: nhiều cặp Z = 0 không đóng góp vào phân phối đổi dấu.

## 2. Tác dụng: power

| δ (hiệu ứng thực hiện được) | E1 chính | E1 vững | E2 chính | E2 vững |
| --- | --- | --- | --- | --- |
| 0,02 (0,013) | 0,010 | 0,000 | 0,083 | 0,070 |
| 0,05 (0,031) | 0,044 | 0,001 | 0,360 | 0,317 |
| 0,109 (0,068) | 0,255 | 0,016 | **0,924** | **0,899** |
| 0,15 (0,094) | 0,475 | 0,050 | 0,993 | 0,992 |
| 0,20 (0,125) | 0,753 | 0,114 | 1,000 | 1,000 |
| 0,30 (0,187) | 0,980 | 0,307 | 1,000 | 1,000 |

**RQ1 (40 trial sàng lọc, 1 seed):** tỉ lệ được admit theo δ.

| δ | −0,20 | −0,10 | −0,05 | 0 | 0,05 | 0,109 | 0,20 | 0,30 | 0,40 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gatekeeper (α = 0,025/7, D2) | 0 | 0 | 0 | 0 | 0 | 0 | 0,0008 | 0,0048 | 0,0508 |
| Plug-in (trung bình < 0) | 0,014 | **0,100** | **0,211** | **0,402** | 0,624 | 0,849 | 0,963 | 0,996 | 1,000 |
| Gatekeeper, ô E2 (α = 0,05) | | | | 0 | | 0,007 | 0,072 | 0,317 | |
| Kiểm định chính xác, cỡ mẫu cố định, cùng dữ liệu, α = 0,05 (để so sánh) | | | | 0,009 | | 0,145 | 0,450 | 0,810 | |

## 3. Phát hiện

Cột **Hậu quả** dùng 3 loại được định nghĩa: **K1** = làm sai một con số hoặc kết luận đã báo cáo hay sẽ báo cáo; **K2** = không làm sai số, nhưng làm giảm power hoặc thu hẹp phạm vi kết luận; **K3** = chỉ ảnh hưởng tài liệu hoặc truy vết.

| # | Phát hiện | Hậu quả | Xử lý đề xuất (kèm cơ sở) |
| --- | --- | --- | --- |
| **A38** | **Power của E1 bị tính sai trong bản đăng ký trước.** n = 40 ra từ (z₁₋α′ + z₁₋β)²·V/δ² với α′ = 0,025, trong khi phân tích dùng Holm trên 3 skill (mức đầu 0,0083). Với α′ = 0,0083 thì công thức cho n ≈ 53 | K1: tuyên bố "power 80%" sai | **Đã sửa** (@thuthuy duyệt 80 USD): E1 mở rộng lên n = 53 (ghi chú thực thi 4), kết luận chính theo ICH E9(R1) (A39). **Căn cứ của n:** δ = 0,109 (phân vị 5% của SWE-Skills-Bench) và power 80% (quy ước Cohen) chỉ là **điểm tham chiếu quy ước**, không phải chứng minh. Căn cứ cuối cùng là **ràng buộc nguồn lực** đã duyệt (Lakens 2022, Table 1, đã đối chiếu bản gốc), kèm **đường cong power theo δ** (§2, §5) như Lakens khuyến nghị ("sensitivity power analysis") |
| **C8** | **RQ1 thu nhỏ không thể cho thấy độ phủ.** Với 40 trial, Gatekeeper admit với tỉ lệ 0,0048 khi δ = 0,3 và 0,0508 khi δ = 0,4. Điều này đã biết từ trước: bảng plasmode (`results/design_table_plasmode.json`, ở α = 0,025/K) cho thấy cần 216–470 trial ở δ = 0,109. Vì vậy RQ1 thu nhỏ chỉ kiểm được **một vế**: harmful acceptance (Gatekeeper 0 so với plug-in 10–21% ở δ = −0,10/−0,05). Vế clean-reuse coverage chắc chắn ≈ 0 | K2: RQ1 thu nhỏ chỉ trả lời được vế an toàn | (1) Báo cáo RQ1 thu nhỏ đúng phạm vi: chỉ vế an toàn. (2) Vế độ phủ cần ngân sách mỗi ô theo bảng plasmode; đó là việc của thí nghiệm chính. (3) Chi phí của tính hợp lệ mọi lúc so với kiểm định cỡ mẫu cố định (0,007 so với 0,145 ở δ = 0,109) là một **kết quả đo** cần báo cáo, không phải lỗi. Lý thuyết của đánh đổi này nằm trong Waudby-Smith & Ramdas 2024 và Grünwald et al. 2024 (GRO; c đã chọn bằng GRO, `results/gro_c.json`) |
| **C9** | A/A của E1 bảo thủ: tỉ lệ báo động 0,0055 ở mức 0,05. A/A đạt **không phải** bằng chứng pipeline sạch: với hiệu ứng nhiễu bằng 0 nó chỉ báo động 0,55% số lần | K2 | Đã có trong bản đăng ký trước: không bác bỏ ≠ tương đương (ICH E9). Báo cáo A/A kèm CI, không dùng như bằng chứng sạch |
| C7 | S2 với 8 repo (E1) | (đã ghi) | Như A38 |
| N3, N6, N7 | **Ba nguồn chưa xác nhận được từ bản gốc:** mốc cắt dữ liệu của Gemini (cả hai trang của Google tải được nhưng không ghi mốc); Steegen et al. 2016 (đa vũ trụ): chưa tải được. *(Sửa: McHugh 2012 **đã được xác nhận** từ trước, PMC3900052; bản tốt bị lỗi A44 ghi đè.)* | K3 (chưa dùng cho kết luận nào) | Không dùng cho tới khi xác nhận (R1). Steegen chỉ dùng để báo loss dạng đường cong, không quyết định nào phụ thuộc. McHugh chỉ dùng cho bước gán nhãn hai người, chưa làm. Mốc cắt: phân tích nhiễm dữ liệu E2 bị treo |
| **C10** | **Nhãn "có hại đã xác lập" của RQ1** (2 seed giữ lại, 40 task, α = 0,025/7) theo δ: tỉ lệ gán nhãn 0,006 / 0,049 / 0,299 / 0,743 / 0,934 ở δ = −0,05 / −0,109 / −0,20 / −0,30 / −0,40. Gán nhãn sai chiều: 0 (khi δ < 0); 0,0002 khi δ = 0 (n_sim = 12.000) | K2 | Một skill có hại chỉ được xác lập với xác suất ≥ 0,74 khi δ ≤ −0,30. Các ô không đạt được ghi là "chưa xác định" và báo cáo riêng (§6.1 bản đăng ký trước E1). Harmful acceptance chỉ tính trên các ô đã xác lập, và số ô đó được báo cáo cạnh tỉ lệ |
| – | Plasmode của E2 dùng tỉ lệ giải đo trên Verified; Live có thể khác | K2 | Sau seed đầu, đo lại tỉ lệ giải của Live và tính lại bảng E2 (không nhìn hiệu ứng) |

## 4. Tóm lại

- **Đáng tin:** mọi phép kiểm định đều giữ đúng tỉ lệ sai danh nghĩa trên dữ liệu mô phỏng từ số đo thật. Phép tính chính xác khớp với liệt kê đầy đủ.
- **Có tác dụng:**
  - **E2: có.** Power 0,90 ở hiệu ứng 0,068.
  - **E1: yếu.** Kết luận "vững" có power ≤ 0,11 ở hiệu ứng thực tế. Kiểm định chính có power 0,98 khi δ = 0,30, nhưng chỉ 0,26 ở δ = 0,109.
  - **RQ1 thu nhỏ: chỉ đo được vế an toàn**, không đo được độ phủ. Vế an toàn chỉ đo được trên các ô có hại đã xác lập: xác suất xác lập ≥ 0,74 khi δ ≤ −0,30 (C10).

## 5. Bản sửa (03/11/2026, yêu cầu của @thuthuy: sửa mọi lỗi làm nghiên cứu yếu đi hoặc làm số liệu sai)

Power của từng quy tắc quyết định ở E1 (plasmode, mức Holm đầu 0,0083, R = 2.000; tỉ lệ sai ở δ = 0 với n = 40, R = 6.000):

| δ | chính | chính + S1 | chính + S1 + S2 (đã đăng ký) |
| --- | --- | --- | --- |
| 0 (tỉ lệ sai) | 0,002 | 0,002 | 0,000 |
| 0,109 | 0,263 (n = 53: 0,370) | 0,262 | 0,018 (n = 53: 0,035) |
| 0,15 | 0,488 (n = 53: 0,657) | 0,488 | 0,057 (n = 53: 0,089) |
| 0,20 | 0,760 (n = 53: 0,901) | 0,760 | 0,117 (n = 53: 0,211) |

1. **A39, đã sửa:** quy tắc kết luận theo ICH E9(R1) (`verdict_ich_e9_r1`). Quy tắc đã đăng ký vẫn được báo cáo (sai lệch D1).
2. **A38, chờ @thuthuy duyệt ngân sách:** mở rộng E1 lên n = 53 mỗi skill, theo đúng thủ tục lấy mẫu đã đăng ký (53 task dùng được đầu tiên theo thứ tự ngẫu nhiên; 40 task đầu giữ nguyên).
   - Chi phí thêm: 32 task cho nhánh `none` + 39 lần chạy skill mỗi seed, tức 71 lần chạy × 3 seed × 0,0617 USD ≈ 13,1 USD (khoảng 213 lần chạy, ước 77M token input).
   - Cơ sở: công thức cỡ mẫu của chính bản đăng ký trước, ở mức Holm đúng.
   - Quyết định chỉ dựa vào lỗi thiết kế, phát hiện bằng mô phỏng trên dữ liệu G1. Kết quả E1 chưa được phân tích.
3. **C8:** RQ1 thu nhỏ được báo cáo đúng phạm vi (chỉ vế an toàn). Độ phủ cần 216–470 trial mỗi ô (α = 0,025/K, p₊ đo được 0,04–0,08, power 80% theo quy ước Cohen; quy ước này **đang chờ đối chiếu** qua Lakens 2022), là việc của thí nghiệm chính.
4. **Nguồn chưa xác nhận:** đã thêm URL chính thức thay thế (PMC cho McHugh; trang tổng quan model của Google; bản PDF của Steegen). Từ khóa "Sample Size Adjustment" được thêm cho ICH E9.

**Power của E2 trên đúng tập đã chốt** (`scripts/e2_power_final.py` → `results/e2_power_final.json`, A63). Dòng E2 ở trên dùng khối 1 (n = 119). Trên 121 task đã chốt, với cụm theo repo của chính tập đó:

| δ | n = 121 | n = 105 (nếu dừng vì ngân sách) |
| --- | --- | --- |
| 0,05 | 0,357 | 0,316 |
| 0,109 | 0,936 | 0,873 |
| 0,15 | 0,994 | 0,987 |

Tỉ lệ bác bỏ sai của kiểm định chính là 0,016 ở cả hai cỡ, dưới mức 0,025.

**Độ bất định của power do đầu vào** (`scripts/power_input_uncertainty.py` → `results/power_input_uncertainty.json`). Phân phối q chỉ đo trên 32 task của G1, trong đó 38% task luôn giải được và 41% task không bao giờ giải được. Bootstrap 32 task (60 lần), mỗi lần 300 lần mô phỏng:

| Thiết kế | δ | Power trung vị | Khoảng 5%–95% |
| --- | --- | --- | --- |
| E2, n = 121 | 0,109 | 0,93 | 0,84–0,99 |
| E2, n = 121 | 0,20 | 1,00 | 1,00–1,00 |
| E1, n = 53 | 0,109 | 0,37 | 0,20–0,58 |
| E1, n = 53 | 0,20 | 0,90 | 0,75–0,98 |

Khoảng này chỉ phản ánh sai số của q. Nó không phản ánh sai lệch do mô hình hiệu ứng (q′ = min(1, q + δ)) hay do q đo trên Verified được dùng cho SWE-bench full và Live.

**Power của E2 tính lại bằng q đo được của Live** (`scripts/e2_power_live_q.py` → `results/e2_power_live_q.json`; đúng bước đã ghi ở hàng "Plasmode của E2 dùng tỉ lệ giải đo trên Verified" ở trên). Chỉ đọc nhánh `none` (L28), không xem nhánh skill.
- q của Live: 109 task, trung bình 0,202; 73% không bao giờ giải được, 14% luôn giải được. G1 (Verified) là 0,49, 41% và 38%.
- Tỉ lệ bác bỏ sai của kiểm định chính: 0,011 ở mức 0,025.

| δ | Hiệu ứng thực hiện được | Power (n = 109) |
| --- | --- | --- |
| 0,02 | 0,017 | 0,18 |
| 0,05 | 0,043 | 0,69 |
| 0,109 | 0,094 | 0,996 |
| 0,15 | 0,130 | 1,00 |

Power cao hơn bảng dựa trên q của G1, vì ít task luôn giải được hơn, nên hiệu ứng ít bị chặn ở mức 1. **Đây là power dùng để báo cáo cho E2.**
